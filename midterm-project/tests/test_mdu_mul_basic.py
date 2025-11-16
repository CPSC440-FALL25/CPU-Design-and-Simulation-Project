
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from bitvec import Bits
from mdu import mdu_mul
from bitvec import bits_to_hex

def int_to_bits(width, val):
    # tests may use Python arithmetic; allowed in tests
    mask = (1 << width) - 1
    v = val & mask
    s = f"{v:0{width}b}"
    return [1 if c == '1' else 0 for c in s]

def hex32(bits):
    h = bits_to_hex(bits)
    return h[-8:]

def test_mul_small():
    a = int_to_bits(32, 3)
    b = int_to_bits(32, 5)
    out = mdu_mul("MUL", a, b)
    assert hex32(out["rd_bits"]) == "0000000F"
    assert out["overflow"] == 0

def test_mul_sign_and_overflow_sample():
    a = int_to_bits(32, 12345678)
    b = int_to_bits(32, -87654321)
    out = mdu_mul("MUL", a, b)
    assert hex32(out["rd_bits"]) == "D91D0712"
    assert out["overflow"] == 1
    # trace exists and has 32 steps
    assert len(out["trace"]) == 32
