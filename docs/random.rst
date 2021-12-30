Random DAG-CBOR Data
====================

The module :mod:`~dag_cbor.random` contains a set of functions to generate random DAG-CBOR data.
The functions are named ``rand_X``, where ``X`` is one of:

- :obj:`int` for uniformly distributed integers
- :obj:`float` for uniformly distributed floats, with fixed decimals
- :obj:`bytes` for byte-strings of uniformly distributed length, with uniformly distributed bytes
- :obj:`str` for strings of uniformly distributed length, with uniformly distributed codepoints (all valid UTF-8 strings, by rejection sampling)
- :obj:`bool` for :obj:`False` or :obj:`True` (50% each)
- ``bool_none`` for :obj:`False`, :obj:`True` or :obj:`None` (33.3% each)
- :obj:`list` for lists of uniformly distributed length, with random elements of any type
- :obj:`dict` for dictionaries of uniformly distributed length, with distinct random string keys and random values of any type
- `cid` for CID data (instance of :obj:`~multiformats.cid.CID` from the `multiformats <https://github.com/hashberg-io/multiformats>`_ library)


Generating random values
------------------------

The function call ``rand_X(n)`` returns an iterator yielding a stream of ``n`` random values of type ``X``, e.g.:

>>> import pprint
>>> import dag_cbor
>>> kwargs = dict(min_codepoint=0x41, max_codepoint=0x5a, include_cid=False)
>>> with dag_cbor.random.options(**kwargs):
...     for d in dag_cbor.random.rand_dict(3):
...             pprint.pp(d)
...
{'BIQPMZ': b'\x85\x1f\x07/\xcc\x00\xfc\xaa',
 'EJEYDTZI': {},
 'PLSG': {'G': 'JFG',
          'HZE': -61.278,
          'JWDRKRGZ': b'-',
          'OCCKQPDJ': True,
          'SJOCTZMK': False},
 'PRDLN': 39.129,
 'TUGRP': None,
 'WZTEJDXC': -69.933}
{'GHAXI': 39.12,
 'PVUWZLC': 4.523,
 'TDPSU': 'TVCADUGT',
 'ZHGVSNSI': [-57, 9, -78.312]}
{'': 11, 'B': True, 'FWD': {}, 'GXZBVAR': 'BTDWMGI', 'TDICHC': 87}

The function call ``rand_X()``, without the positional argument ``n``, instead yields an infinite stream of random values.


Random generation options
-------------------------

The :func:`dag_cbor.random.options` context manager is used to set options temporarily, within the scope of a ``with`` directive.
In the snippet below, we set string characters to be uppercase alphabetic (codepoints `0x41`-`0x5a`) and we excluded CID values from being generated:

.. code-block:: python

    kwargs = dict(min_codepoint=0x41, max_codepoint=0x5a, include_cid=False)
    with dag_cbor.random.options(**kwargs):
        ...

Options can be permanently set with :func:`~dag_cbor.random.set_options` and reset with :func:`~dag_cbor.random.reset_options`.
A read-only view on options can be obtained from :func:`~dag_cbor.random.get_options`, and a read-only view on default options can be obtained from :func:`~dag_cbor.random.default_options`:

>>> import pprint
>>> import dag_cbor
>>> pprint.pp(dag_cbor.random.default_options())
mappingproxy({'min_int': -100,
              'max_int': 100,
              'min_bytes': 0,
              'max_bytes': 8,
              'min_chars': 0,
              'max_chars': 8,
              'min_codepoint': 33,
              'max_codepoint': 126,
              'min_len': 0,
              'max_len': 8,
              'max_nesting': 2,
              'canonical': True,
              'min_float': -100.0,
              'max_float': 100.0,
              'float_decimals': 3,
              'include_cid': True})

See :func:`~dag_cbor.random.set_options` for a description of the individual options.
