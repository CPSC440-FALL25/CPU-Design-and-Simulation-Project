
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
from bitvec import Bits, zero_bits, left_pad, trim_width, twos_complement_negate, add_rca, bits_to_str, bits_to_hex, is_negative
from shifter import shifter
from alu import alu

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
    if op != "MUL":
        raise NotImplementedError("Only MUL (signed* signed, low 32) is implemented in this step")

    if len(rs1_bits) != 32 or len(rs2_bits) != 32:
        raise ValueError("MUL currently expects 32-bit inputs")

    # Get magnitudes and result sign (signed multiply semantics)
    a_mag, a_neg = _abs_bits(rs1_bits)
    b_mag, b_neg = _abs_bits(rs2_bits)
    res_neg = 1 if (a_neg ^ b_neg) else 0

    # 64-bit accumulator and 64-bit multiplicand; 32-bit multiplier (magnitudes, unsigned shift)
    acc = zero_bits(64)
    mcand = left_pad(a_mag, 64)          # multiplicand in low 32, rest 0
    mplier = b_mag[:]                    # 32 bits

    trace = []
    for step in range(32):
        # If LSB of multiplier is 1, add multiplicand into acc
        if mplier[-1] == 1:
            acc, _ = add_rca(acc, mcand, 0)
            action = "ADD"
        else:
            action = "NOP"

        # record a compact trace line (hex for readability)
        t = f"step={step:02d} acc=0x{bits_to_hex(acc)[-16:]} mcand<<=1=0x{bits_to_hex(mcand)[-16:]} mplier=0x{bits_to_hex(left_pad(mplier,32))[-8:]} action={action}"
        trace.append(t)

        # Shift multiplicand left by 1 (logical), multiplier right by 1 (logical on magnitude)
        mcand = shifter(mcand, 1, "SLL")
        mplier = shifter(mplier, 1, "SRL")

    # Apply sign to the 64-bit product if needed
    if res_neg == 1 and any(bit == 1 for bit in acc):  # negate non-zero acc
        acc = twos_complement_negate(acc)

    # Low/High halves
    lo = acc[-32:]
    hi = acc[:32]

    # Overflow (extra, for grading): does the 64-bit product fit in signed 32?
    # If we sign-extend the low 32 back to 64 and it equals the true acc, it's representable.
    sx_lo_to_64 = _sign_extend(lo, 64)
    overflow = 0 if _equal_bits(sx_lo_to_64, acc) else 1

    return {
        "rd_bits": lo,
        "hi_bits": hi,
        "overflow": overflow,
        "trace": trace,
    }
