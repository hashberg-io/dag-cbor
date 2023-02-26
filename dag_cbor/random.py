"""
    Functions to generate random data.
"""
# pylint: disable = global-statement

from __future__ import annotations # See https://peps.python.org/pep-0563/

from contextlib import contextmanager
import math
from random import Random # pylint: disable = import-self
import sys
from types import MappingProxyType
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple
from typing_validation import validate

from multiformats import multicodec, multibase, multihash, CID

from .ipld import IPLDKind
from .encoding import encode, _canonical_order_dict

_min_int = -18446744073709551616
_max_int = 18446744073709551615
_min_float = -sys.float_info.max
_max_float = sys.float_info.max
_min_codepoint = 0x00
_max_codepoint = 0x10FFFF

_default_options: Dict[str, Any] = {
    "min_int": -100,
    "max_int": 100,
    "min_bytes": 0,
    "max_bytes": 8,
    "min_chars": 0,
    "max_chars": 8,
    "min_codepoint": 0x21,
    "max_codepoint": 0x7e,
    "min_len": 0,
    "max_len": 8,
    "max_nesting": 2,
    "canonical": True,
    "min_float": -100.0,
    "max_float": 100.0,
    "float_decimals": 3,
    "include_cid": True,
}

_options = _default_options
_rand = Random(0)

def reset_options() -> None:
    """
        Resets random generation options to their default values.
    """
    global _options
    global _rand
    _options = _default_options
    _rand = Random(0)

def default_options() -> Mapping[str, Any]:
    """
        Readonly view of the default random generation options.
    """
    return MappingProxyType(_default_options)

def get_options() -> Mapping[str, Any]:
    """
        Readonly view of the current random generation options.
    """
    return MappingProxyType(_options)

@contextmanager
def options(*,
            seed: Optional[int] = None,
            min_int: Optional[int] = None,
            max_int: Optional[int] = None,
            min_bytes: Optional[int] = None,
            max_bytes: Optional[int] = None,
            min_chars: Optional[int] = None,
            max_chars: Optional[int] = None,
            min_codepoint: Optional[int] = None,
            max_codepoint: Optional[int] = None,
            min_len: Optional[int] = None,
            max_len: Optional[int] = None,
            max_nesting: Optional[int] = None,
            canonical: Optional[bool] = None,
            min_float: Optional[float] = None,
            max_float: Optional[float] = None,
            float_decimals: Optional[int] = None,
            include_cid: Optional[bool] = None,) -> Iterator[None]:
    """
        Returns with-statement context manager for temporary option setting:

        .. code-block:: python

            with options(**options):
                for value in rand_data(num_samples):
                    ...

        Options available:

        .. code-block::

            seed: int           # set new random number generator, with this seed
            min_int: int        # smallest `int` value
            max_int: int        # largest `int` value
            min_bytes: int      # min length of `bytes` value
            max_bytes: int      # max length of `bytes` value
            min_chars: int      # min length of `str` value
            max_chars: int      # max length of `str` value
            min_codepoint: int  # min utf-8 codepoint in `str` value
            max_codepoint: int  # max utf-8 codepoint in `str` value
            min_len: int        # min length of `list` and `dict` values
            max_len: int        # max length of `list` and `dict` values
            max_nesting: int    # max nesting of collections
            canonical: bool     # whether `dict` values have canonically ordered keys
            min_float: float    # smallest `float` value
            max_float: float    # largest `float` value
            float_decimals: int # number of decimals to keep in floats
            include_cid: bool   # whether to generate CID values
    """
    # pylint: disable = too-many-locals
    global _options
    global _rand
    _old_options = _options
    _old_rand = _rand
    try:
        set_options(seed=seed,
                    min_int=min_int, max_int=max_int,
                    min_bytes=min_bytes, max_bytes=max_bytes,
                    min_chars=min_chars, max_chars=max_chars,
                    min_codepoint=min_codepoint, max_codepoint=max_codepoint,
                    min_len=min_len, max_len=max_len,
                    max_nesting=max_nesting, canonical=canonical,
                    min_float=min_float, max_float=max_float,
                    float_decimals=float_decimals, include_cid=include_cid)
        yield
    finally:
        _options = _old_options
        _rand = _old_rand

