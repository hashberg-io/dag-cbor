"""
    Encoding functions for DAG-CBOR codec.
"""

from __future__ import annotations # See https://peps.python.org/pep-0563/

from io import BufferedIOBase, BytesIO
import math
import struct
from typing import Any, Dict, List, Optional, overload, Union
import unicodedata

from typing_extensions import Literal, TypedDict
from typing_validation import validate

from multiformats import varint, multicodec, CID

from ..ipld import IPLDKind, IPLDObjPath
from .err import CBOREncodingError, DAGCBOREncodingError

__all__ = ("CBOREncodingError", "DAGCBOREncodingError")

_dag_cbor_multicodec = multicodec.get("dag-cbor")
_dag_cbor_code: int = _dag_cbor_multicodec.code
_dag_cbor_code_bytes: bytes = varint.encode(_dag_cbor_code)
_dag_cbor_code_nbytes: int = len(_dag_cbor_code_bytes)

def check_key_compliance(value: Dict[str, Any]) -> None:
    """
        Enforces DAG-CBOR compliance for keys in a mapping.
    """
    validate(value, Dict[str, Any])
    _check_key_compliance(value)

def canonical_order_dict(value: Dict[str, Any]) -> Dict[str, Any]:
    """
        Returns a dictionary with canonically ordered keys, according to the DAG-CBOR specification.
        Specifically, keys are sorted increasingly first by length and then by the lexicographic ordering of the corresponding UTF-8 bytestrings.
    """
    validate(value, Dict[str, Any])
    _check_key_compliance(value)
    # sort keys canonically
    return _canonical_order_dict(value)


@overload
def encode(data: IPLDKind, stream: None = None, *,
           include_multicodec: bool = False,
           normalize_strings: Optional[Literal["NFC", "NFKC", "NFD", "NFKD"]] = None
          ) -> bytes:
    ... # pragma: no cover

@overload
def encode(data: IPLDKind, stream: BufferedIOBase, *,
           include_multicodec: bool = False,
           normalize_strings: Optional[Literal["NFC", "NFKC", "NFD", "NFKD"]] = None
          ) -> int:
    ... # pragma: no cover

def encode(data: IPLDKind, stream: Optional[BufferedIOBase] = None, *,
           include_multicodec: bool = False,
           normalize_strings: Optional[Literal["NFC", "NFKC", "NFD", "NFKD"]] = None
          ) -> Union[bytes, int]:
    r"""
        Encodes the given data with the DAG-CBOR codec.

        By default, the encoded data is written to an internal stream and the bytes are returned at the end (as a `bytes` object).

        .. code-block:: python

            def encode(data: IPLDKind, stream: None = None) -> bytes:
                ...

        Example usage:

        >>> dag_cbor.encode({'a': 12, 'b': 'hello!'})
        b'\xa2aa\x0cabfhello!'

        If a ``stream`` is given, the encoded data is written to the stream and the number of bytes written is returned:

        .. code-block:: python

            def encode(data: IPLDKind, stream: BufferedIOBase) -> int:
                ...

        Example usage with a stream:

        >>> from io import BytesIO
        >>> stream = BytesIO()
        >>> dag_cbor.encode({'a': 12, 'b': 'hello!'}, stream=stream)
        13
        >>> stream.getvalue()
        b'\xa2aa\x0cabfhello!'

        :param data: the DAG data to be encoded
        :param stream: an optional stream into which the encoded data should be written
        :param include_multicodec: if :obj:`True`, the encoded data is prefixed by the multicodec code for ``'dag-cbor'``
                                   (see `multicodec.wrap <https://multiformats.readthedocs.io/en/latest/api/multiformats.multicodec.html#wrap>`_).
        :param normalize_strings: whether strings should be normalised prior to encoding

        :raises CBOREncodingError: if an :obj:`int` outside of ``range(-2**64, 2**64)`` is encountered
        :raises DAGCBOREncodingError: if a value of type other than :obj:`None`, :obj:`bool`, :obj:`int`, :obj:`float`, :obj:`str`,
                                                      :obj:`bytes`, :obj:`list`, :obj:`dict`, or :class:`~multiformats.cid.CID` is encountered
        :raises DAGCBOREncodingError: if attempting to encode the special :obj:`float` values ``NaN``, ``Infinity`` and ``-Infinity``
        :raises DAGCBOREncodingError: if a key of a dictionary is not a string

    """
    validate(stream, Optional[BufferedIOBase])
    validate(include_multicodec, bool)
    options: _EncodeOptions = {}
    if normalize_strings is not None:
        validate(normalize_strings, Literal["NFC", "NFKC", "NFD", "NFKD"])
        options["normalize_strings"] = normalize_strings
    path = IPLDObjPath()
    if stream is None:
        internal_stream = BytesIO()
        if include_multicodec:
            internal_stream.write(_dag_cbor_code_bytes)
        _encode(internal_stream, data, path, options)
        return internal_stream.getvalue()
    num_bytes = 0
    if include_multicodec:
        stream.write(_dag_cbor_code_bytes)
        num_bytes += _dag_cbor_code_nbytes
    num_bytes += _encode(stream, data, path, options)
    return num_bytes

