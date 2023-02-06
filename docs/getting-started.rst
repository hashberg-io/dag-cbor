Getting Started
===============

This is a fully compliant Python implementation of the `DAG-CBOR codec <https://ipld.io/specs/codecs/dag-cbor/spec/>`_, a subset of the `Concise Binary Object Representation (CBOR) <https://cbor.io/>`_ supporting the `IPLD Data Model <https://ipld.io/docs/data-model/>`_ and enforcing a unique (strict) encoded representation of items.


Installation
------------

You can install the latest release from `PyPI <https://pypi.org/project/dag-cbor/>`_ as follows:

.. code-block:: console

    $ pip install --upgrade dag-cbor

GitHub repo: https://github.com/hashberg-io/dag-cbor


Basic Usage
-----------

The core functionality of the library is performed by the :func:`~dag_cbor.encoding.encode` and :func:`~dag_cbor.decoding.decode` functions:

>>> import dag_cbor
>>> dag_cbor.encode({'a': 12, 'b': 'hello!'})
b'\xa2aa\x0cabfhello!'
>>> dag_cbor.decode(b'\xa2aa\x0cabfhello!')
{'a': 12, 'b': 'hello!'}

The :mod:`~dag_cbor.ipld` module contains utility types and functions pertaining to the `IPLD Data Model <https://ipld.io/docs/data-model/>`_.
The :mod:`~dag_cbor.random` module contains functions to generate random data compatible with DAG-CBOR encoding.


The DAG-CBOR codec
------------------

The `DAG-CBOR codec <https://ipld.io/specs/codecs/dag-cbor/spec/>`_ is a restriction of the `CBOR codec <https://cbor.io/>`_, enforcing additional conventions:

- The only tag (major type 6) allowed is the CID tag 42, to be encoded as a two bytes head ``0xd82a``
  (``0xd8`` is ``0b110_11000``, which means "major type 6 (``0b110``, i.e. 6) with 1 byte of argument (``0b11000``, i.e. 24)",
  while `0x2a` is the number 42).
- Integers (major types 0 and 1) must be encoded using the minimum possible number of bytes.
- Lengths for major types 2, 3, 4 and 5 must be encoded in the data item head using the minimum possible number of bytes.
- Map keys must be strings (major type 3) and must be unique.
- Map keys must be sorted ascendingly, first by increasing length and then by lexicographic ordering of their utf-8 encoded bytes (cf. `strictness <https://ipld.io/specs/codecs/dag-cbor/spec/#strictness>`_).
- Indefinite-length items (bytes, strings, lists or maps) are not allowed.
- The "break" token is not allowed.
- The only major type 7 items allowed are 64-bit floats (minor 27) and the simple values `true` (minor 20),
  `false` (minor 21) and `null` (minor 22).
- The special float values ``NaN``, ``Infinity`` and ``-Infinity`` are not allowed.
- Encoding and decoding is only allowed on a single top-level item: back-to-back concatenated items at the top level
  are not allowed.

Because the CBOR codec can encode/decode all data handled by the DAG-CBOR codec, we use an established CBOR implementation as the reference when testing, namely the `cbor2 <https://github.com/agronholm/cbor2>`_ package (with the exception of CID data, which is not natively handled by cbor2).


Multiformats Config
-------------------

Please note that :mod:`dag_cbor` internally imports `multiformats <https://github.com/hashberg-io/multiformats>`_: if you'd like to initialise multiformats
with a custom selection of multicodecs/multihashes, you should call ``multiformats_config.enable()`` **before** you import :mod:`dag_cbor` (see the `multiformats docs <https://multiformats.readthedocs.io/en/latest/getting-started.html>`_ for further details):

.. code-block:: python

    import multiformats_config
    multiformats_config.enable(codecs=["sha1", 0x29], bases=["base64url", "9"])
    import dag_cbor # internally imports multiformats
