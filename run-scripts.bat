mypy dag_cbor
@pause
pylint dag_cbor
@pause
pdoc --config latex_math=True --config show_type_annotations=True --force --html --output-dir docs dag_cbor
@pause
pytest test/ --cov=./dag_cbor
coverage html
@pause
