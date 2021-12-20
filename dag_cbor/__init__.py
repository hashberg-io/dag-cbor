"""
    Python implementation of the [DAG-CBOR codec](https://ipld.io/specs/codecs/dag-cbor/spec/) specification.

    The core functionality of the library is performed by the `dag_cbor.encoding.encode` and `dag_cbor.decoding.decode` functions:

    ```python
    >>> import dag_cbor
    >>> dag_cbor.encode({'a': 12, 'b': 'hello!'})
    b'\\xa2aa\\x0cabfhello!'
    >>> dag_cbor.decode(b'\\xa2aa\\x0cabfhello!')
    {'a': 12, 'b': 'hello!'}
    ```

    For their documentation, see the `dag_cbor.encoding` and `dag_cbor.decoding` modules.
    The `dag_cbor.random` module contains functions to generate random data compatible with DAG-CBOR encoding.
    The `dag_cbor.utils` module contains errors and utility functions.

    The DAG-CBOR codec is a restriction of [CBOR codec](https://cbor.io/), enforcing additional conventions:

    - The only tag (major type 6) allowed is the CID tag 42, to be encoded as a two bytes head `0xd82a`
      (`0xd8 == 0b110_11000` means "major type 6 (`0b110 == 6`) with 1 byte of argument (`0b11000 = 24`)",
      while `0x2a` is the number 42).
    - Integers (major types 0 and 1) must be encoded using the minimum possible number of bytes.
    - Lengths for major types 2, 3, 4 and 5 must be encoded in the data item head using the minimum possible number of bytes.
    - Map keys must be strings (major type 3) and must be unique.
    - Map keys must be sorted ascendingly according to the lexicographic ordering of their utf-8 encoded bytes (which is
      the standard ordering of `bytes` objects in Python).
    - Indefinite-length items (bytes, strings, lists or maps) are not allowed.
    - The "break" token is not allowed.
    - The only major type 7 items allowed are 64-bit floats (minor 27) and the simple values `true` (minor 20),
      `false` (minor 21) and `null` (minor 22).
    - The special float values `NaN`, `Infinity` and `-Infinity` are not allowed.
    - Encoding and decoding is only allowed on a single top-level item: back-to-back concatenated items at the top level
      are not allowed.

    Because the CBOR codec can encode/decode all data handled by the DAG-CBOR codec, we use an established CBOR implementation
    as the reference when testing, namely the [`cbor2`](https://github.com/agronholm/cbor2) package (with the exception of CID
    data, which is not natively handled by `cbor2`).
"""

__version__ = "0.1.2"

from .encoding import encode as encode
from .decoding import decode as decode
from . import random as random
