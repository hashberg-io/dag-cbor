"""
    Utility classes and functions for the `dag_cbor` package.

    Errors raised because of CBOR codec specifications are instances of `CBORError`, while errors
    raised because of additional restrictions imposed by the DAG-CBOR codec are instances of `DAGCBORError`,
    a subclass of `CBORError`. Both kind of errors are then further specialised into encoding and decoding errors,
    depending on where they are raised.

    There are two utility functions dealing with dictionary keys:

    - `check_key_compliance` enforces that dictionary keys myst be `str` instances and unique
    - `canonical_order_dict` applies the above and then sorts the dictionary keys by the lexicographic ordering
      of the corresponding UTF-8 bytestrings (according to DAG-CBOR specification)
"""

class CBORError(Exception):
    """
        Parent class for all errors due to the CBOR specification.
    """
    ...

class CBOREncodingError(CBORError):
    """
        Class for encoding errors due to the CBOR specification.
    """
    ...

class CBORDecodingError(CBORError):
    """
        Class for decoding errors due to the CBOR specification.
    """
    ...

class DAGCBORError(CBORError):
    """
        Parent class for all errors due to the DAG-CBOR specification.
    """
    ...

class DAGCBOREncodingError(CBOREncodingError, DAGCBORError):
    """
        Class for encoding errors due to the DAG-CBOR specification.
    """
    ...

class DAGCBORDecodingError(CBORDecodingError, DAGCBORError):
    """
        Class for decoding errors due to the DAG-CBOR specification.
    """
    ...

def _canonical_order_dict(value: dict) -> dict:
    try:
        utf8key_key_val_pairs = [(k.encode("utf-8", errors="strict"), k, v) for k, v in value.items()]
    except UnicodeError as e:
        raise CBOREncodingError("Strings must be valid utf-8 strings.") from e
    sorted_utf8key_key_val_pairs = sorted(utf8key_key_val_pairs, key=lambda i: i[0])
    return {k: v for _, k, v in sorted_utf8key_key_val_pairs}


def _check_key_compliance(value: dict) -> None:
    """ Check keys for DAG-CBOR compliance. """
    for k in value.keys():
        if not isinstance(k, str):
            raise DAGCBOREncodingError("Keys for maps must be strings.")
    if len(value.keys()) != len(set(value.keys())):
        raise CBOREncodingError("Keys for maps must be unique.")


def check_key_compliance(value: dict) -> None:
    """ Check keys for DAG-CBOR compliance. """
    _check_key_compliance(value)

def canonical_order_dict(value: dict) -> dict:
    """
        Returns a dictionary with canonically ordered keys, according to the DAG-CBOR specification.
        Specifically, keys are sorted increasingly by the lexicographic ordering of the corresponding
        UTF-8 bytestrings.
    """
    _check_key_compliance(value)
    # sort keys canonically
    return _canonical_order_dict(value)
