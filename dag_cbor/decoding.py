"""
    Deconding function for DAG-CBOR codec.

    The core functionality is performed by the `decode` function, which decodes `bytes` into a value:

    ```python
        >>> import dag_cbor
        >>> dag_cbor.decode(b'\\xa2aa\\x0cabfhello!')
        {'a': 12, 'b': 'hello!'}
    ```

    A buffered binary stream (i.e. an instance of `io.BufferedIOBase`) can be passed to the `decode` function
    instead of a `bytes` object, in which case the contents of the stream are read in their entirety and decoded:

    ```python
        >>> stream = BytesIO(b'\\xa2aa\\x0cabfhello!')
        >>> dag_cbor.decode(stream)
        {'a': 12, 'b': 'hello!'}
    ```

    The decision to read the entirety of the stream stems from the [DAG-CBOR codec](https://ipld.io/specs/codecs/dag-cbor/spec/)
    specification, stating that encoding and decoding is only allowed on a single top-level item.
    However, the optional keyword argument `allow_concat` (default `False`) can be set to `True` to disable this behaviour
    and allow only part of the stream to be decoded.
"""

from io import BufferedIOBase, BytesIO
import math
import struct
from typing import Any, Dict, Callable, List, Optional, Tuple, Union
from typing_validation import validate

from multiformats import CID

from .encoding import EncodableType
from .utils import CBORDecodingError, DAGCBORDecodingError

DecodeCallback = Callable[[EncodableType, int], None]
"""
    Type of optional callbacks for the `decode` function:

    ```py
        DecodeCallback = Callable[[EncodableType, int], None]
    ```
"""

def decode(stream_or_bytes: Union[BufferedIOBase, bytes], *,
           allow_concat: bool = False,
           callback: Optional["DecodeCallback"] = None) -> EncodableType:
    """
        Decodes and returns a single data item from the given `stream_or_bytes`, with the DAG-CBOR codec.

        Currently, [pdoc](https://pdoc3.github.io/pdoc/) does not properly document the signature of this function, which is as follows:

        ```py
            def decode(stream_or_bytes: Union[BufferedIOBase, bytes], *,
                       allow_concat: bool = False,
                       callback: Optional[DecodeCallback] = None) -> EncodableType:
        ```

        The optional keyword argument `allow_cocatenation` (default `False`) can be set to `True` to allow only
        part of the stream to be decoded: if set to `False`, the whole stream will be read and any bytes not used
        in the decoding will cause a `dag_cbor.utils.DAGCBORDecodingError` to be raised.

        The optional keyword argument `callback` (default `None`) can be set to a function
        `fun: DecodeCallback` which is invoked as `fun(item, num_bytes_read)` every time an item
        is decoded from the stream/bytes. A simple use for this callback is to count the number of bytes read from the stream:

        ```py
            >>> import dag_cbor
            >>> from io import BytesIO
            >>> class BytesReadCounter:
            ...     _num_bytes_read = 0
            ...     def __call__(self, _, num_bytes_read):
            ...         self._num_bytes_read += num_bytes_read
            ...     def __int__(self):
            ...         return self._num_bytes_read
            ...
            >>> encoded_bytes = b'\\xa2aa\\x0cabfhello!\\x82\\x00\\x01'
            >>> len(encoded_bytes)
            16
            >>> stream = BytesIO(encoded_bytes)
            >>> bytes_read_cnt = BytesReadCounter()
            >>> dag_cbor.decode(stream, allow_concat=True, callback=bytes_read_cnt)
            {'a': 12, 'b': 'hello!'}
            >>> int(bytes_read_cnt)
            13
            >>> bytes_remaining = stream.read()
            >>> bytes_remaining
            b'\\x82\\x00\\x01'
            >>> len(bytes_remaining)
            3
            >>> dag_cbor.decode(bytes_remaining)
            [0, 1]
        ```
    """
    validate(stream_or_bytes, Union[BufferedIOBase, bytes])
    validate(allow_concat, bool)
    # validate(callback, Optional[DecodeCallback]) # not yet supported by typing_validation
    if isinstance(stream_or_bytes, bytes):
        stream: BufferedIOBase = BytesIO(stream_or_bytes)
    else:
        stream = stream_or_bytes
    data, _ = _decode_item(stream, callback=callback)
    if allow_concat:
        return data
    remaining_bytes = stream.read()
    if len(remaining_bytes) > 0:
        raise DAGCBORDecodingError("Encode and decode must operate on a single top-level CBOR object")
    return data

def _decode_item(stream: BufferedIOBase, *,
                 callback: Optional[DecodeCallback]) -> Tuple[EncodableType, int]:
    # pylint: disable = too-many-return-statements, too-many-branches
    major_type, arg, num_bytes_read = _decode_head(stream)
    ret: Optional[Tuple[EncodableType, int]] = None
    if isinstance(arg, float):
        # float
        assert major_type == 0x7
        if math.isnan(arg):
            raise DAGCBORDecodingError("NaN is not an allowed float value.")
        if math.isinf(arg):
            if arg > 0:
                raise DAGCBORDecodingError("Infinity is not an allowed float value.")
            raise DAGCBORDecodingError("-Infinity is not an allowed float value.")
        ret = (arg, num_bytes_read)
    elif major_type == 0x0:
        ret = (arg, num_bytes_read) # unsigned int
    elif major_type == 0x1:
        ret = (-1-arg, num_bytes_read) # negative int
    elif major_type == 0x2:
        value, num_bytes_further_read = _decode_bytes(stream, arg)
        ret = (value, num_bytes_read+num_bytes_further_read)
    elif major_type == 0x3:
        value, num_bytes_further_read = _decode_str(stream, arg)
        ret = (value, num_bytes_read+num_bytes_further_read)
    elif major_type == 0x4:
        value, num_bytes_further_read = _decode_list(stream, arg, callback=callback)
        ret = (value, num_bytes_read+num_bytes_further_read)
    elif major_type == 0x5:
        value, num_bytes_further_read = _decode_dict(stream, arg, callback=callback)
        ret = (value, num_bytes_read+num_bytes_further_read)
    elif major_type == 0x6:
        value, num_bytes_further_read = _decode_cid(stream, arg)
        ret = (value, num_bytes_read+num_bytes_further_read)
    elif major_type == 0x7:
        value, num_bytes_further_read = _decode_bool_none(stream, arg)
        ret = (value, num_bytes_read+num_bytes_further_read)
    else:
        raise RuntimeError("Major type must be one of 0x0-0x7.")
    if callback is not None:
        callback(*ret)
    return ret

