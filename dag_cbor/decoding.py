"""
    Deconding function for DAG-CBOR codec.
"""

from io import BufferedIOBase, BytesIO
import math
import struct
from typing import Any, Dict, Callable, List, Optional, Tuple, Union
from typing_validation import validate

from multiformats import multicodec, CID

from .encoding import EncodableType, _dag_cbor_code
from .utils import CBORDecodingError, DAGCBORDecodingError

DecodeCallback = Callable[[EncodableType, int], None]
""" Type of optional callbacks for the :func:`decode` function."""

def decode(stream_or_bytes: Union[BufferedIOBase, bytes], *,
           allow_concat: bool = False,
           callback: Optional["DecodeCallback"] = None,
           require_multicodec: bool = False) -> EncodableType:
    r"""
        Decodes and returns a single data item from the given ``stream_or_bytes``, with the DAG-CBOR codec.

        A simple use for the optional ``callback`` argument is to count the number of bytes read from the stream:

        >>> import dag_cbor
        >>> from io import BytesIO
        >>> class BytesReadCounter:
        ...     _num_bytes_read = 0
        ...     def __call__(self, _, num_bytes_read):
        ...         self._num_bytes_read += num_bytes_read
        ...     def __int__(self):
        ...         return self._num_bytes_read
        ...
        >>> encoded_bytes = b'\xa2aa\x0cabfhello!\x82\x00\x01'
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
        b'\x82\x00\x01'
        >>> len(bytes_remaining)
        3
        >>> dag_cbor.decode(bytes_remaining)
        [0, 1]

        :param stream_or_bytes: the bytes object or bytes stream to decode
        :type stream_or_bytes: :obj:`bytes` or :obj:`~io.BufferedIOBase`
        :param allow_concat: whether to allow partial stream decoding (if this is :obj:`False`, a byte stream will always be consumed in its entirety)
        :type allow_concat: :obj:`bool`, *optional*
        :param callback: optional callback to be invoked as ``callback(item, num_bytes_read)`` every time an item is decoded,
                         where ``num_bytes_read`` is the number of bytes read decoding the item (excluding sub-items, in the case of lists or dictionaries).
        :type callback: :obj:`DecodeCallback` or :obj:`None`, *optional*
        :param require_multicodec: if :obj:`True`, the data being decoded must be prefixed by the multicodec code for ``'dag-cbor'``
                                   (see `multicodec.unwrap <https://multiformats.readthedocs.io/en/latest/api/multiformats.multicodec.html#unwrap>`_).
        :type require_multicodec: :obj:`bool`, *optional*

        :raises ~dag_cbor.utils.CBORDecodingError: while reading the leading byte of a data item head, if no bytes are available
        :raises ~dag_cbor.utils.CBORDecodingError: while reading the argument bytes of a data item head,
                                                  if the expected number of argument bytes is not available
        :raises ~dag_cbor.utils.CBORDecodingError: while decoding the data of a bytestring or string, if the expected number of data bytes is not available
        :raises ~dag_cbor.utils.CBORDecodingError: while decoding the items of a list or a map (keys and values),
                                                  if the expected number of items is not available
        :raises ~dag_cbor.utils.CBORDecodingError: if an invalid utf-8 byte sequence is encountered while attempting to decode a string
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if attempting to decode the special :obj:`float` values ``NaN``, ``Infinity`` and ``-Infinity``
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if the additional info is greater than 27, or different from 27 for major type 7
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if an integer value was not minimally encoded
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if a key of a map is not a string
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if a map has repeated keys
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if map keys are not in canonical order
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if a tag (major type 6) different than 42 (for CID data) is encountered
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if non-bytestring data is found where CID data is expected (tag 42)
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if a simple value (major type 7) different from 20 (False), 21 (True) or 22 (None) is encountered
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if ``require_multicodec`` is set to :obj:`True` and
                                                     the bytes are not prefixed by the ``'dag-cbor'`` multicodec code
        :raises ~dag_cbor.utils.DAGCBORDecodingError: if ``allow_concat`` is set to :obj:`False` and the decoding did not use all available bytes

    """
    validate(stream_or_bytes, Union[BufferedIOBase, bytes])
    validate(allow_concat, bool)
    validate(require_multicodec, bool)
    # validate(callback, Optional[DecodeCallback]) # TODO: not yet supported by typing_validation
    if isinstance(stream_or_bytes, bytes):
        stream: BufferedIOBase = BytesIO(stream_or_bytes)
    else:
        stream = stream_or_bytes
    if require_multicodec:
        code, _, stream = multicodec.unwrap_raw(stream)
        if code != _dag_cbor_code:
            raise DAGCBORDecodingError(f"Required 'dag-cbor' multicodec code {hex(_dag_cbor_code)}, unwrapped code {hex(code)} instead.")
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
        value, _ = _decode_list(stream, arg, callback=callback)
        ret = (value, num_bytes_read)
    elif major_type == 0x5:
        value, _ = _decode_dict(stream, arg, callback=callback)
        ret = (value, num_bytes_read)
    elif major_type == 0x6:
        value, num_bytes_further_read = _decode_cid(stream, arg)
        ret = (value, num_bytes_read+num_bytes_further_read)
    elif major_type == 0x7:
        value, _ = _decode_bool_none(stream, arg)
        ret = (value, num_bytes_read)
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
    try:
        s = res.decode(encoding="utf-8", errors="strict")
    except UnicodeError as e:
        raise CBORDecodingError("Strings must be valid utf-8 strings.") from e
    return (s, length)

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

