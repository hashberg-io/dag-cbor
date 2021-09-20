# `py-dag-cbor`: A Python implementation of [DAG-CBOR](https://ipld.io/specs/codecs/dag-cbor/spec/)

[![PyPI status](https://app.travis-ci.com/hashberg-io/py-dag-cbor.svg?token=Aux1v4K7oU16PNQw8VRa&branch=main)](https://app.travis-ci.com/github/hashberg-io/py-dag-cbor/)
[![Generic badge](https://img.shields.io/badge/python-3.7+-green.svg)](https://docs.python.org/3.7/)
[![Checked with Mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](https://github.com/python/mypy)
[![PyPI version shields.io](https://img.shields.io/pypi/v/dag-cbor.svg)](https://pypi.python.org/pypi/dag-cbor/)
[![PyPI status](https://img.shields.io/pypi/status/dag-cbor.svg)](https://pypi.python.org/pypi/dag-cbor/)


This is a fully compliant Python implementation of the [DAG-CBOR codec](https://ipld.io/specs/codecs/dag-cbor/spec/), a subset of the [Concise Binary Object Representation (CBOR)](https://cbor.io/) supporting the [IPLD Data Model](https://ipld.io/docs/data-model/) and enforcing a unique (strict) encoded representation of items.

You can install this library with `pip`:

```
pip install dag-cbor
```

The core functionality of the library is performed by the `encode` and `decode` functions:

```python
>>> import dag_cbor
>>> dag_cbor.encode({'a': 12, 'b': 'hello!'})
b'\xa2aa\x0cabfhello!'
>>> dag_cbor.decode(b'\xa2aa\x0cabfhello!')
{'a': 12, 'b': 'hello!'}
```

The [documentation](https://hashberg-io.github.io/py-dag-cbor/dag_cbor/index.html) for this library was generated with [pdoc](https://pdoc3.github.io/pdoc/).
