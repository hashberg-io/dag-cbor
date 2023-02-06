Decoding
========

The core decoding functionality is performed by the :func:`~dag_cbor.decoding.decode` function, which decodes :obj:`bytes` into a value:

>>> import dag_cbor
>>> dag_cbor.decode(b'\xa2aa\x0cabfhello!')
{'a': 12, 'b': 'hello!'}

A buffered binary stream (i.e. an instance of :obj:`~io.BufferedIOBase`) can be passed to the :func:`~dag_cbor.decoding.decode` function instead of a :obj:`bytes` object, in which case the contents of the stream are read in their entirety and decoded:

>>> stream = BytesIO(b'\xa2aa\x0cabfhello!')
>>> dag_cbor.decode(stream)
{'a': 12, 'b': 'hello!'}

The decision to read the entirety of the stream stems from the `DAG-CBOR codec <https://ipld.io/specs/codecs/dag-cbor/spec/>`_ specification, stating that encoding and decoding is only allowed on a single top-level item.
However, the optional keyword argument ``allow_concat`` (default :obj:`False`) can be set to :obj:`True` to disable this behaviour and allow only part of the stream to be decoded.
