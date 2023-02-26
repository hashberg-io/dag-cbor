"""
    Tests on number of bytes written to streams in encoding and read from streams in decoding,
    as well as tests on decoding concatenated data.
"""
# pylint: disable = global-statement

from io import BytesIO
from dag_cbor import encode, decode
from dag_cbor.ipld import IPLDKind
from dag_cbor.random import rand_data

nsamples = 1000
nconcat = 3

class BytesReadCounter:
    """ Counter for bytes read while decoding. """
    _num_bytes_read: int = 0
    def __call__(self, value: IPLDKind, num_bytes_read: int) -> None:
        self._num_bytes_read += num_bytes_read
    def __int__(self) -> int:
        return self._num_bytes_read

def test_decode_concat_length() -> None:
    """
        Encodes random item samples with `dag_cbor.encoding.encode`, then concatenates the bytes of three items.
        Decodes with `dag_cbor.decoding.decode` allowing concatenation and checks that the correct number of bytes
        are read for each encoded item.
    """
    test_data = rand_data(nconcat*nsamples)
    for i in range(nsamples):
        items = [next(test_data) for j in range(nconcat)]
        encoded_items = [encode(x) for x in items]
        stream = BytesIO(b''.join(encoded_items))
        for j in range(nconcat):
            x = items[j]
            bytes_read_cnt = BytesReadCounter()
            decode(stream, allow_concat=True, callback=bytes_read_cnt)
            error_msg = f"failed at #{i}:{j} = {repr(x)}"
            assert len(encoded_items[j]) == int(bytes_read_cnt), error_msg
        error_msg = f"failed at #{i}"
        assert len(stream.read()) == 0, error_msg

def test_encode_length() -> None:
    """
        Encodes random item samples with `dag_cbor.encoding.encode` to a stream,
        then checks that the number of bytes written is the one returned by `encode`.
    """
    test_data = rand_data(nsamples)
    for i, x in enumerate(test_data):
        error_msg = f"failed at #{i} = {repr(x)}"
        stream = BytesIO()
        num_bytes_written: int = encode(x, stream=stream)
        assert len(stream.getvalue()) == num_bytes_written, error_msg
