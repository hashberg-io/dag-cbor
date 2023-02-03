"""
    Error classes and utility functions.

    Errors raised because of CBOR codec specifications are instances of :class:`CBORError`, while errors
    raised because of additional restrictions imposed by the DAG-CBOR codec are instances of :class:`DAGCBORError`,
    a subclass of :class:`CBORError`. Both kind of errors are then further specialised into encoding and decoding errors,
    depending on where they are raised.

    There are two utility functions dealing with dictionary keys:

    - :func:`check_key_compliance` enforces that dictionary keys myst be :obj:`str` instances and unique
    - :func:`canonical_order_dict` applies the above and then sorts the dictionary keys by the lexicographic ordering
      of the corresponding UTF-8 bytestrings (according to DAG-CBOR specification)
"""

from typing import Any, Dict
from typing_validation import validate

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

def _canonical_order_dict(value: Dict[str, Any]) -> Dict[str, Any]:
    utf8key_key_val_pairs = [(k.encode("utf-8", errors="strict"), k, v) for k, v in value.items()]
    sorted_utf8key_key_val_pairs = sorted(utf8key_key_val_pairs, key=lambda i: (len(i[0]), i[0]))
    return {k: v for _, k, v in sorted_utf8key_key_val_pairs}


def _check_key_compliance(value: Dict[str, Any]) -> None:
    """ Check keys for DAG-CBOR compliance. """
    if not all(isinstance(k, str) for k in value.keys()):
        raise DAGCBOREncodingError("Keys for maps must be strings.")


def check_key_compliance(value: Dict[str, Any]) -> None:
    """ Check keys for DAG-CBOR compliance. """
    validate(value, Dict[str, Any])
    _check_key_compliance(value)

def canonical_order_dict(value: Dict[str, Any]) -> Dict[str, Any]:
    """
        Returns a dictionary with canonically ordered keys, according to the DAG-CBOR specification.
        Specifically, keys are sorted increasingly by the lexicographic ordering of the corresponding
        UTF-8 bytestrings.
    """
    validate(value, Dict[str, Any])
    _check_key_compliance(value)
    # sort keys canonically
    return _canonical_order_dict(value)
