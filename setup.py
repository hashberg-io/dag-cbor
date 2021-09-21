""" setup.py created according to https://packaging.python.org/tutorials/packaging-projects """

import setuptools #type:ignore

with open("README.md", "r") as fh:
    long_description: str = fh.read()

setuptools.setup(
    name="dag-cbor",
    version="0.0.5post1",
    author="hashberg",
    author_email="sg495@users.noreply.github.com",
    url="https://github.com/hashberg-io/dag-cbor",
    description="Python implementation of the DAG-CBOR codec.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=["test"]),
    classifiers=[ # see https://pypi.org/classifiers/
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
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
