"""
    Encoding functions for DAG-CBOR codec.
"""

from io import BufferedIOBase, BytesIO
import math
import struct
from typing import Any, Dict, List, Optional, overload, Union
from typing_validation import validate

from multiformats import varint, multicodec, CID

from .utils import CBOREncodingError, DAGCBOREncodingError, _check_key_compliance

FlatEncodableType = Union[None, bool, int, float, bytes, str, CID]
"""
    Union of non-container Python types that can be encoded by this implementation of the DAG-CBOR codec.
"""

EncodableType = Union[FlatEncodableType, List[Any], Dict[str, Any]]
"""
    Union of Python types that can be encoded (at top level) by this implementation of the DAG-CBOR codec.

    Because of limited support for recursive types (see `Mypy issue #731 <https://github.com/python/mypy/issues/731>`_),
    the list items and dictionary values are not recursively typechecked.
"""

_dag_cbor_multicodec = multicodec.get("dag-cbor")
_dag_cbor_code: int = _dag_cbor_multicodec.code
_dag_cbor_code_bytes: bytes = varint.encode(_dag_cbor_code)
_dag_cbor_code_nbytes: int = len(_dag_cbor_code_bytes)

@overload
def encode(data: EncodableType, stream: None = None, *, include_multicodec: bool = False) -> bytes:
    ... # pragma: no cover

@overload
def encode(data: EncodableType, stream: BufferedIOBase, *, include_multicodec: bool = False) -> int:
    ... # pragma: no cover

def encode(data: EncodableType, stream: Optional[BufferedIOBase] = None, *, include_multicodec: bool = False) -> Union[bytes, int]:
    r"""
        Encodes the given data with the DAG-CBOR codec.

        By default, the encoded data is written to an internal stream and the bytes are returned at the end (as a `bytes` object).

        .. code-block:: python

            def encode(data: EncodableType, stream: None = None) -> bytes:
                ...

        Example usage:

        >>> dag_cbor.encode({'a': 12, 'b': 'hello!'})
        b'\xa2aa\x0cabfhello!'

        If a ``stream`` is given, the encoded data is written to the stream and the number of bytes written is returned:

        .. code-block:: python

            def encode(data: EncodableType, stream: BufferedIOBase) -> int:
                ...

        Example usage with a stream:

        >>> from io import BytesIO
        >>> stream = BytesIO()
        >>> dag_cbor.encode({'a': 12, 'b': 'hello!'}, stream=stream)
        13
        >>> stream.getvalue()
        b'\xa2aa\x0cabfhello!'

        :param data: the DAG data to be encoded
        :type data: :obj:`EncodableType`
        :param stream: an optional stream into which the encoded data should be written
        :type stream: :obj:`io.BufferedIOBase` or :obj:`None`, *optional*
        :param include_multicodec: if :obj:`True`, the encoded data is prefixed by the multicodec code for ``'dag-cbor'``
                                   (see `multicodec.wrap <https://multiformats.readthedocs.io/en/latest/api/multiformats.multicodec.html#wrap>`_).
        :type include_multicodec: :obj:`bool`, *optional*

        :raises ~dag_cbor.utils.CBOREncodingError: if an :obj:`int` outside of ``range(-2**64, 2**64)`` is encountered
        :raises ~dag_cbor.utils.DAGCBOREncodingError: if a value of type other than :obj:`None`, :obj:`bool`, :obj:`int`, :obj:`float`, :obj:`str`,
                                                      :obj:`bytes`, :obj:`list`, :obj:`dict`, or :class:`~multiformats.cid.CID` is encountered
        :raises ~dag_cbor.utils.DAGCBOREncodingError: if attempting to encode the special :obj:`float` values ``NaN``, ``Infinity`` and ``-Infinity``
        :raises ~dag_cbor.utils.DAGCBOREncodingError: if a key of a dictionary is not a string

    """
    validate(data, EncodableType)
    validate(stream, Optional[BufferedIOBase])
    validate(include_multicodec, bool)
    if stream is None:
        internal_stream = BytesIO()
        if include_multicodec:
            internal_stream.write(_dag_cbor_code_bytes)
        _encode(internal_stream, data)
        return internal_stream.getvalue()
    num_bytes = 0
    if include_multicodec:
        stream.write(_dag_cbor_code_bytes)
        num_bytes += _dag_cbor_code_nbytes
    num_bytes += _encode(stream, data)
    return num_bytes


