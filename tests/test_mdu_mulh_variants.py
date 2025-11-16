import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from mdu import mdu_mul
from bitvec import bits_to_hex

def i2b32(v: int):
    v &= (1<<32)-1
    return [1 if c=='1' else 0 for c in f"{v:032b}"]

def hex32(bits): return bits_to_hex(bits)[-8:]

def test_mulh_signed_signed_sample():
    a, b = i2b32(12345678), i2b32(-87654321)
    out = mdu_mul("MULH", a, b)
    assert hex32(out["hi_bits"]) == "FFFC27C9"  # sample from spec

def test_mulhu_unsigned_unsigned():
    a, b = i2b32(0x80000000), i2b32(3)
    out = mdu_mul("MULHU", a, b)
    # compare to Python unsigned product >> 32 (allowed in tests)
    hi = ((0x80000000 * 3) >> 32) & 0xFFFFFFFF
    assert hex32(out["hi_bits"]) == f"{hi:08X}"

def test_mulhsu_signed_unsigned():
    a, b = i2b32(-2), i2b32(3)
    out = mdu_mul("MULHSU", a, b)
    prod = (-2 * 3) & ((1<<64)-1)
    hi = (prod >> 32) & 0xFFFFFFFF
    assert hex32(out["hi_bits"]) == f"{hi:08X}"
