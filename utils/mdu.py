
"""
MDU (Multiply/Divide Unit) — multiply (shift-add) for RV32

- Pure bit-vector implementation: no + - * / << >> on integers.
- Uses ALU and shifter from our bit-vector core.
- Exposes a simple interface for MUL (low 32 bits) with a per-step trace.

API (initial):
    mdu_mul(op, rs1_bits, rs2_bits) -> dict with keys:
        rd_bits   : low 32-bit result (Bits)
        hi_bits   : high 32 bits of the 64-bit product (Bits)  (for future MULH* tests)
        overflow  : 0/1 (extra for grading: whether true 64-bit product doesn't fit signed 32)
        trace     : list of per-iteration snapshots (strings)
Supported ops: "MUL" (signed * signed, low 32 bits). Others raise NotImplementedError for now.
"""

from typing import List, Dict, Tuple
from .bitvec import Bits, zero_bits, left_pad, trim_width, twos_complement_negate, add_rca, bits_to_str, bits_to_hex, is_negative
from .shifter import shifter
from .alu import alu

def _sign_extend(bits: Bits, total_width: int) -> Bits:
    sign = bits[0]
    pad = [sign] * (total_width - len(bits))
    return pad + bits[:]

def _abs_bits(bits: Bits) -> Tuple[Bits, int]:
    """Return (magnitude_bits, was_negative) for two's-complement input."""
    if is_negative(bits):
        return twos_complement_negate(bits), 1
    return bits[:], 0

def _equal_bits(a: Bits, b: Bits) -> bool:
    if len(a) != len(b):
        return False
    return all(x==y for x,y in zip(a,b))

def mdu_mul(op: str, rs1_bits: Bits, rs2_bits: Bits) -> Dict[str, object]:
    if op not in ("MUL", "MULH", "MULHU", "MULHSU"):
        raise NotImplementedError(f"Unsupported op: {op}")
    if len(rs1_bits) != 32 or len(rs2_bits) != 32:
        raise ValueError("MUL family expects 32-bit inputs")

    # Choose signedness per op
    if op in ("MUL", "MULH"):                    # signed × signed
        a_mag, a_neg = _abs_bits(rs1_bits)
        b_mag, b_neg = _abs_bits(rs2_bits)
        res_neg = 1 if (a_neg ^ b_neg) else 0
    elif op == "MULHU":                          # unsigned × unsigned
        a_mag, b_mag = rs1_bits[:], rs2_bits[:]
        res_neg = 0
    else:  # "MULHSU"                            # signed × unsigned
        a_mag, a_neg = _abs_bits(rs1_bits)
        b_mag = rs2_bits[:]                      # use as magnitude; do NOT abs()
        res_neg = a_neg

    # 64-bit accumulator + 64-bit mcand, 32-bit mplier (magnitudes)
    acc = zero_bits(64)
    mcand = left_pad(a_mag, 64)
    mplier = b_mag[:]

    trace = []
    for step in range(32):
        if mplier[-1] == 1:
            acc, _ = add_rca(acc, mcand, 0)
            action = "ADD"
        else:
            action = "NOP"

        t = (
            f"step={step:02d} "
            f"acc=0x{bits_to_hex(acc)[-16:]} "
            f"mcand<<=1=0x{bits_to_hex(mcand)[-16:]} "
            f"mplier=0x{bits_to_hex(left_pad(mplier,32))[-8:]} "
            f"action={action}"
        )
        trace.append(t)

        mcand = shifter(mcand, 1, "SLL")
        mplier = shifter(mplier, 1, "SRL")

    # Apply sign if needed (only the signed cases)
    if res_neg == 1 and any(bit == 1 for bit in acc):
        acc = twos_complement_negate(acc)

    lo = acc[-32:]
    hi = acc[:32]

    # Overflow flag (extra for grading): only meaningful for plain MUL
    if op == "MUL":
        sx_lo_to_64 = _sign_extend(lo, 64)
        overflow = 0 if _equal_bits(sx_lo_to_64, acc) else 1
    else:
        overflow = 0

    return {
        "rd_bits": lo,    # architectural result for MUL; for H-variants tests read hi_bits
        "hi_bits": hi,    # high 32 (used by MULH/MULHU/MULHSU)
        "overflow": overflow,
        "trace": trace,
    }
