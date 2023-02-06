r"""
    Utility functions used to produce messages for DAG-CBOR decoding errors.
"""

from __future__ import annotations # See https://peps.python.org/pep-0563/

from typing import List, Optional, Tuple

from .err import CBORDecodingError
from ._stream import StreamSnapshot

_TRUNC_BYTES = 16

def _bytes2hex(bs: bytes) -> str:
    r"""
        Converts bytes to a hex string, showing a truncated string if the number of bytes exceeds 16.
    """
    if len(bs) <= _TRUNC_BYTES:
        return bs.hex()
    return bs[:1].hex()+"..."+bs[-1:].hex() # fixed length 7 < 2*_TRUNC_BYTES

def _decode_error_msg_lines(*snapshots: StreamSnapshot, details: Optional[str] = None,
                            start: int = 0,
                            end: Optional[int] = None,
                            pad_start: int = 0,
                            hl_start: int = 0,
                            hl_len: Optional[int] = None,
                            dots: bool = False,
                            ) -> List[str]:
    r"""
        This utility function takes one or more stream snapshots as input and collates the chunks of read bytes. Let ``bs`` be the bytes read across the
        snapshots (which are assumed to be sequential) and ``pos`` be the position in the stream of the first byte of ``bs`` (he ``start`` and ``end`` arguments
        can be used to focus on a sub-range):

        .. code-block:: python

            bs = b"".join((snapshot.latest_read for snapshot in snapshots))[start:end]
            pos = snapshots[0].latest_read_start+start

        Th utility function returns one or two lines of error message, based on that information:

        1. The first line shows (a selection of) the bytes read and the position of the first byte in the stream
        2. If ``details`` is specified, the second line highlights a selection of bytes from the first line, followed by the given details

        The following optional keyword arguments can be used to customise the selection of read bytes and the highlighting.

        - The ``pad_start`` arguments can be used to specify whitespace padding at the start of the bytes shown, to align them to bytes on other error lines.
        - The ``hl_start`` and ``hl_len`` arguments can be used to specify the start byte and lenght of the range of bytes highlighted in the second line.
        - The ``dots`` argument can be used to specify that three dots '...' should be added after the bytes, to indicate continuation.

    """
    # pylint: disable = too-many-locals
    assert snapshots
    bs = b"".join((snapshot.latest_read for snapshot in snapshots))[start:end]
    pos = snapshots[0].latest_read_start+start
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
    bs_str = "  "*pad_start+bs_str
    bs_tab = "  "*pad_start+bs_tab
    bytes_line = f"At byte #{pos}: {bs_str}"
    if truncated:
        last_byte_idx = pos+len(bs)-1
        bytes_line += f" (last byte #{last_byte_idx})"
    if dots:
        bytes_line += "..."
    lines = [bytes_line]
    if details is not None:
        details_line = f"         {' '*len(str(pos))}  {bs_tab} {details}"
        lines.append(details_line)
    return lines

def _decode_error_msg(msg: str, *snapshots: StreamSnapshot, details: Optional[str] = None,
                      start: int = 0,
                      end: Optional[int] = None,
                      hl_start: int = 0,
                      hl_len: Optional[int] = None,
                      dots: bool = False,
                      ) -> str:
    r"""
        Creates a detailed, multi-line error message, starting from a given ``msg`` and taking into account the information from one or more stream snapshots.
        The resulting error message has ``msg`` on the first line, followed by the lines returned by :func:`_decode_error_msg_lines`.
    """
    lines = [msg]
    if snapshots:
        lines.extend(_decode_error_msg_lines(*snapshots, details=details,
                                         start=start, end=end, hl_start=hl_start, hl_len=hl_len,
                                         dots=dots))
    return "\n".join(lines)


def _extract_error_cause_lines(e: CBORDecodingError) -> List[str]:
    r""" Extracts lines of error description from a :class:`CBORDecodingError`. """
    lines = str(e).split("\n")
    return [(r"\ " if idx == 0 else "  ")+line for idx, line in enumerate(lines)]


def _cid_error_template(cid_head_snapshots: Tuple[StreamSnapshot, StreamSnapshot], *explanation: str) -> str:
    r""" Template for CID errors. """
    lines = [
        "Error while decoding CID.",
        *_decode_error_msg_lines(*cid_head_snapshots, details="CID tag", dots=True),
        *explanation
    ]
    return "\n".join(lines)