def set_options(*,
                seed: Optional[int] = None,
                min_int: Optional[int] = None,
                max_int: Optional[int] = None,
                min_bytes: Optional[int] = None,
                max_bytes: Optional[int] = None,
                min_chars: Optional[int] = None,
                max_chars: Optional[int] = None,
                min_codepoint: Optional[int] = None,
                max_codepoint: Optional[int] = None,
                min_len: Optional[int] = None,
                max_len: Optional[int] = None,
                max_nesting: Optional[int] = None,
                canonical: Optional[bool] = None,
                min_float: Optional[float] = None,
                max_float: Optional[float] = None,
                float_decimals: Optional[int] = None,
                include_cid: Optional[bool] = None,) -> None:
    """
        Permanently sets random generation options. See :func:`options` for the available options.

    """
    # pylint: disable = too-many-branches, too-many-locals, too-many-statements
    for iarg in (seed, min_int, max_int, min_bytes, max_bytes, min_chars, max_chars,
                 min_codepoint, max_codepoint, min_len, max_len, max_nesting, float_decimals):
        validate(iarg, Optional[int])
    for barg in (canonical, include_cid):
        validate(barg, Optional[bool])
    for farg in (min_float, max_float):
        validate(farg, Optional[float])
    global _options
    global _rand
    # set newly passed options
    _new_options: Dict[str, Any] = {}
    if seed is not None:
        _rand = Random(seed)
    if min_int is not None:
        if min_int < _min_int:
            raise ValueError("Value for min_int is not a valid CBOR integer.")
        _new_options["min_int"] = min_int
    if max_int is not None:
        if max_int > _max_int:
            raise ValueError("Value for max_int is not a valid CBOR integer.")
        _new_options["max_int"] = max_int
    if min_bytes is not None:
        if min_bytes < 0:
            raise ValueError("Value for min_bytes is negative.")
        _new_options["min_bytes"] = min_bytes
    if max_bytes is not None:
        if max_bytes < 0:
            raise ValueError("Value for max_bytes is negative.")
        _new_options["max_bytes"] = max_bytes
    if min_chars is not None:
        if min_chars < 0:
            raise ValueError("Value for min_chars is negative.")
        _new_options["min_chars"] = min_chars
    if max_chars is not None:
        if max_chars < 0:
            raise ValueError("Value for max_chars is negative.")
        _new_options["max_chars"] = max_chars
    if min_codepoint is not None:
        if min_codepoint < _min_codepoint or min_codepoint > _max_codepoint:
            raise ValueError("Value for min_codepoint not a valid utf-8 codepoint.")
        _new_options["min_codepoint"] = min_codepoint
    if max_codepoint is not None:
        if max_codepoint < _min_codepoint or max_codepoint > _max_codepoint:
            raise ValueError("Value for max_codepoint not a valid utf-8 codepoint.")
        _new_options["max_codepoint"] = max_codepoint
    if min_len is not None:
        if min_len < 0:
            raise ValueError("Value for min_len is negative.")
        _new_options["min_len"] = min_len
    if max_len is not None:
        if max_len < 0:
            raise ValueError("Value for max_len is negative.")
        _new_options["max_len"] = max_len
    if max_nesting is not None:
        if max_nesting < 0:
            raise ValueError("Value for max_nesting is negative.")
        _new_options["max_nesting"] = max_nesting
    if canonical is not None:
        _new_options["canonical"] = canonical
    if min_float is not None:
        if math.isnan(min_float) or math.isinf(min_float):
            raise ValueError("Value for min_float is not a valid CBOR float.")
        _new_options["min_float"] = min_float
    if max_float is not None:
        if math.isnan(max_float) or math.isinf(max_float):
            raise ValueError("Value for max_float is not a valid CBOR float.")
        _new_options["max_float"] = max_float
    if float_decimals is not None:
        if float_decimals < 0:
            raise ValueError("Value for float_decimals is negative.")
        _new_options["float_decimals"] = float_decimals
    if include_cid is not None:
        _new_options["include_cid"] = include_cid
    # pass-through other options with former values
    for k, v in _options.items():
        if k not in _new_options:
            _new_options[k] = v
    # check compatibility conditions
    if _new_options["min_bytes"] > _new_options["max_bytes"]:
        raise ValueError("Value for min_bytes is larger than value for max_bytes.")
    if _new_options["min_chars"] > _new_options["max_chars"]:
        raise ValueError("Value for min_chars is larger than value for max_chars.")
    if _new_options["min_codepoint"] > _new_options["max_codepoint"]:
        raise ValueError("Value for min_codepoint is larger than value for max_codepoint.")
    if _new_options["min_len"] > _new_options["max_len"]:
        raise ValueError("Value for min_len is larger than value for max_len.")
    # update options
    _options = _new_options


