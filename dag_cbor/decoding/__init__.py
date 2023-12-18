"""
    Deconding function for DAG-CBOR codec.
"""

from __future__ import annotations # See https://peps.python.org/pep-0563/

from io import BufferedIOBase, BytesIO
import math
import struct
import sys
from typing import Any, Dict, Callable, List, Optional, Sequence, Tuple, Union
import unicodedata
from typing_extensions import Literal, Protocol, TypedDict
from typing_validation import validate

from multiformats import multicodec, CID, varint

from ..ipld import IPLDKind
from ..encoding import _dag_cbor_code
from .err import CBORDecodingError, DAGCBORDecodingError
from . import _err
from ._stream import Stream

__all__ = ("CBORDecodingError", "DAGCBORDecodingError")

class DecodeCallback(Protocol):
    r"""
        Type of optional callbacks for the :func:`decode` function.
    """
    def __call__(self, value: IPLDKind, num_bytes_read: int) -> None:
        ...

class _DecodeOptions(TypedDict, total=False):
    r""" Options passed around to decoding sub-routines. """

    callback: "DecodeCallback"
    r""" An optional callback to be called on each decoded item. """

    normalize_strings: Literal["NFC", "NFKC", "NFD", "NFKD"]
    r""" Optional Unicode normalization to be performed on decoded UTF-8 strings. """

