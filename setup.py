""" setup.py created according to https://packaging.python.org/tutorials/packaging-projects """

import setuptools #type:ignore

setuptools.setup(
    name="py-dag-cbor",
    version="0.0.0",
    author="hashberg",
    author_email="sg495@users.noreply.github.com",
    description="Python implementation of the DAG-CBOR codec for IPLD.",
    url="https://github.com/hashberg-io/py-dag-cbor",
    packages=setuptools.find_packages(exclude=["test"]),
    classifiers=[ # see https://pypi.org/classifiers/
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Planning",
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
