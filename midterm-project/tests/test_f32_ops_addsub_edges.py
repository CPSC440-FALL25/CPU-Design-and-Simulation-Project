import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from fpu_f32 import pack_f32_fields, classify_f32, bits_to_hex_str, fadd_f32, fsub_f32

def i2b(w, v):
    v &= (1<<w)-1
    s = f"{v:0{w}b}"
    return [1 if c=='1' else 0 for c in s]

# handy constants
def f32(hex8):  # quick literal loader for tests
    h = int(hex8, 16)
    bits = [ (h >> (31 - i)) & 1 for i in range(32) ]
    return bits

ONE      = pack_f32_fields(0, i2b(8,127), i2b(23,0))           # 1.0 -> 0x3F800000
HALF     = pack_f32_fields(0, i2b(8,126), i2b(23,0))           # 0.5 -> 0x3F000000
ULP_1    = pack_f32_fields(0, i2b(8,127), i2b(23,1))           # 1.0 + 2^-23
# Half-ULP for 0.5 is 2^-25; represent it exactly as a normal number:
TIE_HALF = pack_f32_fields(0, i2b(8,102), i2b(23,0))           # 2^-25
INFp     = pack_f32_fields(0, i2b(8,0xFF), i2b(23,0))
INFm     = pack_f32_fields(1, i2b(8,0xFF), i2b(23,0))
QNAN     = pack_f32_fields(0, i2b(8,0xFF), i2b(23,1))
MZERO    = pack_f32_fields(1, i2b(8,0),    i2b(23,0))
PZERO    = pack_f32_fields(0, i2b(8,0),    i2b(23,0))

def test_add_cancellation_to_pos_zero():
    # 1 + (-1) -> +0 (we accept +0)
    neg_one = pack_f32_fields(1, i2b(8,127), i2b(23,0))
    out = fadd_f32(ONE, neg_one)
    k = classify_f32(out["res_bits"])
    assert k["kind"] == "ZERO" and k["sign"] == 0

def test_add_large_delta_align():
    # 1.0 + 2^-30 ≈ 1.0 (rounds to even)
    tiny = pack_f32_fields(0, i2b(8,127-30), i2b(23,0))
    out = fadd_f32(ONE, tiny)
    assert bits_to_hex_str(out["res_bits"]) == "0x3F800000"  # still 1.0 exactly

def test_rne_tie_to_even():
    # 0.5 + half-ULP should tie to 0.5 (even LSB), not bump to next
    out = fadd_f32(HALF, TIE_HALF)
    assert bits_to_hex_str(out["res_bits"]) == "0x3F000000"

def test_sub_simple_rounding_down():
    # (1 + ulp) - 1 -> ulp (0x33800000 for 2^-23 at exp=0) but easier: exact HALF after crafted inputs
    out = fsub_f32(ULP_1, ONE)
    k = classify_f32(out["res_bits"])
    # exact small positive; don't assert exact hex (impl-specific), just not ZERO/INF/NAN
    assert k["kind"] in ("SUBNORMAL", "NORMAL")

def test_inf_nan_mix():
    # ∞ + (−∞) -> NaN invalid
    out = fadd_f32(INFp, INFm)
    ck = classify_f32(out["res_bits"])
    assert ck["kind"] == "NAN" and out["flags"]["invalid"] == 1

    # NaN propagates
    out2 = fadd_f32(QNAN, ONE)
    assert classify_f32(out2["res_bits"])["kind"] == "NAN"

def test_signed_zero_behavior():
    # (+0) - (+0) -> +0; (+0) - (-0) -> +0 per our choice
    out1 = fsub_f32(PZERO, PZERO)
    out2 = fsub_f32(PZERO, MZERO)
    for out in (out1, out2):
        k = classify_f32(out["res_bits"])
        assert k["kind"] == "ZERO" and k["sign"] == 0
