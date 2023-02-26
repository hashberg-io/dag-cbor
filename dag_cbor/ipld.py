r"""
    Types and functions relating to the IPLD data model `IPLD data model <https://ipld.io/docs/data-model/>`_.
"""

# Part of the dag-cbor library.
# Copyright (C) 2023 Hashberg Ltd

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

from __future__ import annotations # See https://peps.python.org/pep-0563/

from typing import ClassVar, Dict, Iterator, List, MutableMapping, overload, Sequence, Tuple, Union
from weakref import WeakValueDictionary

from typing_validation import validate

from multiformats import CID

IPLDScalarKind = Union[None, bool, int, float, str, bytes, CID]
r"""
    Python type alias for scalar `kinds <https://ipld.io/docs/data-model/kinds/>`_ in the IPLD data model:

    - :obj:`None` for the `Null kind <https://ipld.io/docs/data-model/kinds/#null-kind>`_
    - :obj:`bool` for the `Boolean kind <https://ipld.io/docs/data-model/kinds/#boolean-kind>`_
    - :obj:`int` for the `Integer kind <https://ipld.io/docs/data-model/kinds/#integer-kind>`_
    - :obj:`float` for the `Float kind <https://ipld.io/docs/data-model/kinds/#float-kind>`_
    - :obj:`str` for the `String kind <https://ipld.io/docs/data-model/kinds/#string-kind>`_
    - :obj:`bytes` for the `Bytes kind <https://ipld.io/docs/data-model/kinds/#bytes-kind>`_
    - :class:`CID` for the `Link kind <https://ipld.io/docs/data-model/kinds/#link-kind>`_

"""

IPLDKind = Union[IPLDScalarKind, List["IPLDKind"], Dict[str, "IPLDKind"]]
r"""
    Python type alias for `kinds <https://ipld.io/docs/data-model/kinds/>`_ in the IPLD data model:

    - :obj:`None` for the `Null kind <https://ipld.io/docs/data-model/kinds/#null-kind>`_
    - :obj:`bool` for the `Boolean kind <https://ipld.io/docs/data-model/kinds/#boolean-kind>`_
    - :obj:`int` for the `Integer kind <https://ipld.io/docs/data-model/kinds/#integer-kind>`_
    - :obj:`float` for the `Float kind <https://ipld.io/docs/data-model/kinds/#float-kind>`_
    - :obj:`str` for the `String kind <https://ipld.io/docs/data-model/kinds/#string-kind>`_
    - :obj:`bytes` for the `Bytes kind <https://ipld.io/docs/data-model/kinds/#bytes-kind>`_
    - :class:`CID` for the `Link kind <https://ipld.io/docs/data-model/kinds/#link-kind>`_
    - :obj:`List` for the `List kind <https://ipld.io/docs/data-model/kinds/#list-kind>`_
    - :obj:`Dict` for the `Map kind <https://ipld.io/docs/data-model/kinds/#map-kind>`_

"""

IPLDObjPathSegment = Union[int, str]
r"""
    An individual segment in a :class:`IPLDObjPath` within a IPLD value (see :obj:`IPLDKind` for the ). A segment can be an :obj:`int` or a :obj:`str`:

    - an :obj:`int` segment is a position, indexing an item in a value of List :obj:`IPLDKind` (a :obj:`List` in Python)
    - an :obj:`str` segment is a key, indexing a value in a value of Map :obj:`IPLDKind` (a :obj:`Dict` in Python)

"""

_IPLDObjPathSegments = Tuple[IPLDObjPathSegment, ...]
r"""
    Short type alias for multiple segments.
"""