class _EncodeOptions(TypedDict, total=False):
    r""" Options passed around to encoding sub-routines. """

    normalize_strings: Literal["NFC", "NFKC", "NFD", "NFKD"]
    r""" Optional Unicode normalization to be performed on UTF-8 strings prior to byte encoding. """

def _encode(stream: BufferedIOBase, value: IPLDKind, path: IPLDObjPath, options: _EncodeOptions) -> int:
    # pylint: disable = too-many-return-statements, too-many-branches
    if isinstance(value, bool): # must go before int check
        # major type 0x7 (additional info 20 and 21)
        return _encode_bool(stream, value, path, options)
    if isinstance(value, int):
        # major types 0x0 and 0x1
        return _encode_int(stream, value, path, options)
    if isinstance(value, bytes):
        # major type 0x2
        return _encode_bytes(stream, value, path, options)
    if isinstance(value, str):
        # major type 0x3
        return _encode_str(stream, value, path, options)
    if isinstance(value, list):
        # major type 0x4
        return _encode_list(stream, value, path, options)
    if isinstance(value, dict):
        # major type 0x5
        return _encode_dict(stream, value, path, options)
    if isinstance(value, CID):
        # major type 0x6
        return _encode_cid(stream, value, path, options)
    if value is None:
        # major type 0x7 (additional info 22)
        return _encode_none(stream, value, path, options)
    if isinstance(value, float):
        # major type 0x7 (additional info 27)
        return _encode_float(stream, value, path, options)
    err = f"Error encoding value at {path}: value is not of IPLD kind (found type {type(value)})."
    raise DAGCBOREncodingError(err)

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

def _encode_int(stream: BufferedIOBase, value: int, path: IPLDObjPath, options: _EncodeOptions) -> int:
    if value >= 18446744073709551616:
        # unsigned int must be < 2**64
        err = f"Error encoding integer value at {path}: Unsigned integer out of range."
        raise CBOREncodingError(err)
    if value < -18446744073709551616:
        # negative int must be >= -2**64
        err = f"Error encoding integer value at {path}: Negative integer out of range."
        raise CBOREncodingError(err)
    if value >= 0:
        # unsigned int
        return _encode_head(stream, 0x0, value)
    # negative int
    return _encode_head(stream, 0x1, -1-value)

def _encode_bytes(stream: BufferedIOBase, value: bytes, path: IPLDObjPath, options: _EncodeOptions) -> int:
    num_head_bytes = _encode_head(stream, 0x2, len(value))
    stream.write(value)
    return num_head_bytes+len(value)

