"""
    Python implementation of the `DAG-CBOR codec <https://ipld.io/specs/codecs/dag-cbor/spec/>`_ specification.
"""

__version__ = "0.2.1"

from .encoding import encode
from .decoding import decode

# explicit re-exports
__all__ = [
    "encode",
    "decode"
]
