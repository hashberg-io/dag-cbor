
Encoding
========

The core encoding functionality is performed by the :func:`~dag_cbor.encoding.encode` function, which encods a value into a :obj:`bytes` object:

>>> import dag_cbor
>>> dag_cbor.encode({'a': 12, 'b': 'hello!'})
b'\xa2aa\x0cabfhello!'

A buffered binary stream (i.e. an instance of :obj:`~io.BufferedIOBase`) can be passed to the :func:`~dag_cbor.encoding.encode` function using the optional keyword argument ``stream``, in which case the encoded bytes are written to the stream and the number of bytes written is returned:

>>> from io import BytesIO
>>> stream = BytesIO()
>>> dag_cbor.encode({'a': 12, 'b': 'hello!'}, stream=stream)
13
>>> stream.getvalue()
b'\xa2aa\x0cabfhello!'
