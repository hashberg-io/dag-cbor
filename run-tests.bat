@echo off
mypy --strict dag_cbor
pylint --rcfile=.pylintrc --disable=fixme dag_cbor
python -m readme_renderer README.rst -o README-PROOF.html
pytest test/ --cov=./dag_cbor
coverage html
@pause
