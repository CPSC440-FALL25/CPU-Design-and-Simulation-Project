"""
Float32 (IEEE-754 single) bitfield tools — pure bit-vectors.

This module:
- Packs from fields: sign(1) | exp(8) | frac(23)  -> 32-bit Bits
- Unpacks fields from a 32-bit Bits pattern
- Classifies special values: ZERO, SUBNORMAL, NORMAL, INF, NAN
- No host float math, no int(..., base), no bin/hex/format in the implementation.

Arithmetic (fadd/fsub/fmul) will come later and reuse bitvec/alu/shifter.

Public:
  pack_f32_fields(sign:int, exp_bits:Bits, frac_bits:Bits) -> Bits
  unpack_f32_fields(bits:Bits) -> (sign:int, exp_bits:Bits, frac_bits:Bits)
  classify_f32(bits:Bits) -> dict {kind: str, sign: int}
  bits_to_hex_str(bits:Bits) -> "0x........"  (uses bitvec helper)
"""

from typing import Tuple, Dict
from bitvec import Bits, bits_to_hex

def _check_len(bits: Bits, expected: int, label: str):
    if len(bits) != expected:
        raise ValueError(f"{label} must be {expected} bits, got {len(bits)}")

def pack_f32_fields(sign: int, exp_bits: Bits, frac_bits: Bits) -> Bits:
    if sign not in (0,1):
        raise ValueError("sign must be 0 or 1")
    _check_len(exp_bits, 8, "exp_bits")
    _check_len(frac_bits, 23, "frac_bits")
    return [sign] + exp_bits[:] + frac_bits[:]

def unpack_f32_fields(bits: Bits) -> Tuple[int, Bits, Bits]:
    if len(bits) != 32:
        raise ValueError("float32 requires 32 bits")
    sign = bits[0]
    exp_bits = bits[1:9]
    frac_bits = bits[9:]
    return sign, exp_bits, frac_bits

def classify_f32(bits: Bits) -> Dict[str, int]:
    """Return kind ∈ {ZERO,SUBNORMAL,NORMAL,INF,NAN} and sign."""
    s, e, f = unpack_f32_fields(bits)
    exp_all_zero = all(b == 0 for b in e)
    exp_all_one  = all(b == 1 for b in e)
    frac_zero    = all(b == 0 for b in f)
    if exp_all_zero and frac_zero:
        return {"kind":"ZERO", "sign": s}
    if exp_all_zero and not frac_zero:
        return {"kind":"SUBNORMAL", "sign": s}
    if exp_all_one and frac_zero:
        return {"kind":"INF", "sign": s}
    if exp_all_one and not frac_zero:
        return {"kind":"NAN", "sign": s}
    return {"kind":"NORMAL", "sign": s}

def bits_to_hex_str(bits: Bits) -> str:
    return "0x" + bits_to_hex(bits)[-8:]