def rand_data(n: Optional[int] = None, *, max_nesting: Optional[int] = None) -> Iterator[IPLDKind]:
    r"""
        Generates a stream of random data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
        :param max_nesting: the maximum nesting level for containers; if :obj:`None`, value from :func:`get_options` is used

        Maximum nesting level for containers:

        - the integer value -1 means no containers will be generated
        - integer values >= 0 mean that containers will be generated, with items generated by ``random_data(max_nesting=max_nesting-1)``
        - no other values are valid

    """
    validate(n, Optional[int])
    validate(max_nesting, Optional[int])
    return _rand_data(n, max_nesting=max_nesting)

def _rand_data(n: Optional[int] = None, *, max_nesting: Optional[int] = None) -> Iterator[IPLDKind]:
    if n is not None and n < 0:
        raise ValueError()
    if max_nesting is None:
        max_nesting = _options["max_nesting"]
    elif max_nesting < -1:
        raise ValueError("Value for max_nesting must be >= -1 (with -1 indicating no containers).")
    include_cid = _options["include_cid"]
    data_generators: List[Iterator[Any]] = [
        _rand_list(max_nesting=max_nesting) if max_nesting >= 0 else iter([]),
        _rand_dict(max_nesting=max_nesting) if max_nesting >= 0 else iter([]),
        _rand_int(),
        _rand_bytes(),
        _rand_str(),
        _rand_bool_none(),
        _rand_float(),
        _rand_cid()
    ]
    num_data_generators = len(data_generators) if include_cid else len(data_generators)-1
    i = 0
    while n is None or i < n:
        if max_nesting == -1:
            # exclude containers
            datatype = _rand.randrange(0x2, num_data_generators)
        else:
            # include containers
            datatype = _rand.randrange(0x0, num_data_generators)
        try:
            yield next(data_generators[datatype])
        except StopIteration as e:
            raise RuntimeError("All random streams are infinite, this should not happen.") from e
        i += 1

def rand_list(n: Optional[int] = None, *, length: Optional[int] = None, max_nesting: Optional[int] = None) -> Iterator[List[Any]]:
    """
        Generates a stream of random :obj:`list` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
        :param length: size for the lists; if :obj:`None`, a random value is sampled according to the :func:`options`
        :param max_nesting: the maximum nesting level for containers; if :obj:`None`, value from :func:`get_options` is used
    """
    validate(n, Optional[int])
    validate(length, Optional[int])
    validate(max_nesting, Optional[int])
    return _rand_list(n, length=length, max_nesting=max_nesting)

def _rand_list(n: Optional[int] = None, *, length: Optional[int] = None, max_nesting: Optional[int] = None) -> Iterator[List[Any]]:
    if n is not None and n < 0:
        raise ValueError()
    if length is not None and length < 0:
        raise ValueError()
    if max_nesting is None:
        max_nesting = _options["max_nesting"]
    elif max_nesting < 0:
        raise ValueError("Value for max_nesting is negative.")
    min_len = _options["min_len"]
    max_len = _options["max_len"]
    i = 0
    while n is None or i < n:
        _length = length if length is not None else _rand.randint(min_len, max_len)
        yield list(_rand_data(_length, max_nesting=max_nesting-1))
        i += 1

