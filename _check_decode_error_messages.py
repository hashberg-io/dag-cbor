r"""
    Prints error messages for a variety of decoding failures, to check that the new detailed error messages look all right.
"""
# pylint: disable = all

from typing import List
from multiformats import varint
from dag_cbor.random import rand_data
from dag_cbor import encode, decode
from dag_cbor.ipld import Kind
from dag_cbor.encoding import CBOREncodingError
from dag_cbor.decoding import CBORDecodingError

import random

random.seed(0)

test_cases = [
    # err._required_multicodec
    "00",
    "81e20301",
    # err._multiple_top_level_items
    "718301020301",
    # err._invalid_float
    "71fb7ff8000000000000",
    "71fb7ff0000000000000",
    "71fbfff0000000000000",
    # err._unexpected_eof
    "71",
    "71830102",
    "71fb3fb99999",
    "7146"+"7891bc",
    "7166"+b"hello".hex(),
    "71a1"+("66"+b"hello".hex()),
    # err._invalid_additional_info
    "715c",
    "71f9",
    # err._excessive_int_size
    "7119"+f"{156:0>4x}",
    "711a"+f"{156:0>8x}",
    "711a"+f"{32033:0>8x}",
    "711b"+f"{156:0>16x}",
    "711b"+f"{32033:0>16x}",
    "711b"+f"{2305067290:0>16x}",
    # err._unicode
    "7161"+b"\xe9".hex(),
    "7162"+b"\xe9\x80".hex(),
    "7162"+b"A\xe9".hex(),
    "7163"+b"AB\xe9".hex(),
    "7162"+b"\xe9Z".hex(),
    "7163"+b"\xe9YZ".hex(),
    "7164"+b"A\xe9YZ".hex(),
    "7165"+b"AB\xe9YZ".hex(),
    "7165"+b"AB\xe9\x80YZ".hex(),
    "7169"+b"ABCD\xe9\x80WXYZ".hex(),
    "7171"+b"ABCDEFGHIJKLMNO\xe9\x80".hex(),
    "71a1"+("63"+b"A\xe9Z".hex())+"01",
    # err._list_item
    "718401"+("1a"+f"{32033:0>8x}")+"0304",
    "718401"+("65"+b"A\xe9YZ".hex())+"0304",
    # err._dict_key_type
    "71a10101",
    "71a18301020301",
    # err._dict_item for a value
    "71a2"+("65"+b"hello".hex())+"01"+("63"+b"bye".hex())+"fb7ff0000000000000",
    # err._duplicate_dict_key for a value
    "71a3"+("65"+b"hello".hex())+"01"+("63"+b"bye".hex())+"02"+("65"+b"hello".hex())+"03",
    # err._dict_key_order
    "71a3"+("65"+b"hello".hex())+"01"+("66"+b"whatup".hex())+"02"+("63"+b"bye".hex())+"03",
    # err._invalid_tag
    "71d829"+"46"+"7891bc",
    # err._cid
    "71d82a"+"46"+"7891bc",
    # err._cid_bytes
    "71d82a"+"65"+b"hello".hex(),
    # err._cid_multibase
    "71d82a"+"450101030405",
    # err._simple_value
    "71f3"
]

def create_embedding_obj(tag: str) -> Kind:
    for obj in rand_data(max_nesting=4):
        if not isinstance(obj, dict):
            continue
        if len(obj) < 4:
            continue
        list_values = [v for v in obj.values() if isinstance(v, list) and len(v) > 4]
        if not list_values:
            continue
        l = random.choice(list_values)
        l[random.randrange(0, len(l))] = tag
        return obj
    return tag

def deep_embed(test_case: str) -> str:
    tag = "0xdeadbeef"
    obj = create_embedding_obj(tag)
    obj_bytes = encode(obj).hex()
    tag_bytes = encode(tag).hex()
    return "71"+obj_bytes.replace(tag_bytes, test_case[2:])

deep_test_cases = [
    deep_embed(random.choice(test_cases))
    for _ in range(10)
]
def print_decode_error(test_case: str) -> bool:
    encoded_bytes = bytes.fromhex(test_case)
    encoded_bytes_str = encoded_bytes.hex() if encoded_bytes else "<NO BYTES>"
    print(f"> Error raised by decoding test case {idx: >2}:\n{encoded_bytes_str}")
    print()
    try:
        decode(encoded_bytes, require_multicodec=True)
    except CBORDecodingError as e:
        print(e)
        cause = e.__cause__
        while cause is not None:
            print(cause)
            cause = cause.__cause__
        print()
        return True
    return False

if __name__ == "__main__":
    print("==== Shallow test cases ====")
    print()
    for idx, test_case in enumerate(test_cases):
        assert print_decode_error(test_case), f"Decoding of test case {idx} should have raised error."
    print("==== Deep test cases ====")
    print()
    for idx, test_case in enumerate(deep_test_cases):
        assert print_decode_error(test_case), f"Decoding of deep test case {idx} should have raised error."
