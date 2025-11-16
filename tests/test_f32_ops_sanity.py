import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from fpu_f32 import pack_f32_fields, classify_f32, bits_to_hex_str, fmul_f32

def i2b(width, val):
    val &= (1<<width)-1
    s = f"{val:0{width}b}"
    return [1 if c=='1' else 0 for c in s]

def bits_1_0():   return pack_f32_fields(0, i2b(8,127), i2b(23,0))         # 1.0 => 0x3F800000
def bits_1_5():   return pack_f32_fields(0, i2b(8,127), i2b(23,0x400000))  # 1.5 => 0x3FC00000
def bits_2_25():
    # 2.25 = 1.125 * 2^1  -> exponent 128, fraction = 0.125 = 2^-3 -> 1 << 20 = 0x100000
    return pack_f32_fields(0, i2b(8, 128), i2b(23, 0x100000))

def bits_3_375(): return pack_f32_fields(0, i2b(8,128), i2b(23,0x580000))  # 3.375 => 0x40580000

def test_mul_by_one():
    a = bits_1_0(); b = bits_2_25()
    out = fmul_f32(a, b)
    assert bits_to_hex_str(out["res_bits"]) == "0x40100000"   # 2.25

def test_mul_simple_normal():
    a = bits_1_5(); b = bits_1_5()
    out = fmul_f32(a, b)
    assert bits_to_hex_str(out["res_bits"]) == "0x40100000"  # 1.5*1.5=2.25

def test_mul_needs_right_normalize():
    a = bits_1_5(); b = bits_2_25()
    out = fmul_f32(a, b)
    assert bits_to_hex_str(out["res_bits"]) == "0x40580000"  # 3.375

def test_specials():
    pos_zero = pack_f32_fields(0, i2b(8,0), i2b(23,0))
    neg_zero = pack_f32_fields(1, i2b(8,0), i2b(23,0))
    pos_inf  = pack_f32_fields(0, i2b(8,0xFF), i2b(23,0))
    neg_inf  = pack_f32_fields(1, i2b(8,0xFF), i2b(23,0))
    qnan     = pack_f32_fields(0, i2b(8,0xFF), i2b(23,1))

    # 0 * finite = 0 (sign xor)
    out = fmul_f32(pos_zero, bits_2_25())
    assert classify_f32(out["res_bits"])['kind'] == 'ZERO' and classify_f32(out["res_bits"])['sign'] == 0
    out = fmul_f32(neg_zero, bits_2_25())
    assert classify_f32(out["res_bits"])['kind'] == 'ZERO' and classify_f32(out["res_bits"])['sign'] == 1

    # inf * finite = inf (sign xor)
    out = fmul_f32(pos_inf, bits_1_5())
    assert classify_f32(out["res_bits"])['kind'] == 'INF' and classify_f32(out["res_bits"])['sign'] == 0
    out = fmul_f32(neg_inf, bits_1_5())
    assert classify_f32(out["res_bits"])['kind'] == 'INF' and classify_f32(out["res_bits"])['sign'] == 1

    # 0 * inf => NaN, invalid
    out = fmul_f32(pos_zero, pos_inf)
    assert classify_f32(out["res_bits"])['kind'] == 'NAN'
    assert out['flags']['invalid'] == 1

    # propagate NaN
    out = fmul_f32(qnan, bits_1_5())
    assert classify_f32(out["res_bits"])['kind'] == 'NAN'