def rand_dict(n: Optional[int] = None, *, length: Optional[int] = None, max_nesting: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
        Generates a stream of random :obj:`dict` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
        :param length: size for the dicts; if :obj:`None`, a random value is sampled according to the :func:`options`
        :param max_nesting: the maximum nesting level for containers; if :obj:`None`, value from :func:`get_options` is used
    """
    validate(n, Optional[int])
    validate(length, Optional[int])
    validate(max_nesting, Optional[int])
    return _rand_dict(n, length=length, max_nesting=max_nesting)

def _rand_dict(n: Optional[int] = None, *, length: Optional[int] = None, max_nesting: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    # pylint: disable = too-many-locals, too-many-branches
    if n is not None and n < 0:
        raise ValueError()
    if length is not None and length < 0:
        raise ValueError()
    if max_nesting is None:
        max_nesting = _options["max_nesting"]
    elif max_nesting < 0:
        raise ValueError("Value for max_nesting is negative.")
    min_len = _options["min_len"]
    max_len = _options["max_len"]
    canonical = _options["canonical"]
    min_chars = _options["min_chars"]
    max_chars = _options["max_chars"]
    max_codepoint = _options["max_codepoint"]
    num_codepoints = max_codepoint-_options["min_codepoint"]
    i = 0
    while n is None or i < n:
        _length = length if length is not None else _rand.randint(min_len, max_len)
        # check whether we have enough distinct strings to generate a random dictionary of desired length
        if num_codepoints == 1:
            num_strings = max_chars-min_chars+1
        else:
            num_strings = (num_codepoints**min_chars)*(num_codepoints**(max_chars-min_chars+1)-1)//(num_codepoints-1)
        if num_strings < _length:
            raise ValueError(f"Not enough distinct strings available to make a dictionary of length {_length}")
        # generate distinct dictionary keys
        if num_codepoints == 1:
            key_lengths = _rand.sample(range(min_chars, max_chars+1), _length)
            keys = [chr(max_codepoint)*l for l in key_lengths]
        else:
            keys = []
            keys_set = set()
            str_generator = _rand_str()
            while len(keys) < _length:
                try:
                    s = next(str_generator)
                except StopIteration as e:
                    raise RuntimeError("Random string stream is infinite, this should not happen.") from e
                if s not in keys_set:
                    keys.append(s)
                    keys_set.add(s)
        # generate dictionary
        raw_dict = dict(zip(keys, _rand_data(_length, max_nesting=max_nesting-1)))
        if canonical:
            yield _canonical_order_dict(raw_dict)
        else:
            yield raw_dict
        i += 1

def rand_int(n: Optional[int] = None) -> Iterator[int]:
    """
        Generates a stream of random :obj:`int` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
    """
    validate(n, Optional[int])
    return _rand_int(n)

def _rand_int(n: Optional[int] = None) -> Iterator[int]:
    if n is not None and n < 0:
        raise ValueError()
    min_int = _options["min_int"]
    max_int = _options["max_int"]
    i = 0
    while n is None or i < n:
        yield _rand.randint(min_int, max_int)
        i += 1

def rand_bytes(n: Optional[int] = None, *, length: Optional[int] = None) -> Iterator[bytes]:
    """
        Generates a stream of random :obj:`bytes` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
        :param length: length of the bytestrings; if :obj:`None`, a random value is sampled according to the :func:`options`
    """
    validate(n, Optional[int])
    validate(length, Optional[int])
    return _rand_bytes(n, length=length)

def _rand_bytes(n: Optional[int] = None, *, length: Optional[int] = None) -> Iterator[bytes]:
    if n is not None and n < 0:
        raise ValueError()
    if length is not None and length < 0:
        raise ValueError()
    min_bytes = _options["min_bytes"]
    max_bytes = _options["max_bytes"]
    i = 0
    while n is None or i < n:
        _length = length if length is not None else _rand.randint(min_bytes, max_bytes)
        yield bytes([_rand.randint(0, 255) for _ in range(_length)])
        i += 1

def rand_str(n: Optional[int] = None, *, length: Optional[int] = None) -> Iterator[str]:
    """
        Generates a stream of random :obj:`str` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
        :param length: length of the strings; if :obj:`None`, a random value is sampled according to the :func:`options`
    """
    validate(n, Optional[int])
    validate(length, Optional[int])
    return _rand_str(n, length=length)

def _rand_str(n: Optional[int] = None, *, length: Optional[int] = None) -> Iterator[str]:
    if n is not None and n < 0:
        raise ValueError()
    if length is not None and length < 0:
        raise ValueError()
    min_chars = _options["min_chars"]
    max_chars = _options["max_chars"]
    min_codepoint = _options["min_codepoint"]
    max_codepoint = _options["max_codepoint"]
    i = 0
    while n is None or i < n:
        _length = length if length is not None else _rand.randint(min_chars, max_chars)
        codepoints = [_rand.randint(min_codepoint, max_codepoint) for _ in range(_length)]
        try:
            string = "".join(chr(c) for c in codepoints)
            string.encode("utf-8", errors="strict")
            yield string
            i += 1
        except UnicodeError:
            continue

def rand_bool(n: Optional[int] = None) -> Iterator[bool]:
    """
        Generates a stream of random :obj:`bool` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
    """
    validate(n, Optional[int])
    return _rand_bool(n)

def _rand_bool(n: Optional[int] = None) -> Iterator[bool]:
    if n is not None and n < 0:
        raise ValueError()
    i = 0
    while n is None or i < n:
        x = _rand.randint(0, 1)
        yield x == 1
        i += 1

def rand_bool_none(n: Optional[int] = None) -> Iterator[Optional[bool]]:
    """
        Generates a stream of random :obj:`bool` or :obj:`None` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
    """
    validate(n, Optional[int])
    return _rand_bool_none(n)

def _rand_bool_none(n: Optional[int] = None) -> Iterator[Optional[bool]]:
    if n is not None and n < 0:
        raise ValueError()
    i = 0
    while n is None or i < n:
        x = _rand.randint(0, 2)
        yield None if x == 2 else x == 1
        i += 1

def rand_float(n: Optional[int] = None) -> Iterator[float]:
    """
        Generates a stream of random :obj:`float` data.

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
    """
    validate(n, Optional[int])
    return _rand_float(n)

def _rand_float(n: Optional[int] = None) -> Iterator[float]:
    if n is not None and n < 0:
        raise ValueError()
    min_float = _options["min_float"]
    max_float = _options["max_float"]
    float_decimals = _options["float_decimals"]
    eps = 10.0**-float_decimals
    if min_float >= 0 or max_float <= 0:
        # no overflow in `min_float + (max_float-min_float) * random()`, can use `Random.uniform`
        i = 0
        while n is None or i < n:
            x = _rand.uniform(min_float, max_float)
            yield x-x%eps
            i += 1
    else:
        # overflow in `min_float + (max_float-min_float) * random()`, cannot use `Random.uniform`
        i = 0
        while n is None or i < n:
            x = 1/(1+max_float/(-min_float))
            # x is (-min_float)/(max_float-min_float), the probability of sampling a number in (-min_float, 0)
            if _rand.random() < x:
                x = _rand.random()*min_float
            else:
                x = _rand.random()*max_float
            yield x-x%eps
            i += 1

_cid_multibase = multibase.get("base58btc") # the default base for binary CIDs
_cid_version = 1
_cid_multicodec = multicodec.get("dag-cbor")
_cid_multihash = multihash.get("sha3-512")

def rand_data_cid(n: Optional[int] = None, *, max_nesting: Optional[int] = None) -> Iterator[Tuple[IPLDKind, CID]]:
    r"""
        Generates a stream of random DAG-CBOR data and associated CIDs:

        - multibase 'base32'
        - CIDv1
        - multicodec 'dag-cbor'
        - multihash 'sha3-512', with full 512-bit digest

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
        :param max_nesting: the maximum nesting level for containers; if :obj:`None`, value from :func:`get_options` is used

    """
    validate(n, Optional[int])
    return _rand_data_cid(n, max_nesting=max_nesting)

def rand_cid(n: Optional[int] = None, *, max_nesting: Optional[int] = None) -> Iterator[CID]:
    """
        Generates a stream of random CIDs:

        - multibase 'base32'
        - CIDv1
        - multicodec 'dag-cbor'
        - multihash 'sha3-512', with full 512-bit digest

        :param n: the number of samples to be yielded; if :obj:`None`, an infinite stream is yielded
        :param max_nesting: the maximum nesting level for containers; if :obj:`None`, value from :func:`get_options` is used
    """
    validate(n, Optional[int])
    return _rand_cid(n, max_nesting=max_nesting)

def _rand_cid(n: Optional[int] = None, *, max_nesting: Optional[int] = None) -> Iterator[CID]:
    return (cid for _, cid in _rand_data_cid(n, max_nesting=max_nesting))

def _rand_data_cid(n: Optional[int] = None, *, max_nesting: Optional[int] = None) -> Iterator[Tuple[IPLDKind, CID]]:
    if n is not None and n < 0:
        raise ValueError()
    if max_nesting is None:
        max_nesting = _options["max_nesting"]
    elif max_nesting < 0:
        raise ValueError("Value for max_nesting is negative.")
    i = 0
    rand_data_generator = _rand_data(max_nesting=max_nesting-1)
    while n is None or i < n:
        try:
            dag_cbor_data = next(rand_data_generator)
            binary_data = encode(dag_cbor_data)
        except StopIteration as e:
            raise RuntimeError("Random digest stream is infinite, this should not happen.") from e
        yield (dag_cbor_data, CID(_cid_multibase, _cid_version, _cid_multicodec, _cid_multihash.digest(binary_data)))
        i += 1
