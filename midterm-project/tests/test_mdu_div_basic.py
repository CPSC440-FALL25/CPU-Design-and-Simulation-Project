import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from mdu_div import mdu_div
from bitvec import bits_to_hex

def i2b32(v: int):
    v &= (1<<32)-1
    return [1 if c=='1' else 0 for c in f"{v:032b}"]

def h32(b): return bits_to_hex(b)[-8:]

def test_div_signed_basic():
    out = mdu_div("DIV", i2b32(-7), i2b32(3))
    assert h32(out["q_bits"]) == "FFFFFFFE"  # -2
    assert h32(out["r_bits"]) == "FFFFFFFF"  # -1

def test_divu_basic():
    out = mdu_div("DIVU", i2b32(0x80000000), i2b32(3))
    assert h32(out["q_bits"]) == "2AAAAAAA"
    assert h32(out["r_bits"]) == "00000002"

def test_div_by_zero_signed():
    out = mdu_div("DIV", i2b32(5), i2b32(0))
    assert h32(out["q_bits"]) == "FFFFFFFF"
    assert h32(out["r_bits"]) == "00000005"

def test_div_by_zero_unsigned():
    out = mdu_div("DIVU", i2b32(5), i2b32(0))
    assert h32(out["q_bits"]) == "FFFFFFFF"
    assert h32(out["r_bits"]) == "00000005"

def test_intmin_overflow_case():
    out = mdu_div("DIV", i2b32(-0x80000000), i2b32(-1))
    assert h32(out["q_bits"]) == "80000000"
    assert h32(out["r_bits"]) == "00000000"
    assert out["overflow"] == 1

def test_rem_signed_sign_and_div0():
    out = mdu_div("REM", i2b32(-7), i2b32(3))
    assert h32(out["r_bits"]) == "FFFFFFFF"  # -1

    out2 = mdu_div("REM", i2b32(5), i2b32(0))
    assert out2["q_bits"] is None
    assert h32(out2["r_bits"]) == "00000005"

def test_remu_div0():
    out = mdu_div("REMU", i2b32(0xDEADBEEF), i2b32(0))
    assert out["q_bits"] is None
    assert h32(out["r_bits"]) == "DEADBEEF"
