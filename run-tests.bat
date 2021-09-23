mypy dag_cbor
@pause
pylint dag_cbor
@pause
pytest test/ --cov=./dag_cbor
coverage html
@pause
