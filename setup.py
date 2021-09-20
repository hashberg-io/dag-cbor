""" setup.py created according to https://packaging.python.org/tutorials/packaging-projects """

import setuptools #type:ignore

with open("README.md", "r") as fh:
    long_description: str = fh.read()

setuptools.setup(
    name="dag-cbor",
    version="0.0.4",
    author="hashberg",
    author_email="sg495@users.noreply.github.com",
    url="https://github.com/hashberg-io/py-dag-cbor",
    description="Python implementation of the DAG-CBOR codec.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["test"]),
    classifiers=[ # see https://pypi.org/classifiers/
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Typing :: Typed",
    ],
    package_data={"": [],
                  "dag_cbor": ["dag_cbor/py.typed"],
                 },
    install_requires=[
        "py-cid",
        "py-multihash"
    ],
    include_package_data=True
)
