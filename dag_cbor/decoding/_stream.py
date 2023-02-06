r"""
    Byte-streams and snapshots used in DAG-CBOR decoding, keeping track of latest and previous read byte chunks for error reporting purposes.
"""

from __future__ import annotations # See https://peps.python.org/pep-0563/

from io import BufferedIOBase, BytesIO
from typing import Optional

class StreamSnapshot:
    r""" A snapshot of the current state of a byte-stream being decoded. """

    _bs: bytes
    _pos: int

    def __new__(cls, latest_read: bytes, next_read_start: int) -> "StreamSnapshot":
        instance = object.__new__(cls)
        instance._bs = latest_read
        instance._pos = next_read_start
        return instance

    @property
    def latest_read(self) -> bytes:
        r""" The latest byte chunk read from the stream. """
        return self._bs

    @property
    def latest_read_size(self) -> int:
        r""" Size of the latest byte chunk read from the stream. """
        return len(self._bs)

    @property
    def latest_read_start(self) -> int:
        r""" Start position in the stream for the latest byte chunk read. """
        return self._pos-len(self._bs)

    @property
    def num_bytes_read(self) -> int:
        r""" Total number of bytes read so far from the stream. """
        return self._pos


class Stream:
    r"""
        Container for the byte-stream being decoded, offering additional book-keeping functionality used to produce detailed error messages.
    """

    _buf: BufferedIOBase
    _bs: bytes
    _pos: int
    _prev_bs: bytes
    _prev_pos: int

    def __new__(cls, buffer: Optional[BufferedIOBase] = None, init_bytes_read: bytes = bytes()) -> "Stream":
        if buffer is None:
            buffer = BytesIO(bytes())
        instance = object.__new__(cls)
        instance._buf = buffer
        instance._bs = init_bytes_read
        instance._pos = len(init_bytes_read)
        instance._prev_bs = bytes()
        instance._prev_pos = 0
        return instance

    @property
    def curr_snapshot(self) -> "StreamSnapshot":
        r""" A snapshot of the current state of the stream. """
        return StreamSnapshot(self._bs, self._pos)

    @property
    def prev_snapshot(self) -> "StreamSnapshot":
        r""" A snapshot of the state of the stream immediately before the latest non-extending read. """
        return StreamSnapshot(self._prev_bs, self._prev_pos)

    def read(self, num_bytes: Optional[int] = None, *, extend: bool = False) -> bytes:
        r"""
            Read the given number of bytes from the stream. If :obj:`None`, reads all remaining bytes.
            If ``extend`` is set to :obj:`True`, the current stream snapshot (see :attr:`Stream.curr_snapshot`) is extended with the bytes just read,
            and the previous stream snapshot (see :attr:`Stream.prev_snapshot`) is kept.
            Otherwise, the previous snapshot is replaced with the current snaptshot, and a new current snapshot is created with the bytes just read.
        """
        bs = self._buf.read(num_bytes)
        if extend:
            self._bs += bs
            self._pos += len(bs)
        else:
            self._prev_bs = self._bs
            self._prev_pos = self._pos
            self._bs = bs
            self._pos += len(bs)
        return bs
