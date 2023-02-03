r"""
    Utility functions used to produce messages for DAG-CBOR decoding errors.
"""

from typing import List, Optional

from ..utils import CBORDecodingError
from ._stream import StreamSnapshot

_TRUNC_BYTES = 16

def _bytes2hex(bs: bytes) -> str:
    if len(bs) <= _TRUNC_BYTES:
        return bs.hex()
    return bs[:1].hex()+"..."+bs[-1:].hex() # fixed length 7 < 2*_TRUNC_BYTES

def _decode_error_lines(*snapshots: StreamSnapshot, details: Optional[str] = None,
                        eof: bool = False,
                        start: Optional[int] = None,
                        end: Optional[int] = None,
                        pad_start: int = 0,
                        pad_end: int = 0,
                        hl_start: int = 0,
                        hl_len: Optional[int] = None,
                        dots: bool = False,
                        ) -> List[str]:
    # pylint: disable = too-many-locals
    assert snapshots
    bs = bytes()
    pos = snapshots[0].latest_read_start
    for snapshot in snapshots:
        bs += snapshot.latest_read
    if start is None:
        start = 0
    if end is None:
        end = len(bs)
    assert 0 <= start <= end <= len(bs)
    assert pad_start >= 0
    assert pad_end >= 0
    assert hl_start >= 0
    bs = bs[start:end]
    pos += start
    pos_str = str(pos)
    pos_tab = " "*len(pos_str)
    bs_str = _bytes2hex(bs)
    truncated = len(bs_str) != 2*len(bs)
    if not bs_str:
        bs_str = "<EOF>"
        bs_tab = "^"*len(bs_str)
    else:
        if hl_len is None:
            hl_len = len(bs)-hl_start
        else:
            assert 0 <= hl_len <= len(bs)-start
        if truncated and not (hl_len == 1 and (hl_start in {0, len(bs)-1})):
            bs_tab = "^"*len(bs_str)
        else:
            bs_tab = "  "*hl_start+"^^"*hl_len
    bs_str = "  "*pad_start+bs_str+"  "*pad_end
    bs_tab = "  "*pad_start+bs_tab
    bytes_line = f"At byte #{pos_str}: {bs_str}"
    if truncated:
        last_byte_idx = pos+len(bs)-1
        bytes_line += f" (last byte #{last_byte_idx})"
    if dots:
        bytes_line += "..."
    descr_line = f"         {pos_tab}  {bs_tab} {details}"
    lines = [bytes_line]
    if details is not None:
        lines.append(descr_line)
    return lines

def _decode_error_msg(msg: str, *snapshots: StreamSnapshot, details: Optional[str] = None,
                      eof: bool = False,
                      start: Optional[int] = None,
                      end: Optional[int] = None,
                      hl_start: int = 0,
                      hl_len: Optional[int] = None,
                      dots: bool = False,
                      ) -> str:
    lines = [msg]
    lines.extend(_decode_error_lines(*snapshots, details=details, eof=eof,
                                     start=start, end=end, hl_start=hl_start, hl_len=hl_len,
                                     dots=dots))
    return "\n".join(lines)


def _extract_error_cause_lines(e: CBORDecodingError) -> List[str]:
    lines = str(e).split("\n")
    return [(r"\ " if idx == 0 else "  ")+line for idx, line in enumerate(lines)]


def _cid_error_template(cid_head_snapshots: tuple[StreamSnapshot, StreamSnapshot], *explanation: str) -> str:
    lines = [
        "Error while decoding CID.",
        *_decode_error_lines(*cid_head_snapshots, details="CID tag", dots=True),
        *explanation
    ]
    return "\n".join(lines)
