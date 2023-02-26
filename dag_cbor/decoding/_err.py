r"""
    Detailed messages for all possible DAG-CBOR decoding errors.
"""

from __future__ import annotations # See https://peps.python.org/pep-0563/

import math
from typing import Tuple
from typing_extensions import Literal

from multiformats import varint

from ..ipld import IPLDKind
from ..encoding import _dag_cbor_code
from .err import CBORDecodingError
from ._stream import Stream, StreamSnapshot
from ._err_utils import _bytes2hex, _decode_error_msg_lines, _decode_error_msg, _extract_error_cause_lines, _cid_error_template

def _required_multicodec(stream: Stream) -> str:
    curr_snapshot = stream.curr_snapshot
    msg = "Required 'dag-cbor' multicodec code."
    exp_bs = varint.encode(_dag_cbor_code)
    details = f"byte{'s' if curr_snapshot.latest_read_size > 1 else ''} should be 0x{exp_bs.hex()}."
    return _decode_error_msg(msg, curr_snapshot, details=details)

def _multiple_top_level_items(stream: Stream) -> str:
    msg = "Encode and decode must operate on a single top-level CBOR object."
    details = "unexpected start byte of a second top-level CBOR object"
    return _decode_error_msg(msg, stream.curr_snapshot, details=details)

def _invalid_float(stream: Stream, arg: float) -> str:
    if math.isnan(arg):
        msg = "NaN is not an allowed float value."
        float_str = "float('NaN')"
    else:
        assert math.isinf(arg), "Float must be NaN or infinite."
        s = ("" if arg > 0 else "-")
        msg = s+"Infinity is not an allowed float value."
        float_str = f"float('{s}Infinity')"
    details = f"struct.pack('>d', {float_str})"
    return _decode_error_msg(msg, stream.curr_snapshot, details=details, hl_start=1)

def _unexpected_eof(stream: Stream, what: str, n: int, include_prev_snapshot: bool = True) -> str:
    prev_snapshot = stream.prev_snapshot if include_prev_snapshot else StreamSnapshot(bytes(), 0)
    curr_snapshot = stream.curr_snapshot
    msg = f"Unexpected EOF while attempting to read {what}."
    bytes_read = curr_snapshot.latest_read_size
    hl_start = prev_snapshot.latest_read_size
    details = f"{bytes_read} bytes read, out of {n} expected."
    snapshots = [prev_snapshot, curr_snapshot] if include_prev_snapshot else [curr_snapshot]
    return _decode_error_msg(msg, *snapshots, details=details, hl_start=hl_start)

def _invalid_additional_info(stream: Stream, additional_info: int, major_type: int) -> str:
    msg = f"Invalid additional info {additional_info} in data item head for major type 0x{major_type:x}."
    if major_type == 0x7:
        details = f"lower 5 bits are {additional_info:0>5b}, expected from {0:0>5b} to {23:0>5b}, or {27:0>5b}."
    else:
        details = f"lower 5 bits are {additional_info:0>5b}, expected from {0:0>5b} to {27:0>5b}."
    return _decode_error_msg(msg, stream.curr_snapshot, details=details)

def _excessive_int_size(stream: Stream, arg: int, bytes_used: int, bytes_sufficient: int) -> str:
    s = 's' if bytes_sufficient > 1 else ''
    msg = f"Integer {arg} was encoded using {bytes_used} bytes, while {bytes_sufficient} byte{s} would have been enough."
    details = f"same as byte{s} 0x{arg:0>{2*bytes_sufficient}x}"
    return _decode_error_msg(msg, stream.prev_snapshot, stream.curr_snapshot, details=details, hl_start=1)

def _unicode(stream: Stream, length: int, start: int, end: int, reason: str) -> str:
    prev_snapshot = stream.prev_snapshot
    curr_snapshot = stream.curr_snapshot
    msg = "String bytes are not valid utf-8 bytes."
    lines = [msg]
    str_details = f"string of length {length}"
    lines.extend(_decode_error_msg_lines(prev_snapshot, curr_snapshot, details=str_details, hl_len=1))
    lines.extend(_decode_error_msg_lines(curr_snapshot, details=reason, start=start, end=end, pad_start=start+prev_snapshot.latest_read_size))
    return "\n".join(lines)

