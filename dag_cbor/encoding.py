"""
    Encoding functions for DAG-CBOR codec.
"""

from io import BufferedIOBase, BytesIO
import math
import struct
from typing import Optional, overload, Union

import cid # type: ignore

from .utils import CBOREncodingError, DAGCBOREncodingError

EncodableType = Union[None, bool, int, bytes, str, list, dict, cid.cid.BaseCID, float]

@overload
def encode(data: EncodableType, stream: None = None) -> bytes:
    ... # pragma: no cover

@overload
def encode(data: EncodableType, stream: BufferedIOBase) -> None:
    ... # pragma: no cover

def encode(data: EncodableType, stream: Optional[BufferedIOBase] = None) -> Optional[bytes]:
    """
        Encodes the given `data` with the DAG-CBOR codec.
        If a `stream` is given, the encoded data is written to the stream and nothing is returned.
        Otherwise, the encoded data is written to an internal stream and the bytes are returned at the end.
    """
    if stream is None:
        internal_stream = BytesIO()
        _encode(internal_stream, data)
        return internal_stream.getvalue()
    _encode(stream, data)
    return None

def _encode(stream: BufferedIOBase, value: EncodableType):
    # pylint: disable = too-many-return-statements, too-many-branches
    if isinstance(value, bool): # must go before int check
        # major type 0x7 (additional info 20 and 21)
        _encode_bool(stream, value)
    elif isinstance(value, int):
        # major types 0x0 and 0x1
        _encode_int(stream, value)
    elif isinstance(value, bytes):
        # major type 0x2
        _encode_bytes(stream, value)
    elif isinstance(value, str):
        # major type 0x3
        _encode_str(stream, value)
    elif isinstance(value, list):
        # major type 0x4
        _encode_list(stream, value)
    elif isinstance(value, dict):
        # major type 0x5
        _encode_dict(stream, value)
    elif isinstance(value, cid.cid.BaseCID):
        # major type 0x6
        _encode_cid(stream, value)
    elif value is None:
        # major type 0x7 (additional info 22)
        _encode_none(stream, value)
    elif isinstance(value, float):
        # major type 0x7 (additional info 27)
        _encode_float(stream, value)
    else:
        raise DAGCBOREncodingError(f"Type {type(value)} is not encodable.")

def _encode_head(stream: BufferedIOBase, major_type: int, arg: int):
    if arg < 24:
        # argument value as additional info in leading byte
        head = struct.pack(">B", (major_type<<5)|arg)
    elif arg <= 255:
        # leading byte + 1 byte argument value (additional info = 24)
        head = struct.pack(">BB", (major_type<<5)|24, arg)
    elif arg <= 65535:
        # leading byte + 2 bytes argument value (additional info = 25)
        head = struct.pack(">BH", (major_type<<5)|25, arg)
    elif arg <= 4294967295:
        # leading byte + 4 bytes argument value (additional info = 26)
        head = struct.pack(">BL", (major_type<<5)|26, arg)
    else:
        # leading byte + 8 bytes argument value (additional info = 27)
        head = struct.pack(">BQ", (major_type<<5)|27, arg)
    stream.write(head)

def _encode_int(stream: BufferedIOBase, value: int):
    if value >= 18446744073709551616:
        # unsigned int must be < 2**64
        raise CBOREncodingError("Unsigned integer out of range.")
    if value < -18446744073709551616:
        # negative int must be >= -2**64
        raise CBOREncodingError("Negative integer out of range.")
    if value >= 0:
        # unsigned int
        _encode_head(stream, 0x0, value)
    else:
        # negative int
        _encode_head(stream, 0x1, -1-value)

def _encode_bytes(stream: BufferedIOBase, value: bytes):
    _encode_head(stream, 0x2, len(value))
    stream.write(value)

def _encode_str(stream: BufferedIOBase, value: str):
    try:
        utf8_value: bytes = value.encode("utf-8", errors="strict")
    except UnicodeError as e:
        raise CBOREncodingError("Strings must be valid utf-8 strings.") from e
    _encode_head(stream, 0x3, len(utf8_value))
    stream.write(utf8_value)

def _encode_list(stream: BufferedIOBase, value: list):
    _encode_head(stream, 0x4, len(value))
    for item in value:
        _encode(stream, item)

def _encode_dict(stream: BufferedIOBase, value: dict):
    # check keys for DAG-CBOR compliance
    for k in value.keys():
        if not isinstance(k, str):
            raise DAGCBOREncodingError("Keys for maps must be strings.")
    if len(value.keys()) != len(set(value.keys())):
        raise CBOREncodingError("Keys for maps must be unique.")
    # sort keys canonically
    try:
        utf8key_val_pairs = [(k.encode("utf-8", errors="strict"), v)
                             for k, v in value.items()]
    except UnicodeError as e:
        raise CBOREncodingError("Strings must be valid utf-8 strings.") from e
    sorted_utf8key_val_pairs = sorted(utf8key_val_pairs, key=lambda i: i[0])
    # encode key-value pairs (keys already utf-8 encoded)
    _encode_head(stream, 0x5, len(value))
    for utf8k, v in sorted_utf8key_val_pairs:
        _encode_head(stream, 0x3, len(utf8k))
        stream.write(utf8k)
        _encode(stream, v)

def _encode_cid(stream: BufferedIOBase, value: cid.cid.BaseCID):
    _encode_head(stream, 0x6, 42)
    _encode_bytes(stream, value.buffer)

def _encode_bool(stream: BufferedIOBase, value: bool):
    _encode_head(stream, 0x7, 21 if value else 20)

def _encode_none(stream: BufferedIOBase, value: None):
    _encode_head(stream, 0x7, 22)

def _encode_float(stream: BufferedIOBase, value: float):
    if math.isnan(value):
        raise DAGCBOREncodingError("NaN is not an allowed float value.")
    if math.isinf(value):
        if value > 0:
            raise DAGCBOREncodingError("Infinity is not an allowed float value.")
        raise DAGCBOREncodingError("-Infinity is not an allowed float value.")
    # special head, with double encoding for 4B argument value
    head = struct.pack(">Bd", (0x7<<5)|27, value)
    stream.write(head)
