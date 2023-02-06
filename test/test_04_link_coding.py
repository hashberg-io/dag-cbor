"""
    Tests on the specifics of DAG-CBOR Link encoding.
"""

# pylint: disable = global-statement

import cbor2

from dag_cbor import encode, decode
from dag_cbor.decoding.err import DAGCBORDecodingError
from dag_cbor.random import rand_cid, options

import pytest

nsamples = 1000

def test_decoding_requires_multibase_prefix() -> None:
    """
        Checks that the decoder fails if the identity multibase prefix (0x00) is not
        present in the DAG-CBOR representation.
    """
    test_data = rand_cid(nsamples)
    for i, x in enumerate(test_data):
        with pytest.raises(DAGCBORDecodingError):
            decode(cbor2.dumps(cbor2.CBORTag(42, bytes(x))))

def test_encoding_produces_multibase_prefix() -> None:
    """
        Checks that the encoder includes the identity multibase prefix (0x00) in the
        DAG-CBOR representation.
    """
    test_data = rand_cid(nsamples)
    for i, x in enumerate(test_data):
        rtdata = cbor2.loads(encode(x))
        assert rtdata.value[0] == 0