class IPLDObjPath(Sequence[IPLDObjPathSegment]):
    r"""
        Path within an object of :obj:`IPLDKind`, as a sequence of :obj:`IPLDObjPathSegment`.
        Paths are immutable and hashable, and a path is a :obj:`Sequence` of the segments that constitute it.
    """

    _instances: ClassVar[MutableMapping[_IPLDObjPathSegments, IPLDObjPath]] = WeakValueDictionary()

    @staticmethod
    def parse(path_str: str) -> IPLDObjPath:
        r"""
            Parses a :class:`IPLDObjPath` from a string representation where segments are separated by `"/"`, such as that returned by
            :meth:`IPLDObjPath.__repr__`.
        """
        if path_str.startswith("IPLDObjPath()"):
            path_str = path_str[6:]
        if not path_str.startswith("/"):
            raise ValueError("Path must start with '/' or 'IPLDObjPath()/'.")
        segs: List[IPLDObjPathSegment] = []
        seg_str_list = path_str[1:].split("/")
        for idx, seg_str in enumerate(seg_str_list):
            if seg_str.startswith("'"):
                if not seg_str.endswith("'"):
                    raise ValueError(f"At segment {idx}: opening single quote without closing single quote.")
                segs.append(seg_str[1:-1])
            elif seg_str.startswith('"'):
                if not seg_str.endswith('"'):
                    raise ValueError(f"At segment {idx}: opening double quote without closing double quote.")
                segs.append(seg_str[1:-1])
            else:
                if not seg_str.isnumeric():
                    raise ValueError(f"At segment {idx}: segment is unquoted and not numeric.")
                segs.append(int(seg_str))
        return IPLDObjPath._new_instance(tuple(segs))

    @staticmethod
    def _new_instance(segments: Tuple[IPLDObjPathSegment, ...]) -> IPLDObjPath:
        r"""
            Returns an instance of :class:`IPLDObjPath` with given segments, without performing any validation.
        """
        instance = IPLDObjPath._instances.get(segments)
        if instance is None:
            instance = object.__new__(IPLDObjPath)
            instance._segments = segments
            IPLDObjPath._instances[segments] = instance
        return instance

    _segments: _IPLDObjPathSegments

    def __new__(cls, *segments: IPLDObjPathSegment) -> IPLDObjPath:
        r""" Constructor for :class:`IPLDObjPath`. """
        validate(segments, _IPLDObjPathSegments)
        return IPLDObjPath._new_instance(segments)

    def access(self, value: IPLDKind) -> IPLDKind:
        r"""
            Accesses the sub-value at this path in the given IPLD value.
            Can be written more expressively as `self >> value`, see :meth:`IPLDObjPath.__rshift__`.
        """
        return _access(self, value)

    def __truediv__(self, other: Union[IPLDObjPathSegment, IPLDObjPath]) -> IPLDObjPath:
        r"""
            The `/` operator can be used to create paths by concatenating segments. Below we use `_` as a suggestive name for an empty path, acting as root:

            >>> _ = IPLDObjPath()
            >>> p = _/2/'red'
            >>> p
            /2/'red'

            Concatenating an existing path with one or more segments returns a new path, extended by the given segments:

            >>> p/3
            /2/'red'/3
            >>> p/0/'blue'
            /2/'red'/0/'blue'

            Concatenating two paths yields a new path, where the end of the first path is treated as the root for the second:

            >>> q = _/0/'blue'
            >>> p/q
            /2/'red'/0/'blue'
        """
        if isinstance(other, (int, str)):
            return IPLDObjPath._new_instance(self._segments+(other,))
        if isinstance(other, IPLDObjPath):
            return IPLDObjPath._new_instance(self._segments+other._segments)
        return NotImplemented

    def __rtruediv__(self, other: Union[IPLDObjPathSegment, IPLDObjPath]) -> IPLDObjPath:
        r"""
            It is possible to prepend a single segment at a time to an existing path using `/` (a new path is returned):

            >>> _ = IPLDObjPath()
            >>> p = _/2/'red'
            >>> 1/p
            /1/2/'red'

            Prepending multiple segments requires brackets (because the `/` operator associates to the left):

            >>> 0/(1/p)
            /0/1/2/'red'
        """
        if isinstance(other, (int, str)):
            return IPLDObjPath._new_instance((other,)+self._segments)
        return NotImplemented

    def __len__(self) -> int:
        return len(self._segments)

    def __iter__(self) -> Iterator[IPLDObjPathSegment]:
        return iter(self._segments)

    @overload
    def __getitem__(self, idx: int) -> IPLDObjPathSegment:
        ...

    @overload
    def __getitem__(self, idx: slice) -> IPLDObjPath:
        ...

    def __getitem__(self, idx: Union[int, slice]) -> Union[IPLDObjPathSegment, IPLDObjPath]:
        if isinstance(idx, int):
            return self._segments[idx]
        return IPLDObjPath._new_instance(self._segments[idx])

    def __le__(self, other: IPLDObjPath) -> bool:
        r"""
            The `<` and `<=` operators can be used to check whether a path is a (strict) sub-path of another path, starting at the same root:

            >>> _ = IPLDObjPath()
            >>> p = _/0/'red'
            >>> q = p/1/2
            >>> p == q
            False
            >>> p <= q
            True
            >>> p < q
            True

        """
        if isinstance(other, IPLDObjPath):
            return len(self) <= len(other) and all(a == b for a, b in zip(self, other))
        return NotImplemented

    def __lt__(self, other: IPLDObjPath) -> bool:
        r""" See :meth:`IPLDObjPath.__le__`. """
        if isinstance(other, IPLDObjPath):
            return len(self) < len(other) and all(a == b for a, b in zip(self, other))
        return NotImplemented

    def __repr__(self) -> str:
        r"""
            .. code-block:: python

                return "/"+"/".join(repr(seg) for seg in self)
        """
        return "/"+"/".join(repr(seg) for seg in self)

    def __rshift__(self, value: IPLDKind) -> IPLDKind:
        r"""
            Accesses the sub-value at this path in the given IPLD value:

            >>> _ = IPLDObjPath()
            >>> _ >> [0, False, {"a": b"hello", "b": "bye"}]
            [0, False, {'a': b'hello', 'b': 'bye'}]
            >>> _/2 >> [0, False, {"a": b"hello", "b": "bye"}]
            {'a': b'hello', 'b': 'bye'}
            >>> _/2/'b' >> [0, False, {"a": b"hello", "b": "bye"}]
            'bye'

            :raises ValueError: if attempting to access a sub-value in a value of :obj:`IPLDScalarKind`
            :raises ValueError: if attempting to access a sub-value indexed by a :obj:`str` segment in a value of list :obj:`IPLDKind` (a Python :obj:`List`)
            :raises ValueError: if attempting to access a sub-value keyed by a :obj:`int` segment in a value of map :obj:`IPLDKind` (a Python :obj:`Dict`)
            :raises IndexError: if attempting to access a sub-value in a value of list kind, where the :obj:`int` segment is not a valid index for the list
            :raises KeyError: if attempting to access a sub-value in a value of map kind, where the :obj:`str` segment is not a valid key for the map
            :raises TypeError: if any of the sub-values along the path is not of IPLD :obj:`IPLDKind` at the top level
        """
        return _access(self, value)


