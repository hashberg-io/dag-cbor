dag-cbor: A Python implementation of the `DAG-CBOR codec <https://ipld.io/specs/codecs/dag-cbor/spec/>`_
========================================================================================================

.. image:: https://img.shields.io/badge/python-3.7+-green.svg
    :target: https://docs.python.org/3.7/
    :alt: Python versions

.. image:: https://img.shields.io/pypi/v/dag-cbor.svg
    :target: https://pypi.python.org/pypi/dag-cbor/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/status/dag-cbor.svg
    :target: https://pypi.python.org/pypi/dag-cbor/
    :alt: PyPI status

.. image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: https://github.com/python/mypy
    :alt: Checked with Mypy
    
.. image:: https://readthedocs.org/projects/dag-cbor/badge/?version=latest
    :target: https://dag-cbor.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://github.com/hashberg-io/dag-cbor/actions/workflows/python-pytest.yml/badge.svg
    :target: https://github.com/hashberg-io/dag-cbor/actions/workflows/python-pytest.yml
    :alt: Python package status

.. image:: https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square
    :target: https://github.com/RichardLitt/standard-readme
    :alt: standard-readme compliant


This is a fully compliant Python implementation of the `DAG-CBOR codec <https://ipld.io/specs/codecs/dag-cbor/spec/>`_, a subset of the `Concise Binary Object Representation (CBOR) <https://cbor.io/>`_ supporting the `IPLD Data Model <https://ipld.io/docs/data-model/>`_ and enforcing a unique (strict) encoded representation of items.


.. contents::


Install
-------

You can install the latest release from `PyPI <https://pypi.org/project/dag-cbor/>`_ as follows:

.. code-block:: console

    $ pip install --upgrade dag-cbor


Usage
-----

We suggest you import DAG-CBOR as follows:

>>> import dag_cbor

Below are some basic usage examples, to get you started: for detailed documentation, see https://dag-cbor.readthedocs.io/


Encoding and decoding
^^^^^^^^^^^^^^^^^^^^^

>>> dag_cbor.encode({'a': 12, 'b': 'hello!'})
b'\xa2aa\x0cabfhello!'
>>> dag_cbor.decode(b'\xa2aa\x0cabfhello!')
{'a': 12, 'b': 'hello!'}


Random DAG-CBOR data
^^^^^^^^^^^^^^^^^^^^

>>> import pprint # pretty-printing
>>> custom_opts = dict(min_codepoint=0x41, max_codepoint=0x5a, include_cid=False)
>>> with dag_cbor.random.options(**custom_opts):
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



API
---

For the full API documentation, see https://dag-cbor.readthedocs.io/


Contributing
------------

Please see `<CONTRIBUTING.md>`_.


License
-------

`MIT © Hashberg Ltd. <LICENSE>`_
