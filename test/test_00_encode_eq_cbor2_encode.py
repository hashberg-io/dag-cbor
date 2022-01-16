"""
    Tests on encoding data using `dag_cbor` vs encoding data using `cbor2`.
"""
# pylint: disable = global-statement

import cbor2 # type: ignore

from dag_cbor import encode
from dag_cbor.random import rand_list, rand_dict, rand_int, rand_bytes, rand_str, rand_bool_none, rand_float, rand_cid, options

nsamples = 1000

def test_int() -> None:
    """
        Encodes random `int` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_int(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert cbor2.dumps(x) == encode(x), error_msg

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
        assert cbor2.dumps(x) == encode(x), error_msg

def test_bytes() -> None:
    """
        Encodes random `bytes` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_bytes(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert cbor2.dumps(x) == encode(x), error_msg

def test_str() -> None:
    """
        Encodes random `str` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_str(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert cbor2.dumps(x) == encode(x), error_msg

def test_bool_none() -> None:
    """
        Encodes random `Optional[bool]` or samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_bool_none(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert cbor2.dumps(x) == encode(x), error_msg

def test_float() -> None:
    """
        Encodes random `float` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_float(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert cbor2.dumps(x) == encode(x), error_msg

def test_list() -> None:
    """
        Encodes random `list` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    with options(include_cid=False):
        test_data = rand_list(nsamples)
        for i, x in enumerate(test_data):
            error_msg = f"failed at #{i} = {repr(x)}"
            assert cbor2.dumps(x) == encode(x), error_msg

def test_dict() -> None:
    """
        Encodes random `dict` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    with options(include_cid=False):
        test_data = rand_dict(nsamples)
        for i, x in enumerate(test_data):
            error_msg = f"failed at #{i} = {repr(x)}"
            assert cbor2.dumps(x) == encode(x), error_msg


def test_dict_noncanonical() -> None:
    """
        Encodes a dict given in noncanonical order and tests if it is encoded in canonical order.
        from the specs (https://ipld.io/specs/codecs/dag-cbor/spec/#strictness):

        If two keys have different lengths, the shorter one sorts earlier;
        If two keys have the same length, the one with the lower value in (byte-wise) lexical order sorts earlier.
    """
    test_data = {"bar123": 5, "zap": 7, "abc432": 9}
    assert list(cbor2.loads(encode(test_data))) == ["zap", "abc432", "bar123"]


def test_cid() -> None:
    """
        Encodes random CID samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    test_data = rand_cid(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        assert cbor2.dumps(cbor2.CBORTag(42, b"\0" + bytes(x))) == encode(x), error_msg
