import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))
from mdu import mdu_mul
from bitvec import bits_to_hex

def i2b32(v):
    v &= (1<<32)-1
    return [1 if c=='1' else 0 for c in f"{v:032b}"]

def hex32(b): return bits_to_hex(b)[-8:]

def test_mul_zeroes_and_ones():
    for a in (0, 1, -1, 0x7FFFFFFF, -0x80000000):
        out = mdu_mul("MUL", i2b32(a), i2b32(0))
        assert hex32(out["rd_bits"]) == "00000000"
        assert out["overflow"] == 0

def test_mul_neg_neg_is_pos():
    out = mdu_mul("MUL", i2b32(-3), i2b32(-7))
    assert hex32(out["rd_bits"]) == f"{(((-3)*(-7)) & 0xFFFFFFFF):08X}"

def test_mul_intmin_times_minus1_overflow_lowword():
    out = mdu_mul("MUL", i2b32(-0x80000000), i2b32(-1))
    # Python calc for low 32
    expect = ((-0x80000000)*(-1)) & 0xFFFFFFFF
    assert hex32(out["rd_bits"]) == f"{expect:08X}"
    assert out["overflow"] == 1  # product doesn't fit signed 32
