"""
    Tests on encoding data using `dag_cbor` and decoding back using `cbor2`.
"""
# pylint: disable = global-statement

from dag_cbor import encode, decode
from dag_cbor.random import rand_list, rand_dict, rand_int, rand_bytes, rand_str, rand_bool_none, rand_float, rand_cid, options

import pytest

nsamples = 1000

def test_int() -> None:
    """
        Encodes random `int` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_int(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

def test_special_int() -> None:
    """
        Encodes specially crafted `int` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    exponents = [8, 16, 32, 26]
    special_data = [2**e for e in exponents]
    special_data += [x-1 for x in special_data]
    special_data += [-x for x in special_data]
    for i, x in enumerate(special_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

def test_bytes() -> None:
    """
        Encodes random `bytes` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_bytes(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

def test_str() -> None:
    """
        Encodes random `str` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_str(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

def test_bool_none() -> None:
    """
        Encodes random `Optional[bool]` or samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_bool_none(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

def test_float() -> None:
    """
        Encodes random `float` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_float(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

def test_list() -> None:
    """
        Encodes random `list` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    with options(include_cid=False):
        test_data = rand_list(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

@pytest.mark.parametrize("canonical", [True, False])
def test_dict(canonical: bool) -> None:
    """
        Encodes random `dict` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    with options(include_cid=False, canonical=canonical):
        test_data = rand_dict(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg

def test_cid() -> None:
    """
        Encodes random CID samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_cid(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert x == decode(encode(x)), error_msg
        assert x == decode(encode(x, include_multicodec=True), require_multicodec=True), error_msg
