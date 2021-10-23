mypy --strict dag_cbor
pylint dag_cbor
pytest test/ --cov=./dag_cbor
coverage html
@pause
