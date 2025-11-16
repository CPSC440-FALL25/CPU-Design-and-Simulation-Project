import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from twos_complement import encode_twos_complement, decode_twos_complement

def test_encode_examples():
    e = encode_twos_complement(13)
    assert e['hex'] == '0x0000000D'
    e = encode_twos_complement(-13)
    assert e['hex'] == '0xFFFFFFF3'
    assert e['overflow'] == 0

def test_overflow_edge():
    assert encode_twos_complement( 2_147_483_647 )['overflow'] == 0
    assert encode_twos_complement( 2_147_483_648 )['overflow'] == 1  # 2^31
    assert encode_twos_complement(-2_147_483_648 )['overflow'] == 0
    assert encode_twos_complement(-2_147_483_649 )['overflow'] == 1

def test_decode_roundtrip_small():
    for v in (-13, -7, -1, 0, 13):
        enc = encode_twos_complement(v)
        dec = decode_twos_complement(enc['bin'].replace('_',''))
        assert int(dec['value_str']) == v

def test_decode_boundary():
    int_min_bits = '1' + '0'*31
    int_max_bits = '0' + '1'*31
    assert int(decode_twos_complement(int_min_bits)['value_str']) == -2_147_483_648
    assert int(decode_twos_complement(int_max_bits)['value_str']) ==  2_147_483_647
