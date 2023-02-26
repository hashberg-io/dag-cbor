"""
    Python implementation of the `DAG-CBOR codec <https://ipld.io/specs/codecs/dag-cbor/spec/>`_ specification.
"""

from __future__ import annotations # See https://peps.python.org/pep-0563/

__version__ = "0.3.2"

from .ipld import IPLDKind, IPLDScalarKind, IPLDObjPath
from .encoding import encode
from .decoding import decode

# explicit re-exports
__all__ = ["encode", "decode", "IPLDKind", "IPLDScalarKind", "IPLDObjPath"]