def _list_item(list_head_snapshot: StreamSnapshot, idx: int, length: int, e: CBORDecodingError) -> str:
    msg = "Error while decoding list."
    lines = [
        msg,
        *_decode_error_msg_lines(list_head_snapshot, details=f"list of length {length}", dots=True),
        f"Error occurred while decoding item at position {idx}: further details below.",
        *_extract_error_cause_lines(e)
    ]
    return "\n".join(lines)

def _dict_key_type(stream: Stream, major_type: int) -> str:
    msg = "Dictionary key is not of string type."
    details = f"major type is {hex(major_type)}, should be 0x3 (string) instead."
    return _decode_error_msg(msg, stream.curr_snapshot, details=details, hl_len=1, dots=True)

def _dict_item(dict_head_snapshot: StreamSnapshot, item: Literal["key", "value"], idx: int, length: int, e: CBORDecodingError) -> str:
    msg = "Error while decoding dict."
    details = f"dict of length {length}"
    lines = [
        msg,
        *_decode_error_msg_lines(dict_head_snapshot, details=details, dots=True),
        f"Error occurred while decoding {item} at position {idx}: further details below.",
        *_extract_error_cause_lines(e)
    ]
    return "\n".join(lines)

def _duplicate_dict_key(dict_head_snapshot: StreamSnapshot, stream: Stream, k: str, idx: int, length: int) -> str:
    msg = "Error while decoding dict."
    dict_details = f"dict of length {length}"
    key_details = f"decodes to key {repr(k)}"
    lines = [
        msg,
        *_decode_error_msg_lines(dict_head_snapshot, details=dict_details, dots=True),
        f"Duplicate key is found at position {idx}.",
        *_decode_error_msg_lines(stream.curr_snapshot, details=key_details)
    ]
    return "\n".join(lines)

def _dict_key_order(dict_head_snapshot: StreamSnapshot, kb0: bytes, idx0: int, kb1: bytes, idx1: int, length: int) -> str:
    # pylint: disable = too-many-arguments
    msg = "Error while decoding dict."
    pad_len = max(len(str(idx0)), len(str(idx1)))
    idx0_str = f"{idx0: >{pad_len}}"
    idx1_str = f"{idx1: >{pad_len}}"
    details = f"dict of length {length}"
    lines = [
        msg,
        *_decode_error_msg_lines(dict_head_snapshot, details=details, dots=True),
        "Dictionary keys not in canonical order.",
        f"  Key at pos #{idx0_str}: {_bytes2hex(kb0)}",
        f"  Key at pos #{idx1_str}: {_bytes2hex(kb1)}",
    ]
    return "\n".join(lines)

def _invalid_tag(stream: Stream, arg: int) -> str:
    prev_snapshot = stream.prev_snapshot
    curr_snapshot = stream.curr_snapshot
    msg = "Error while decoding item of major type 0x6: only tag 42 is allowed."
    details = f"tag {arg}"
    hl_start = prev_snapshot.latest_read_size
    return _decode_error_msg(msg, prev_snapshot, curr_snapshot, details=details, hl_start=hl_start)

def _cid(cid_head_snapshots: Tuple[StreamSnapshot, StreamSnapshot], e: CBORDecodingError) -> str:
    return _cid_error_template(cid_head_snapshots, *_extract_error_cause_lines(e))

def _cid_bytes(cid_head_snapshots: Tuple[StreamSnapshot, StreamSnapshot], stream: Stream, cid_bytes: IPLDKind) -> str:
    decoded_type = type(cid_bytes).__name__
    details = f"decodes to an item of type {repr(decoded_type)}"
    explanation = [
        "CID bytes did not decode to an item of type 'bytes'.",
        *_decode_error_msg_lines(stream.curr_snapshot, details=details),
    ]
    return _cid_error_template(cid_head_snapshots, *explanation)

def _cid_multibase(cid_head_snapshots: Tuple[StreamSnapshot, StreamSnapshot], stream: Stream, cid_bytes: bytes) -> str:
    details = "byte should be 0x00"
    explanation = [
        "CID does not start with the identity Multibase prefix.",
        *_decode_error_msg_lines(stream.prev_snapshot, stream.curr_snapshot, details=details, hl_start=1, hl_len=1),
    ]
    return _cid_error_template(cid_head_snapshots, *explanation)

def _simple_value(stream: Stream, arg: int) -> str:
    msg = "Error while decoding major type 0x7: allowed simple values are 0x14, 0x15 and 0x16."
    details = f"simple value is {arg}"
    return _decode_error_msg(msg, stream.curr_snapshot, details=details)
