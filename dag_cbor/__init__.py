"""
    Python implementation of the [DAG-CBOR codec specification](https://ipld.io/specs/codecs/dag-cbor/spec/).

    This is a CBOR codec (e.g. see [cbor2](https://github.com/agronholm/cbor2)) which enforces additional
    restrictions and conventions, both in encoding and in decoding:

    - The only tag (major type 6) allowed is the CID tag 42, to be encoded as a two bytes head `0xD82A`
      (`0xD8 == 0b110_11000` means "major type 6 (`0b110 == 6`) with 1 byte of argument (`0b11000 = 24`)",
      while `0x2A` is the number 42).
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
"""

from .encoding import encode
from .decoding import decode