def _decode_head(stream: BufferedIOBase) -> Tuple[int, Union[int, float], int]:
    # read leading byte
    res = stream.read(1)
    if len(res) < 1:
        raise CBORDecodingError("Unexpected EOF while reading leading byte of data item head.")
    leading_byte = res[0]
    major_type = leading_byte >> 5
    additional_info = leading_byte & 0b11111
    # read argument value and return (major_type, arg, num_bytes_read)
    if additional_info < 24:
        # argument value = additional info
        return (major_type, additional_info, 1)
    if additional_info > 27 or (major_type == 0x7 and additional_info != 27):
        raise DAGCBORDecodingError(f"Invalid additional info {additional_info} in data item head for major type {major_type}.")
    argument_nbytes = 1<<(additional_info-24)
    res = stream.read(argument_nbytes)
    if len(res) < argument_nbytes:
        raise CBORDecodingError(f"Unexpected EOF while reading {argument_nbytes} byte argument of data item head.")
    if additional_info == 24:
        # 1 byte of unsigned int argument value to follow
        return (major_type, res[0], 2)
    if additional_info == 25:
        # 2 bytes of unsigned int argument value to follow
        arg = struct.unpack(">H", res)[0]
        if arg <= 255:
            raise DAGCBORDecodingError(f"Integer {arg} was encoded using 2 bytes, while 1 byte would have been enough.")
        return (major_type, arg, 3)
    if additional_info == 26:
        # 4 bytes of unsigned int argument value to follow
        arg = struct.unpack(">L", res)[0]
        if arg <= 65535:
            raise DAGCBORDecodingError(f"Integer {arg} was encoded using 4 bytes, while 2 bytes would have been enough.")
        return (major_type, arg, 5)
    # necessarily additional_info == 27
    if major_type == 0x7:
        # 8 bytes of float argument value to follow
        return (major_type, struct.unpack(">d", res)[0], 9)
    # 8 bytes of unsigned int argument value to follow
    arg = struct.unpack(">Q", res)[0]
    if arg <= 4294967295:
        raise DAGCBORDecodingError(f"Integer {arg} was encoded using 8 bytes, while 4 bytes would have been enough.")
    return (major_type, arg, 9)

def _decode_bytes(stream: BufferedIOBase, length: int) -> Tuple[bytes, int]:
    res = stream.read(length)
    if len(res) < length:
        raise CBORDecodingError(f"Unexpected EOF while reading {length} bytes of bytestring.")
    return (res, length)

def _decode_str(stream: BufferedIOBase, length: int) -> Tuple[str, int]:
    res = stream.read(length)
    if len(res) < length:
        raise CBORDecodingError(f"Unexpected EOF while reading {length} bytes of string.")
    return (res.decode(encoding="utf-8", errors="strict"), length)

def _decode_list(stream: BufferedIOBase, length: int, *,
                 callback: Optional[DecodeCallback]) -> Tuple[List[Any], int]:
    l: List[Any] = []
    for i in range(length):
        try:
            item, _ = _decode_item(stream, callback=callback)
            l.append(item)
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding item #{i} in list of length {length}.") from e
    return (l, 0)

def _decode_dict(stream: BufferedIOBase, length: int,
                 callback: Optional[DecodeCallback]) -> Tuple[Dict[str, Any], int]:
    d: Dict[str, Any] = {}
    for i in range(length):
        try:
            k, _ = _decode_item(stream, callback=callback)
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding key #{i} in dict of length {length}.") from e
        if not isinstance(k, str):
            raise DAGCBORDecodingError(f"Key #{i} in dict of length {length} is of type {type(k)}, expected string.")
        try:
            v, _ = _decode_item(stream, callback=callback)
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding value #{i} in dict of length {length}.") from e
        d[k] = v
    if len(d) != length:
        raise DAGCBORDecodingError(f"Found only {len(d)} unique keys out of {length} key-value pairs.")
    return (d, 0)

def _decode_cid(stream: BufferedIOBase, arg: int) -> Tuple[CID, int]:
    if arg != 42:
        raise DAGCBORDecodingError(f"Error while decoding major type 0x6: tag {arg} is not allowed.")
    try:
        cid_bytes, num_bytes_read = _decode_item(stream, callback=None)
    except CBORDecodingError as e:
        raise CBORDecodingError("Error while decoding CID bytes.") from e
    if not isinstance(cid_bytes, bytes):
        raise DAGCBORDecodingError(f"Expected CID bytes, found data of type {type(cid_bytes)} instead.")
    return (CID.decode(cid_bytes), num_bytes_read)

def _decode_bool_none(stream: BufferedIOBase, arg: int) -> Tuple[Optional[bool], int]:
    if arg == 20:
        return (False, 0)
    if arg == 21:
        return (True, 0)
    if arg == 22:
        return (None, 0)
    raise DAGCBORDecodingError(f"Error while decoding major type 0x7: simple value {arg} is not allowed.")
