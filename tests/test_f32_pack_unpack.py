import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from fpu_f32 import pack_f32_fields, unpack_f32_fields, classify_f32, bits_to_hex_str

def i2b(width, val):
    val &= (1<<width)-1
    s = f"{val:0{width}b}"
    return [1 if c=='1' else 0 for c in s]

def test_pack_3_75():
    # 3.75 = 1.875 * 2^1  => exp = 127+1 = 128 (0b1000_0000), frac = 0.875 -> 0x700000
    sign = 0
    exp  = i2b(8, 128)
    frac = i2b(23, 0x700000)
    bits = pack_f32_fields(sign, exp, frac)
    assert bits_to_hex_str(bits) == "0x40700000"
    # round-trip fields
    s2, e2, f2 = unpack_f32_fields(bits)
    assert s2 == sign and e2 == exp and f2 == frac

def test_zeros_infs_nan():
    pos_zero = pack_f32_fields(0, i2b(8,0), i2b(23,0))
    neg_zero = pack_f32_fields(1, i2b(8,0), i2b(23,0))
    pos_inf  = pack_f32_fields(0, i2b(8,0xFF), i2b(23,0))
    neg_inf  = pack_f32_fields(1, i2b(8,0xFF), i2b(23,0))
    quiet_nan= pack_f32_fields(0, i2b(8,0xFF), i2b(23,1))  # any nonzero frac

    assert classify_f32(pos_zero)["kind"] == "ZERO" and classify_f32(pos_zero)["sign"] == 0
    assert classify_f32(neg_zero)["kind"] == "ZERO" and classify_f32(neg_zero)["sign"] == 1
    assert classify_f32(pos_inf )["kind"] == "INF"  and classify_f32(pos_inf )["sign"] == 0
    assert classify_f32(neg_inf )["kind"] == "INF"  and classify_f32(neg_inf )["sign"] == 1
    assert classify_f32(quiet_nan)["kind"] == "NAN"

def test_subnormal_classification():
    # Smallest positive subnormal: sign=0, exp=0, frac=1
    sub = pack_f32_fields(0, i2b(8,0), i2b(23,1))
    c = classify_f32(sub)
    assert c["kind"] == "SUBNORMAL" and c["sign"] == 0
