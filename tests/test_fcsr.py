import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from fcsr import (
    new_fcsr, fcsr_pack_u8, fcsr_unpack_u8, fcsr_set_rounding, fcsr_get_rounding,
    fcsr_read_fflags, fcsr_write_fflags, fcsr_clear_fflags, fcsr_accumulate,
    FRM_RNE, FRM_RTZ
)
from fpu_f32 import pack_f32_fields, fmul_f32

def i2b(width, val):
    # tests may use host ints freely
    val &= (1<<width)-1
    s = f"{val:0{width}b}"
    return [1 if c=='1' else 0 for c in s]

def bits_to_int(bits):
    x = 0
    for b in bits:
        x = (x << 1) | (1 if b else 0)
    return x

# some float32 literals
def f32_from_fields(s,e,f): return pack_f32_fields(s, i2b(8,e), i2b(23,f))
POS_ZERO = f32_from_fields(0, 0x00, 0x000000)
POS_INF  = f32_from_fields(0, 0xFF, 0x000000)
MAX_FIN  = f32_from_fields(0, 0xFE, 0x7FFFFF)   # largest finite
F32_2_0  = f32_from_fields(0, 0x80, 0x000000)   # 2.0
MIN_NORM = f32_from_fields(0, 0x01, 0x000000)   # 2^-126
F32_0_25 = f32_from_fields(0, 0x7D, 0x000000)   # 0.25

def test_default_and_rounding_set_get_and_pack():
    f = new_fcsr()
    # default pack is 0x00
    assert bits_to_int(fcsr_pack_u8(f)) == 0

    # set RTZ and verify top 3 bits == 001 -> 0x20 overall
    fcsr_set_rounding(f, FRM_RTZ)
    u8 = bits_to_int(fcsr_pack_u8(f))
    assert (u8 & 0xE0) == 0x20  # frm in bits 7..5 is 001

    # get returns same bits
    assert fcsr_get_rounding(f) == FRM_RTZ

def test_accumulate_invalid_from_op():
    f = new_fcsr()
    out = fmul_f32(POS_ZERO, POS_INF)  # 0 * inf -> NaN, invalid=1
    fcsr_accumulate(f, out["flags"])
    ff = fcsr_read_fflags(f)  # [NV,DZ,OF,UF,NX]
    assert ff[0] == 1 and ff[1] == 0 and ff[2] == 0 and ff[3] == 0

def test_overflow_then_underflow_sticky_and_clear():
    f = new_fcsr()
    # overflow: max_finite * 2.0 -> +inf, overflow=1
    out1 = fmul_f32(MAX_FIN, F32_2_0)
    fcsr_accumulate(f, out1["flags"])
    # underflow: min_normal * 0.25 -> flush to zero, underflow=1
    out2 = fmul_f32(MIN_NORM, F32_0_25)
    fcsr_accumulate(f, out2["flags"])

    ff = fcsr_read_fflags(f)  # [NV,DZ,OF,UF,NX]
    assert ff[2] == 1  # OF
    assert ff[3] == 1  # UF

    # now clear
    fcsr_clear_fflags(f)
    ff2 = fcsr_read_fflags(f)
    assert ff2 == [0,0,0,0,0]
