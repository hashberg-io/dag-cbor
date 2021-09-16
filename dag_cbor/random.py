"""
    Generation of random data valid for DAG-CBOR encoding.
"""
# pylint: disable = global-statement


from contextlib import contextmanager
from hashlib import sha3_512
import math
from random import Random
import sys
from types import MappingProxyType
from typing import Any, Dict, Iterator, List, Optional

import cid # type: ignore
import multihash # type: ignore

from .utils import _canonical_order_dict

_default_options: Dict[str, Any] = {
    "min_int": -18446744073709551616,
    "max_int": 18446744073709551615,
    "min_bytes": 0,
    "max_bytes": 16,
    "min_chars": 0,
    "max_chars": 16,
    "min_codepoint": 0x00,
    "max_codepoint": 0x10FFFF,
    "min_len": 0,
    "max_len": 8,
    "max_nesting": 2,
    "canonical": True,
    "min_float": -sys.float_info.max,
    "max_float": sys.float_info.max,
    "include_cid": True,
}

_options = _default_options
_rand = Random(0)

def reset_rand_options():
    """
        Resets random generation options to their default values.
    """
    global _options
    global _default_options
    global _rand
    _options = _default_options
    _rand = Random(0)

def get_options():
    """ Get a readonly view of the random generation options. """
    # pylint: disable = global-statement
    global _options
    return MappingProxyType(_options)

@contextmanager
def rand_options(*,
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
                 include_cid: Optional[bool] = None,):
    """ Returns with-statement context for temporary option setting. """
    # pylint: disable = too-many-locals
    global _options
    global _rand
    try:
        _old_options = _options
        _old_rand = _rand
        set_rand_options(seed=seed,
                         min_int=min_int, max_int=max_int,
                         min_bytes=min_bytes, max_bytes=max_bytes,
                         min_chars=min_chars, max_chars=max_chars,
                         min_codepoint=min_codepoint, max_codepoint=max_codepoint,
                         min_len=min_len, max_len=max_len,
                         max_nesting=max_nesting, canonical=canonical,
                         min_float=min_float, max_float=max_float,
                         include_cid=include_cid)
        yield
    finally:
        _options = _old_options
        _rand = _old_rand

def set_rand_options(*,
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
                    include_cid: Optional[bool] = None,):
    """ Sets random generation options. """
    # pylint: disable = too-many-branches, too-many-locals, too-many-statements
    global _options
    global _rand
    # set newly passed options
    _new_options: Dict[str, Any] = {}
    if seed is not None:
        _rand = Random(seed)
    if min_int is not None:
        if min_int < _default_options["min_int"]:
            raise ValueError("Value for min_int is not a valid CBOR integer.")
        _new_options["min_int"] = min_int
    if max_int is not None:
        if max_int > _default_options["max_int"]:
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
        if min_codepoint < _default_options["min_codepoint"] or min_codepoint > _default_options["max_codepoint"]:
            raise ValueError("Value for min_codepoint not a valid utf-8 codepoint.")
        _new_options["min_codepoint"] = min_codepoint
    if max_codepoint is not None:
        if max_codepoint < _default_options["min_codepoint"] or max_codepoint > _default_options["max_codepoint"]:
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


