"""
    Encoding functions for DAG-CBOR codec.
"""

from io import BufferedIOBase, BytesIO
import math
import struct
from typing import Optional, Tuple, Union

import cid # type: ignore

from .encoding import EncodableType
from .utils import CBORDecodingError, DAGCBORDecodingError

def decode(stream_or_bytes: Union[BufferedIOBase, bytes]) -> EncodableType:
    """
        Decodes and returns a single data item from the given `stream_or_bytes`, with the DAG-CBOR codec.
    """
    if isinstance(stream_or_bytes, bytes):
        stream: BufferedIOBase = BytesIO(stream_or_bytes)
    else:
        stream = stream_or_bytes
    data = _decode_item(stream)
    remaining_bytes = stream.read()
    if len(remaining_bytes) > 0:
        raise DAGCBORDecodingError("Encode and decode must operate on a single top-level CBOR object")
    return data

def _decode_item(stream: BufferedIOBase) -> EncodableType:
    # pylint: disable = too-many-return-statements
    major_type, arg = _decode_head(stream)
    if isinstance(arg, float):
        # float
        assert major_type == 0x7
        if math.isnan(arg):
            raise DAGCBORDecodingError("NaN is not an allowed float value.")
        if math.isinf(arg):
            if arg > 0:
                raise DAGCBORDecodingError("Infinity is not an allowed float value.")
            raise DAGCBORDecodingError("-Infinity is not an allowed float value.")
        return arg
    if major_type == 0x0:
        return arg # unsigned int
    if major_type == 0x1:
        return -1-arg # negative int
    if major_type == 0x2:
        return _decode_bytes(stream, arg)
    if major_type == 0x3:
        return _decode_str(stream, arg)
    if major_type == 0x4:
        return _decode_list(stream, arg)
    if major_type == 0x5:
        return _decode_dict(stream, arg)
    if major_type == 0x6:
        return _decode_cid(stream, arg)
    if major_type == 0x7:
        return _decode_bool_none(stream, arg)
    raise RuntimeError("Major type must be one of 0x0-0x7.")

def _decode_head(stream: BufferedIOBase) -> Tuple[int, Union[int, float]]:
    # read leading byte
    res = stream.read(1)
    if len(res) < 1:
        raise CBORDecodingError("Unexpected EOF while reading leading byte of data item head.")
    leading_byte = res[0]
    major_type = leading_byte >> 5
    additional_info = leading_byte & 0b11111
    # read argument value and return (major_type, arg)
    if additional_info < 24:
        # argument value = additional info
        return (major_type, additional_info)
    if additional_info > 27 or (major_type == 0x7 and additional_info != 27):
        raise DAGCBORDecodingError(f"Invalid additional info {additional_info} in data item head for major type {major_type}.")
    argument_nbytes = 1<<(additional_info-24)
    res = stream.read(argument_nbytes)
    if len(res) < argument_nbytes:
        raise CBORDecodingError(f"Unexpected EOF while reading {argument_nbytes} byte argument of data item head.")
    if additional_info == 24:
        # 1 byte of unsigned int argument value to follow
        return (major_type, res[0])
    if additional_info == 25:
        # 2 bytes of unsigned int argument value to follow
        arg = struct.unpack(">H", res)[0]
        if arg <= 255:
            raise DAGCBORDecodingError(f"Integer {arg} was encoded using 2 bytes, while 1 byte would have been enough.")
        return (major_type, arg)
    if additional_info == 26:
        # 4 bytes of unsigned int argument value to follow
        arg = struct.unpack(">L", res)[0]
        if arg <= 65535:
            raise DAGCBORDecodingError(f"Integer {arg} was encoded using 4 bytes, while 2 bytes would have been enough.")
        return (major_type, arg)
    # necessarily additional_info == 27
    if major_type == 0x7:
        # 8 bytes of float argument value to follow
        return (major_type, struct.unpack(">d", res)[0])
    # 8 bytes of unsigned int argument value to follow
    arg = struct.unpack(">Q", res)[0]
    if arg <= 4294967295:
        raise DAGCBORDecodingError(f"Integer {arg} was encoded using 8 bytes, while 4 bytes would have been enough.")
    return (major_type, arg)

def _decode_bytes(stream: BufferedIOBase, length: int) -> bytes:
    res = stream.read(length)
    if len(res) < length:
        raise CBORDecodingError(f"Unexpected EOF while reading {length} bytes of bytestring.")
    return res

def _decode_str(stream: BufferedIOBase, length: int) -> str:
    res = stream.read(length)
    if len(res) < length:
        raise CBORDecodingError(f"Unexpected EOF while reading {length} bytes of string.")
    return res.decode(encoding="utf-8", errors="strict")

def _decode_list(stream: BufferedIOBase, length: int) -> list:
    l: list = []
    for i in range(length):
        try:
            l.append(_decode_item(stream))
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding item #{i} in list of length {length}.") from e
    return l

def _decode_dict(stream: BufferedIOBase, length: int) -> dict:
    d: dict = {}
    for i in range(length):
        try:
            k = _decode_item(stream)
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding key #{i} in dict of length {length}.") from e
        if not isinstance(k, str):
            raise DAGCBORDecodingError(f"Key #{i} in dict of length {length} is of type {type(k)}, expected string.")
        try:
            v = _decode_item(stream)
        except CBORDecodingError as e:
            raise CBORDecodingError(f"Error while decoding value #{i} in dict of length {length}.") from e
        d[k] = v
    if len(d) != length:
        raise DAGCBORDecodingError(f"Found only {len(d)} unique keys out of {length} key-value pairs.")
    return d

def _decode_cid(stream: BufferedIOBase, arg: int) -> cid.cid.BaseCID:
    if arg != 42:
        raise DAGCBORDecodingError(f"Error while decoding major type 0x6: tag {arg} is not allowed.")
    try:
        cid_bytes = _decode_item(stream)
    except CBORDecodingError as e:
        raise CBORDecodingError("Error while decoding CID bytes.") from e
    if not isinstance(cid_bytes, bytes):
        raise DAGCBORDecodingError(f"Expected CID bytes, found data of type {type(cid_bytes)} instead.")
    return cid.from_bytes(cid_bytes)

def _decode_bool_none(stream: BufferedIOBase, arg: int) -> Optional[bool]:
    if arg == 20:
        return False
    if arg == 21:
        return True
    if arg == 22:
        return None
    raise DAGCBORDecodingError(f"Error while decoding major type 0x7: simple value {arg} is not allowed.")
