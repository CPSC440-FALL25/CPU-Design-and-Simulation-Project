import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from fpu_f32 import pack_f32_fields, classify_f32, bits_to_hex_str, fadd_f32, fsub_f32

def i2b(width, val):
    val &= (1<<width)-1
    s = f"{val:0{width}b}"
    return [1 if c=='1' else 0 for c in s]

# helpers for a few known values
def bits_1_0():   return pack_f32_fields(0, i2b(8,127), i2b(23,0))         # 1.0 => 0x3F800000
def bits_1_5():   return pack_f32_fields(0, i2b(8,127), i2b(23,0x400000))  # 1.5 => 0x3FC00000
def bits_2_0():   return pack_f32_fields(0, i2b(8,128), i2b(23,0))         # 2.0 => 0x40000000
def bits_2_25():  return pack_f32_fields(0, i2b(8,128), i2b(23,0x100000))  # 2.25 => 0x40100000
def bits_2_5():   return pack_f32_fields(0, i2b(8,128), i2b(23,0x200000))  # 2.5  => 0x40200000
def bits_3_75():  return pack_f32_fields(0, i2b(8,128), i2b(23,0x700000))  # 3.75 => 0x40700000
def bits_0_5():   return pack_f32_fields(0, i2b(8,126), i2b(23,0))         # 0.5 => 0x3F000000

def test_add_simple():
    a = bits_1_0(); b = bits_1_5()
    out = fadd_f32(a, b)
    assert bits_to_hex_str(out["res_bits"]) == "0x40200000"  # 2.5

def test_add_mixed_exponents():
    a = bits_1_5(); b = bits_2_25()
    out = fadd_f32(a, b)
    assert bits_to_hex_str(out["res_bits"]) == "0x40700000"  # 3.75

def test_sub_simple():
    a = bits_2_0(); b = bits_1_5()
    out = fsub_f32(a, b)
    assert bits_to_hex_str(out["res_bits"]) == "0x3F000000"  # 0.5

def test_sub_cancel_to_zero_positive_zero():
    a = bits_1_5(); b = bits_1_5()
    out = fsub_f32(a, b)
    k = classify_f32(out["res_bits"])
    assert k["kind"] == "ZERO" and k["sign"] == 0

def test_specials_inf_nan():
    pos_inf  = pack_f32_fields(0, i2b(8,0xFF), i2b(23,0))
    neg_inf  = pack_f32_fields(1, i2b(8,0xFF), i2b(23,0))
    qnan     = pack_f32_fields(0, i2b(8,0xFF), i2b(23,1))
    one      = bits_1_0()

    # ∞ + (−∞) -> NaN invalid
    out = fadd_f32(pos_inf, neg_inf)
    assert classify_f32(out["res_bits"])["kind"] == "NAN" and out["flags"]["invalid"] == 1

    # NaN propagates
    out = fadd_f32(qnan, one)
    assert classify_f32(out["res_bits"])["kind"] == "NAN"

    # ∞ − ∞ -> NaN invalid (via fsub)
    out = fsub_f32(pos_inf, pos_inf)
    assert classify_f32(out["res_bits"])["kind"] == "NAN" and out["flags"]["invalid"] == 1
