"""
    Encodes random items with `dag_cbor.encoding.encode`, then decodes with `dag_cbor.decoding.decode` and checks that the original data is recovered.
"""
# pylint: disable = global-statement

import cbor2.decoder as cbor2 # type: ignore

from dag_cbor import encode, decode
from dag_cbor.random import rand_list, rand_dict, rand_int, rand_bytes, rand_str, rand_bool_none, rand_float, rand_cid, rand_options

nsamples = 1000

def test_int():
    """
        Encodes random `int` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    test_data = rand_int(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        encoded_data = encode(x)
        assert decode(encoded_data) == cbor2.loads(encoded_data), error_msg

def test_bytes():
    """
        Encodes random `bytes` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    test_data = rand_bytes(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        encoded_data = encode(x)
        assert decode(encoded_data) == cbor2.loads(encoded_data), error_msg

def test_str():
    """
        Encodes random `str` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    test_data = rand_str(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        encoded_data = encode(x)
        assert decode(encoded_data) == cbor2.loads(encoded_data), error_msg

def test_bool_none():
    """
        Encodes random `Optional[bool]` or samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    test_data = rand_bool_none(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        encoded_data = encode(x)
        assert decode(encoded_data) == cbor2.loads(encoded_data), error_msg

def test_float():
    """
        Encodes random `float` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    test_data = rand_float(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        encoded_data = encode(x)
        assert decode(encoded_data) == cbor2.loads(encoded_data), error_msg

def test_list():
    """
        Encodes random `list` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    with rand_options(include_cid=False):
        test_data = rand_list(nsamples)
        for i, x in enumerate(test_data):
            error_msg = f"failed at #{i} = {repr(x)}"
            encoded_data = encode(x)
            assert decode(encoded_data) == cbor2.loads(encoded_data), error_msg

def test_dict():
    """
        Encodes random `dict` samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    with rand_options(include_cid=False):
        test_data = rand_dict(nsamples)
        for i, x in enumerate(test_data):
            error_msg = f"failed at #{i} = {repr(x)}"
            encoded_data = encode(x)
            assert decode(encoded_data) == cbor2.loads(encoded_data), error_msg

def test_cid():
    """
        Encodes random CID samples with `dag_cbor.encoding.encode`,
        encodes them with `cbor2.encoder.dumps` and checks that the two encodings match.
    """
    global nsamples
    test_data = rand_cid(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        encoded_data = encode(x)
        assert cbor2.CBORTag(42, decode(encoded_data).buffer) == cbor2.loads(encoded_data), error_msg