def rand_data(n: Optional[int] = None, *, max_nesting: Optional[int] = None):
    """
        Generates a stream of random data data.
        If a number `n` is given, that number of samples is yelded.

        The optional `max_nesting` keyword argument can be used to explicitly set the
        maximum nesting level for containers:

        - the value `None` (default) is replaced with the integer value `get_options()["max_nesting"]`
        - the integer value -1 means no containers will be generated
        - integer values >= 0 mean that containers will be generated, with items generated by `random_data(max_nesting=max_nesting-1)`
        - no other values are valid
    """
    if n is not None and n < 0:
        raise ValueError()
    if max_nesting is None:
        max_nesting = _options["max_nesting"]
    elif max_nesting < -1:
        raise ValueError("Value for max_nesting must be >= -1 (with -1 indicating no containers).")
    include_cid = _options["include_cid"]
    data_generators: List[Iterator] = [
        rand_list(max_nesting=max_nesting) if max_nesting >= 0 else iter([]),
        rand_dict(max_nesting=max_nesting) if max_nesting >= 0 else iter([]),
        rand_int(),
        rand_bytes(),
        rand_str(),
        rand_bool_none(),
        rand_float(),
        rand_cid()
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

def rand_list(n: Optional[int] = None, *, length: Optional[int] = None, max_nesting: Optional[int] = None) -> Iterator[list]:
    """
        Generates a stream of random `list` data.
        If a number `n` is given, that number of samples is yelded.
    """
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
        yield list(rand_data(_length, max_nesting=max_nesting-1))
        i += 1

def rand_dict(n: Optional[int] = None, *, length: Optional[int] = None, max_nesting: Optional[int] = None) -> Iterator[dict]:
    """
        Generates a stream of random `dict` data.
        If a number `n` is given, that number of samples is yelded.
    """
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
    i = 0
    while n is None or i < n:
        _length = length if length is not None else _rand.randint(min_len, max_len)
        raw_dict = dict(zip(rand_str(_length), rand_data(_length, max_nesting=max_nesting-1)))
        if canonical:
            yield _canonical_order_dict(raw_dict)
        else:
            yield raw_dict
        i += 1

def rand_int(n: Optional[int] = None) -> Iterator[int]:
    """
        Generates a stream of random `int` data.
        If a number `n` is given, that number of samples is yelded.
    """
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
        Generates a stream of random `bytes` data.
        If a number `n` is given, that number of samples is yelded.
    """
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
        Generates a stream of random `str` data.
        If a number `n` is given, that number of samples is yelded.
    """
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
        Generates a stream of random `bool` data.
        If a number `n` is given, that number of samples is yelded.
    """
    if n is not None and n < 0:
        raise ValueError()
    i = 0
    while n is None or i < n:
        x = _rand.randint(0, 1)
        yield x == 1
        i += 1

def rand_bool_none(n: Optional[int] = None) -> Iterator[Optional[bool]]:
    """
        Generates a stream of random `Optional[bool]` data.
        If a number `n` is given, that number of samples is yelded.
    """
    if n is not None and n < 0:
        raise ValueError()
    i = 0
    while n is None or i < n:
        x = _rand.randint(0, 2)
        yield None if x == 2 else x == 1
        i += 1

def rand_float(n: Optional[int] = None) -> Iterator[float]:
    """
        Generates a stream of random `int` data.
        If a number `n` is given, that number of samples is yelded.
    """
    if n is not None and n < 0:
        raise ValueError()
    min_float = _options["min_float"]
    max_float = _options["max_float"]
    if min_float >= 0 or max_float <= 0:
        # no overflow in `min_float + (max_float-min_float) * random()`, can use `Random.uniform`
        i = 0
        while n is None or i < n:
            yield _rand.uniform(min_float, max_float)
            i += 1
    else:
        # overflow in `min_float + (max_float-min_float) * random()`, cannot use `Random.uniform`
        i = 0
        while n is None or i < n:
            x = 1/(1+max_float/(-min_float))
            # x is (-min_float)/(max_float-min_float), the probability of sampling a number in (-min_float, 0)
            if _rand.random() < x:
                yield _rand.random()*min_float
            else:
                yield _rand.random()*max_float
            i += 1

def rand_cid(n: Optional[int] = None) -> Iterator[None]:
    """
        Generates a stream of random `CID` data.
        If a number `n` is given, that number of samples is yelded.
    """
    if n is not None and n < 0:
        raise ValueError()
    hashfun = sha3_512
    hashcode = "sha3-512"
    hashlen = 0x40
    cid_version = 1
    cid_codec = "dag-cbor"
    bytes_generator = rand_bytes(length=hashlen)
    i = 0
    while n is None or i < n:
        try:
            payload = next(bytes_generator)
            h = hashfun()
            h.update(payload)
            digest = h.digest()
        except StopIteration as e:
            raise RuntimeError("Random digest stream is infinite, this should not happen.") from e
        yield cid.make_cid(cid_version, cid_codec, multihash.encode(digest, hashcode))
        i += 1