_scalar_kinds = (type(None), bool, int, float, str, bytes, CID)
_recursive_kinds = (list, dict)

def _access(path: IPLDObjPath, value: IPLDKind, idx: int = 0) -> IPLDKind:
    r"""
        Implementation for :func:`IPLDObjPath.access` and :func:`IPLDObjPath.__rshift__`.
    """
    if isinstance(value, _scalar_kinds):
        if len(path) > idx:
            err = f"Error trying to access value at {path[:idx+1]}: value at {path[:idx]} is of scalar kind."
            raise ValueError(err)
        return value
    if isinstance(value, list):
        if idx >= len(path):
            return value
        key = path[idx]
        if not isinstance(key, int):
            err = f"Error trying to access value at {path[:idx+1]}: value at {path[:idx]} is of list kind, but segment {repr(path[idx])} is not integer."
            raise ValueError(err)
        if key not in range(len(value)):
            err = f"Error trying to access value at {path[:idx+1]}: segment {repr(path[idx])} is not a valid index for list at {path[:idx]}."
            raise IndexError(err)
        return _access(path, value[key], idx + 1)
    if isinstance(value, dict):
        if idx >= len(path):
            return value
        key = path[idx]
        if not isinstance(key, str):
            err = f"Error trying to access value at {path[:idx+1]}: value at {path[:idx]} is of map kind, but segment {repr(path[idx])} is not a string."
            raise ValueError(err)
        if key not in value:
            err = f"Error trying to access value at {path[:idx+1]}: segment {repr(path[idx])} is not a valid key for map at {path[:idx]}."
            raise KeyError(err)
        return _access(path, value[key], idx + 1)
    err = f"Error trying to access value at {path[:idx+1]}: value at {path[:idx]} is not of IPLD kind (found type {type(value)})."
    raise TypeError(err)