def _encode(stream: BufferedIOBase, value: EncodableType) -> int:
    # pylint: disable = too-many-return-statements, too-many-branches
    if isinstance(value, bool): # must go before int check
        # major type 0x7 (additional info 20 and 21)
        return _encode_bool(stream, value)
    if isinstance(value, int):
        # major types 0x0 and 0x1
        return _encode_int(stream, value)
    if isinstance(value, bytes):
        # major type 0x2
        return _encode_bytes(stream, value)
    if isinstance(value, str):
        # major type 0x3
        return _encode_str(stream, value)
    if isinstance(value, list):
        # major type 0x4
        return _encode_list(stream, value)
    if isinstance(value, dict):
        # major type 0x5
        return _encode_dict(stream, value)
    if isinstance(value, CID):
        # major type 0x6
        return _encode_cid(stream, value)
    if value is None:
        # major type 0x7 (additional info 22)
        return _encode_none(stream, value)
    if isinstance(value, float):
        # major type 0x7 (additional info 27)
        return _encode_float(stream, value)
    raise DAGCBOREncodingError(f"Type {type(value)} is not encodable.")

def _encode_head(stream: BufferedIOBase, major_type: int, arg: int) -> int:
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
    return len(head)

def _encode_int(stream: BufferedIOBase, value: int) -> int:
    if value >= 18446744073709551616:
        # unsigned int must be < 2**64
        raise CBOREncodingError("Unsigned integer out of range.")
    if value < -18446744073709551616:
        # negative int must be >= -2**64
        raise CBOREncodingError("Negative integer out of range.")
    if value >= 0:
        # unsigned int
        return _encode_head(stream, 0x0, value)
    # negative int
    return _encode_head(stream, 0x1, -1-value)

def _encode_bytes(stream: BufferedIOBase, value: bytes) -> int:
    num_head_bytes = _encode_head(stream, 0x2, len(value))
    stream.write(value)
    return num_head_bytes+len(value)

def _encode_str(stream: BufferedIOBase, value: str) -> int:
    # try:
    #     utf8_value: bytes = value.encode("utf-8", errors="strict")
    # except UnicodeError as e:
    #     raise CBOREncodingError("Strings must be valid utf-8 strings.") from e
    # # as far as I understand, the above should never raise UnicodeError on "utf-8" encoding
    utf8_value: bytes = value.encode("utf-8", errors="strict")
    num_head_bytes = _encode_head(stream, 0x3, len(utf8_value))
    stream.write(utf8_value)
    return num_head_bytes+len(utf8_value)

def _encode_list(stream: BufferedIOBase, value: List[Any]) -> int:
    num_bytes_written = _encode_head(stream, 0x4, len(value))
    for item in value:
        num_bytes_written += _encode(stream, item)
    return num_bytes_written

def _encode_dict(stream: BufferedIOBase, value: Dict[str, Any]) -> int:
    _check_key_compliance(value)
    # try:
    #     utf8key_val_pairs = [(k.encode("utf-8", errors="strict"), v)
    #                          for k, v in value.items()]
    # except UnicodeError as e:
    #     raise CBOREncodingError("Strings must be valid utf-8 strings.") from e
    # # as far as I understand, the above should never raise UnicodeError on "utf-8" encoding
    utf8key_val_pairs = [(k.encode("utf-8", errors="strict"), v)
                         for k, v in value.items()]
    # 1. sort keys canonically:
    sorted_utf8key_val_pairs = sorted(utf8key_val_pairs, key=lambda i: (len(i[0]), i[0]))
    # 2. encode key-value pairs (keys already utf-8 encoded):
    num_bytes_written = _encode_head(stream, 0x5, len(value))
    for utf8k, v in sorted_utf8key_val_pairs:
        num_bytes_written += _encode_head(stream, 0x3, len(utf8k))
        stream.write(utf8k)
        num_bytes_written += len(utf8k)
        num_bytes_written += _encode(stream, v)
    return num_bytes_written

def _encode_cid(stream: BufferedIOBase, value: CID) -> int:
    num_bytes_written = _encode_head(stream, 0x6, 42)
    num_bytes_written += _encode_bytes(stream, b"\0" + bytes(value))
    return num_bytes_written

def _encode_bool(stream: BufferedIOBase, value: bool) -> int:
    return _encode_head(stream, 0x7, 21 if value else 20)

def _encode_none(stream: BufferedIOBase, value: None) -> int:
    return _encode_head(stream, 0x7, 22)

def _encode_float(stream: BufferedIOBase, value: float) -> int:
    if math.isnan(value):
        raise DAGCBOREncodingError("NaN is not an allowed float value.")
    if math.isinf(value):
        if value > 0:
            raise DAGCBOREncodingError("Infinity is not an allowed float value.")
        raise DAGCBOREncodingError("-Infinity is not an allowed float value.")
    # special head, with double encoding for 4B argument value
    head = struct.pack(">Bd", (0x7<<5)|27, value)
    stream.write(head)
    return len(head)
