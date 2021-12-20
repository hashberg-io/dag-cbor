@echo off
mypy --strict dag_cbor
pylint --rcfile=.pylintrc --disable=fixme dag_cbor
pytest test/ --cov=./dag_cbor
coverage html
@pause
