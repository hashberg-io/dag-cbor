r"""
    Errors for the :mod:`dag_cbor.encoding` submodule.
"""

class CBORError(Exception):
    """
        Parent class for all errors due to the CBOR specification.
    """
    ...

class DAGCBORError(CBORError):
    """
        Parent class for all errors due to the DAG-CBOR specification.
    """
    ...

class CBOREncodingError(CBORError):
    """
        Class for encoding errors due to the CBOR specification.
    """
    ...

class DAGCBOREncodingError(CBOREncodingError, DAGCBORError):
    """
        Class for encoding errors due to the DAG-CBOR specification.
    """
    ...