def _encode_str(stream: BufferedIOBase, value: str, path: IPLDObjPath, options: _EncodeOptions) -> int:
    if "normalize_strings" in options:
        value = unicodedata.normalize(options["normalize_strings"], value)
    utf8_value: bytes = value.encode("utf-8", errors="strict")
    num_head_bytes = _encode_head(stream, 0x3, len(utf8_value))
    stream.write(utf8_value)
    return num_head_bytes+len(utf8_value)

def _encode_list(stream: BufferedIOBase, value: List[Any], path: IPLDObjPath, options: _EncodeOptions) -> int:
    num_bytes_written = _encode_head(stream, 0x4, len(value))
    for idx, item in enumerate(value):
        num_bytes_written += _encode(stream, item, path/idx, options)
    return num_bytes_written

def _encode_dict(stream: BufferedIOBase, value: Dict[str, Any], path: IPLDObjPath, options: _EncodeOptions) -> int:
    _check_key_compliance(value, path)
    if "normalize_strings" in options:
        nf = options["normalize_strings"]
        value = {unicodedata.normalize(nf, k): v for k, v in value.items()}
    utf8key_val_pairs = [(k, k.encode("utf-8", errors="strict"), v)
                         for k, v in value.items()]
    # 1. sort keys canonically:
    sorted_utf8key_val_pairs = sorted(utf8key_val_pairs, key=lambda i: (len(i[1]), i[1]))
    # 2. encode key-value pairs (keys already utf-8 encoded):
    num_bytes_written = _encode_head(stream, 0x5, len(value))
    for k, utf8k, v in sorted_utf8key_val_pairs:
        num_bytes_written += _encode_head(stream, 0x3, len(utf8k))
        stream.write(utf8k)
        num_bytes_written += len(utf8k)
        num_bytes_written += _encode(stream, v, path/k, options)
    return num_bytes_written

def _encode_cid(stream: BufferedIOBase, value: CID, path: IPLDObjPath, options: _EncodeOptions) -> int:
    num_bytes_written = _encode_head(stream, 0x6, 42)
    num_bytes_written += _encode_bytes(stream, b"\0" + bytes(value), path, options)
    return num_bytes_written

def _encode_bool(stream: BufferedIOBase, value: bool, path: IPLDObjPath, options: _EncodeOptions) -> int:
    return _encode_head(stream, 0x7, 21 if value else 20)

def _encode_none(stream: BufferedIOBase, value: None, path: IPLDObjPath, options: _EncodeOptions) -> int:
    return _encode_head(stream, 0x7, 22)

def _encode_float(stream: BufferedIOBase, value: float, path: IPLDObjPath, options: _EncodeOptions) -> int:
    if math.isnan(value):
        err = f"Error encoding float value at {path}: NaN is not allowed."
        raise DAGCBOREncodingError(err)
    if math.isinf(value):
        s = "" if value > 0 else "-"
        err = f"Error encoding float value at {path}: {s}Infinity is not allowed."
        raise DAGCBOREncodingError(err)
    # special head, with double encoding for 4B argument value
    head = struct.pack(">Bd", (0x7<<5)|27, value)
    stream.write(head)
    return len(head)

def _check_key_compliance(value: Dict[str, Any], path: Optional[IPLDObjPath] = None) -> None:
    """ Check keys for DAG-CBOR compliance. """
    for idx, k in enumerate(value.keys()):
        if not isinstance(k, str):
            err = "" if path is None else f"Error encoding value of map kind at {path}: "
            err += f"key for key-value pair at position {idx} is not a string."
            raise DAGCBOREncodingError(err)

def _canonical_order_dict(value: Dict[str, Any]) -> Dict[str, Any]:
    utf8key_key_val_pairs = [(k.encode("utf-8", errors="strict"), k, v) for k, v in value.items()]
    sorted_utf8key_key_val_pairs = sorted(utf8key_key_val_pairs, key=lambda i: (len(i[0]), i[0]))
    return {k: v for _, k, v in sorted_utf8key_key_val_pairs}