def _decode_dict_key(stream: BufferedIOBase, key_idx: int, dict_length: int, *,
                     callback: Optional[DecodeCallback]) -> Tuple[str, int, bytes]:
    # pylint: disable = too-many-return-statements, too-many-branches
    major_type, arg, num_bytes_read = _decode_head(stream)
    ret: Optional[Tuple[EncodableType, int]] = None
    if major_type != 0x3:
        raise DAGCBORDecodingError(f"Key #{key_idx} in dict of length {dict_length} is of major type {hex(major_type)}, expected 0x3 (string).")
    assert not isinstance(arg, float)
    str_length = arg
    str_bytes: bytes = stream.read(str_length)
    if len(str_bytes) < str_length:
        raise CBORDecodingError(f"Unexpected EOF while reading {str_length} bytes of string.")
    try:
        s = str_bytes.decode(encoding="utf-8", errors="strict")
    except UnicodeError as e:
        raise CBORDecodingError("Strings must be valid utf-8 strings.") from e
    ret = (s, num_bytes_read+str_length)
    if callback is not None:
        callback(*ret)
    return ret+(str_bytes,)

def _decode_dict(stream: BufferedIOBase, length: int,
                 callback: Optional[DecodeCallback]) -> Tuple[Dict[str, Any], int]:
    # pylint: disable = too-many-locals
    d: Dict[str, Any] = {}
    key_bytes_list: List[bytes] = []
    for i in range(length):
        try:
            k, _, k_bytes = _decode_dict_key(stream, i, length, callback=callback)
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding key #{i} in dict of length {length}.") from e
        try:
            v, _ = _decode_item(stream, callback=callback)
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding value #{i} in dict of length {length}.") from e
        d[k] = v
        key_bytes_list.append(k_bytes)
    if len(d) != length:
        raise DAGCBORDecodingError(f"Found only {len(d)} unique keys out of {length} key-value pairs.")
    # check that keys are sorted canonically
    assert len(key_bytes_list) == length
    sorted_key_bytes_list = sorted(key_bytes_list)
    for idx, (k1, k2) in enumerate(zip(key_bytes_list, sorted_key_bytes_list)):
        if k1 != k2:
            exp_idx = sorted_key_bytes_list.index(k1)
            raise DAGCBORDecodingError(f"Dictionary keys not in canonical order: key #{idx} should have been in position #{exp_idx} instead.")
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
    if not cid_bytes[0] == 0:
        raise DAGCBORDecodingError(f"CID does not start with the identity Multibase prefix (0x00).")
    return (CID.decode(cid_bytes[1:]), num_bytes_read)

def _decode_bool_none(stream: BufferedIOBase, arg: int) -> Tuple[Optional[bool], int]:
    if arg == 20:
        return (False, 0)
    if arg == 21:
        return (True, 0)
    if arg == 22:
        return (None, 0)
    raise DAGCBORDecodingError(f"Error while decoding major type 0x7: simple value {arg} is not allowed.")
