r"""
    Errors for the :mod:`dag_cbor.decoding` submodule.
"""

from ..encoding.err import CBORError, DAGCBORError

class CBORDecodingError(CBORError):
    """
        Class for decoding errors due to the CBOR specification.
    """
    ...

class DAGCBORDecodingError(CBORDecodingError, DAGCBORError):
    """
        Class for decoding errors due to the DAG-CBOR specification.
    """
    ...