def decode(stream_or_bytes: Union[BufferedIOBase, bytes], *,
           allow_concat: bool = False,
           callback: Optional["DecodeCallback"] = None,
           require_multicodec: bool = False,
           normalize_strings: Literal["NFC", "NFKC", "NFD", "NFKD", None] = None) -> IPLDKind:
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
        :param allow_concat: whether to allow partial stream decoding (if this is :obj:`False`, a byte stream will always be consumed in its entirety)
        :param callback: optional callback to be invoked as ``callback(item, num_bytes_read)`` every time an item is decoded,
                         where ``num_bytes_read`` is the number of bytes read decoding the item (excluding sub-items, in the case of lists or dictionaries).
        :param require_multicodec: if :obj:`True`, the data being decoded must be prefixed by the multicodec code for ``'dag-cbor'``
                                   (see `multicodec.unwrap <https://multiformats.readthedocs.io/en/latest/api/multiformats.multicodec.html#unwrap>`_).
        :param normalize_strings: whether strings should be normalised after decoding

        :raises CBORDecodingError: while reading the leading byte of a data item head, if no bytes are available
        :raises CBORDecodingError: while reading the argument bytes of a data item head,
                                                   if the expected number of argument bytes is not available
        :raises CBORDecodingError: while decoding the data of a bytestring or string, if the expected number of data bytes is not available
        :raises CBORDecodingError: while decoding the items of a list or a map (keys and values),
                                                   if the expected number of items is not available
        :raises CBORDecodingError: if an invalid utf-8 byte sequence is encountered while attempting to decode a string
        :raises DAGCBORDecodingError: if attempting to decode the special :obj:`float` values ``NaN``, ``Infinity`` and ``-Infinity``
        :raises DAGCBORDecodingError: if the additional info is greater than 27, or different from 27 for major type 7
        :raises DAGCBORDecodingError: if an integer value was not minimally encoded
        :raises DAGCBORDecodingError: if a key of a map is not a string
        :raises DAGCBORDecodingError: if a map has repeated keys
        :raises DAGCBORDecodingError: if map keys are not in canonical order
        :raises DAGCBORDecodingError: if a tag (major type 6) different than 42 (for CID data) is encountered
        :raises DAGCBORDecodingError: if non-bytestring data is found where CID data is expected (tag 42)
        :raises DAGCBORDecodingError: if a simple value (major type 7) different from 20 (False), 21 (True) or 22 (None) is encountered
        :raises DAGCBORDecodingError: if ``require_multicodec`` is set to :obj:`True` and
                                                      the bytes are not prefixed by the ``'dag-cbor'`` multicodec code
        :raises DAGCBORDecodingError: if ``allow_concat`` is set to :obj:`False` and the decoding did not use all available bytes

    """
    validate(stream_or_bytes, Union[BufferedIOBase, bytes])
    validate(allow_concat, bool)
    validate(require_multicodec, bool)
    options: _DecodeOptions = {}
    if callback is not None:
        options["callback"] = callback
    if normalize_strings is not None:
        validate(normalize_strings, Literal["NFC", "NFKC", "NFD", "NFKD"])
        options["normalize_strings"] = normalize_strings
    if isinstance(stream_or_bytes, bytes):
        _stream: BufferedIOBase = BytesIO(stream_or_bytes)
    else:
        _stream = stream_or_bytes
    if require_multicodec:
        code, _, _stream = multicodec.unwrap_raw(_stream)
        stream = Stream(_stream, varint.encode(code))
        if code != _dag_cbor_code:
            raise DAGCBORDecodingError(_err._required_multicodec(stream))
    else:
        stream = Stream(_stream)
    data, _ = _decode_item(stream, options)
    if not allow_concat:
        remaining_bytes = stream.read()
        if len(remaining_bytes) > 0:
            raise DAGCBORDecodingError(_err._multiple_top_level_items(stream))
    return data

def _decode_item(stream: Stream, options: _DecodeOptions) -> Tuple[IPLDKind, int]:
    major_type, arg, num_bytes_read = _decode_head(stream)
    ret: Optional[Tuple[IPLDKind, int]] = None
    assert 0x0 <= major_type <= 0x7, f"Major type must be one of 0x0-0x7, found 0x{major_type:x} instead."
    if isinstance(arg, float):
        # Major type 0x7 (float case):
        assert major_type == 0x7, f"Major type for float must be 0x7, found 0x{major_type:x} instead."
        if math.isnan(arg) or math.isinf(arg):
            raise DAGCBORDecodingError(_err._invalid_float(stream, arg))
        ret = (arg, num_bytes_read)
    elif major_type <= 0x1:
        # Major types 0x0 and 0x1:
        ret = (arg if major_type == 0x0 else -1-arg, num_bytes_read)
    else:
        # Major types 0x2-0x6 and 0x7 (bool/null case):
        value, num_bytes_further_read = _decoders[major_type](stream, arg, options)
        ret = (value, num_bytes_read+num_bytes_further_read)
    if "callback" in options:
        options["callback"](*ret)
    return ret


def _decode_head(stream: Stream) -> Tuple[int, Union[int, float], int]:
    # pylint: disable = too-many-branches
    # read leading byte
    res = stream.read(1)
    if len(res) < 1:
        raise CBORDecodingError(_err._unexpected_eof(stream, "leading byte of data item head", 1, include_prev_snapshot=False))
    leading_byte = res[0]
    major_type = leading_byte >> 5
    additional_info = leading_byte & 0b11111
    # read argument value and return (major_type, arg, num_bytes_read)
    if additional_info < 24:
        # argument value = additional info
        return (major_type, additional_info, 1)
    if additional_info > 27 or (major_type == 0x7 and additional_info != 27):
        raise DAGCBORDecodingError(_err._invalid_additional_info(stream, additional_info, major_type))
    argument_nbytes = 1<<(additional_info-24)
    res = stream.read(argument_nbytes)
    if len(res) < argument_nbytes:
        raise CBORDecodingError(_err._unexpected_eof(stream, f"{argument_nbytes} byte argument of data item head", argument_nbytes))
    if additional_info == 24:
        # 1 byte of unsigned int argument value to follow
        if res[0] < 24:
            raise DAGCBORDecodingError(_err._excessive_int_size(stream, res[0], 1, 0))
        return (major_type, res[0], 2)
    if additional_info == 25:
        # 2 bytes of unsigned int argument value to follow
        arg = struct.unpack(">H", res)[0]
        if arg <= 255:
            raise DAGCBORDecodingError(_err._excessive_int_size(stream, arg, 2, 1))
        return (major_type, arg, 3)
    if additional_info == 26:
        # 4 bytes of unsigned int argument value to follow
        arg = struct.unpack(">L", res)[0]
        if arg <= 65535:
            if arg <= 255:
                raise DAGCBORDecodingError(_err._excessive_int_size(stream, arg, 4, 1))
            raise DAGCBORDecodingError(_err._excessive_int_size(stream, arg, 4, 2))
        return (major_type, arg, 5)
    # necessarily additional_info == 27
    if major_type == 0x7:
        # 8 bytes of float argument value to follow
        return (major_type, struct.unpack(">d", res)[0], 9)
    # 8 bytes of unsigned int argument value to follow
    arg = struct.unpack(">Q", res)[0]
    if arg <= 4294967295:
        if arg <= 255:
            raise DAGCBORDecodingError(_err._excessive_int_size(stream, arg, 8, 1))
        if arg <= 65535:
            raise DAGCBORDecodingError(_err._excessive_int_size(stream, arg, 8, 2))
        raise DAGCBORDecodingError(_err._excessive_int_size(stream, arg, 8, 4))
    return (major_type, arg, 9)

def _decode_bytes(stream: Stream, length: int, options: _DecodeOptions) -> Tuple[bytes, int]:
    res = stream.read(length)
    if len(res) < length:
        raise CBORDecodingError(_err._unexpected_eof(stream, f"{length} bytes of bytestring", length))
    return (res, length)

def _decode_str(stream: Stream, length: int, options: _DecodeOptions) -> Tuple[str, int]:
    res = stream.read(length)
    if len(res) < length:
        raise CBORDecodingError(_err._unexpected_eof(stream, f"{length} bytes of string", length))
    try:
        s = res.decode(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as e:
        raise CBORDecodingError(_err._unicode(stream, length, e.start, e.end, e.reason)) # pylint: disable = raise-missing-from
    if "normalize_strings" in options:
        s = unicodedata.normalize(options["normalize_strings"], s)
    return (s, length)

def _decode_list(stream: Stream, length: int, options: _DecodeOptions) -> Tuple[List[Any], int]:
    list_head_snapshot = stream.curr_snapshot
    l: List[Any] = []
    for idx in range(length):
        try:
            item, _ = _decode_item(stream, options)
            l.append(item)
        except CBORDecodingError as e:
            raise CBORDecodingError(_err._list_item(list_head_snapshot, idx, length, e)) # pylint: disable = raise-missing-from
    return (l, 0)

def _decode_dict_key(stream: Stream, key_idx: int, dict_length: int, options: _DecodeOptions) -> Tuple[str, int, bytes]:
    # pylint: disable = too-many-return-statements, too-many-branches
    major_type, arg, num_bytes_read = _decode_head(stream)
    ret: Optional[Tuple[IPLDKind, int]] = None
    if major_type != 0x3:
        raise DAGCBORDecodingError(_err._dict_key_type(stream, major_type))
    assert not isinstance(arg, float)
    str_length = arg
    str_bytes: bytes = stream.read(str_length)
    if len(str_bytes) < str_length:
        raise CBORDecodingError(_err._unexpected_eof(stream, f"{str_length} bytes of string", str_length))
    try:
        s = str_bytes.decode(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as e:
        raise CBORDecodingError(_err._unicode(stream, str_length, e.start, e.end, e.reason)) # pylint: disable = raise-missing-from
    if "normalize_strings" in options:
        s = unicodedata.normalize(options["normalize_strings"], s)
    ret = (s, num_bytes_read+str_length)
    if "callback" in options:
        options["callback"](*ret)
    return ret+(str_bytes,)

def _decode_dict(stream: Stream, length: int, options: _DecodeOptions) -> Tuple[Dict[str, Any], int]:
    # pylint: disable = too-many-locals
    dict_head_snapshot = stream.curr_snapshot
    d: Dict[str, Any] = {}
    key_bytes_list: List[bytes] = []
    for i in range(length):
        try:
            k, _, k_bytes = _decode_dict_key(stream, i, length, options)
        except CBORDecodingError as e:
            raise CBORDecodingError(_err._dict_item(dict_head_snapshot, "key", i, length, e)) # pylint: disable = raise-missing-from
        if k in d:
            raise DAGCBORDecodingError(_err._duplicate_dict_key(dict_head_snapshot, stream, k, i, length))
        try:
            v, _ = _decode_item(stream, options)
        except CBORDecodingError as e:
            raise CBORDecodingError(_err._dict_item(dict_head_snapshot, "value", i, length, e)) # pylint: disable = raise-missing-from
        d[k] = v
        key_bytes_list.append(k_bytes)
    # check that keys are sorted canonically
    assert len(key_bytes_list) == length
    sorted_key_bytes_list = sorted(key_bytes_list, key=lambda e: (len(e), e))
    for idx0, (kb0, kb1) in enumerate(zip(key_bytes_list, sorted_key_bytes_list)):
        if kb0 != kb1:
            idx1 = key_bytes_list.index(kb1)
            raise DAGCBORDecodingError(_err._dict_key_order(dict_head_snapshot, kb0, idx0, kb1, idx1, length))
    return (d, 0)

def _decode_cid(stream: Stream, arg: int, options: _DecodeOptions) -> Tuple[CID, int]:
    if arg != 42:
        raise DAGCBORDecodingError(_err._invalid_tag(stream, arg))
    cid_head_snapshots = stream.prev_snapshot, stream.curr_snapshot
    try:
        if "callback" in options:
            options = {**options}
            del options["callback"]
        cid_bytes, num_bytes_read = _decode_item(stream, options)
    except CBORDecodingError as e:
        raise CBORDecodingError(_err._cid(cid_head_snapshots, e)) # pylint: disable = raise-missing-from
    if not isinstance(cid_bytes, bytes):
        raise DAGCBORDecodingError(_err._cid_bytes(cid_head_snapshots, stream, cid_bytes))
    if not cid_bytes[0] == 0:
        raise DAGCBORDecodingError(_err._cid_multibase(cid_head_snapshots, stream, cid_bytes))
    return (CID.decode(cid_bytes[1:]), num_bytes_read)

def _decode_bool_none(stream: Stream, arg: int, options: _DecodeOptions) -> Tuple[Optional[bool], int]:
    if arg == 20:
        return (False, 0)
    if arg == 21:
        return (True, 0)
    if arg == 22:
        return (None, 0)
    raise DAGCBORDecodingError(_err._simple_value(stream, arg))

def _decode_dummy(stream: Stream, arg: int, options: _DecodeOptions) -> Tuple[None, int]:
    assert False, f"Major type {arg} does not have an associated decoder."

_decoders: Tuple[Callable[[Stream, int, _DecodeOptions], Tuple[IPLDKind, int]], ...] = (
    _decode_dummy,
    _decode_dummy,
    _decode_bytes,
    _decode_str,
    _decode_list,
    _decode_dict,
    _decode_cid,
    _decode_bool_none
)
