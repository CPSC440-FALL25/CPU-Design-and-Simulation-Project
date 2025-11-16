"""
MDU Division (restoring) for RV32 — pure bit-vectors.

Implements:
  - DIV  (signed)
  - DIVU (unsigned)
  - REM  (signed remainder)
  - REMU (unsigned remainder)

RISC-V semantics handled:
  - DIV  x / 0  => q = -1 (0xFFFFFFFF), r = dividend
  - DIVU x / 0  => q = 0xFFFFFFFF,      r = dividend
  - REM  x / 0  => r = dividend         (q is not architecturally used)
  - REMU x / 0  => r = dividend         (q is not architecturally used)
  - DIV INT_MIN / -1 => q = INT_MIN (0x80000000), r = 0, overflow flag = 1
  - Quotient truncates toward zero; remainder has the sign of the dividend (signed ops).

API:
  mdu_div(op, rs1_bits, rs2_bits) -> { "q_bits", "r_bits", "overflow", "trace" }
"""

from typing import Dict, Tuple
from bitvec import Bits, zero_bits, left_pad, twos_complement_negate, is_negative, bits_to_hex
from shifter import shifter
from alu import alu

def _abs_bits(bits: Bits) -> Tuple[Bits, int]:
    if is_negative(bits):
        return twos_complement_negate(bits), 1
    return bits[:], 0

def _is_zero(bits: Bits) -> bool:
    return all(b == 0 for b in bits)

def _eq_bits(a: Bits, b: Bits) -> bool:
    if len(a) != len(b): return False
    return all(x == y for x, y in zip(a, b))

def _set_lsb(bits: Bits, val: int) -> Bits:
    out = bits[:]
    out[-1] = 1 if val else 0
    return out

def _hex32(bits: Bits) -> str:
    return bits_to_hex(bits)[-8:]

def _restoring_div_unsigned(dividend_mag: Bits, divisor_mag: Bits):
    """Unsigned restoring division. Returns (q_bits(32), r_bits(32), trace)."""
    assert len(dividend_mag) == 32 and len(divisor_mag) == 32

    # 33-bit remainder 'r' (MSB acts as sign for subtraction result), 32-bit quotient 'q'
    r = zero_bits(33)
    q = dividend_mag[:]
    d33 = left_pad(divisor_mag, 33)

    trace = []
    for step in range(32):
        # Shift (r, q) left together
        r = shifter(r, 1, "SLL")
        r[-1] = q[0]            # bring down the next bit from q into r LSB
        q = shifter(q, 1, "SLL")

        # Try subtract: r - d33 using ALU on 33-bit vectors
        r_try, _ = alu(r, d33, "SUB")  # r + (~d33 + 1)

        if r_try[0] == 1:
            # Negative -> restore, set q[LSB] = 0
            q = _set_lsb(q, 0)
            action = "RESTORE"
        else:
            # Accept subtraction, set q[LSB] = 1
            r = r_try
            q = _set_lsb(q, 1)
            action = "SUB"

        # Minimal trace: step + low 32 bits of r and full q
        trace.append(f"step={step:02d} r=0x{_hex32(r[-32:])} q=0x{_hex32(q)} action={action}")

    # Final remainder is low 32 bits of r
    return q, r[-32:], trace

def mdu_div(op: str, rs1_bits: Bits, rs2_bits: Bits) -> Dict[str, object]:
    if op not in ("DIV","DIVU","REM","REMU"):
        raise NotImplementedError(f"Unsupported op: {op}")
    if len(rs1_bits) != 32 or len(rs2_bits) != 32:
        raise ValueError("DIV/REM expect 32-bit inputs")

    dividend = rs1_bits[:]
    divisor  = rs2_bits[:]

    # Divide by zero
    if _is_zero(divisor):
        if op in ("DIV","DIVU"):
            # q = all 1s, r = dividend
            return {"q_bits": [1]*32, "r_bits": dividend, "overflow": 0, "trace": ["div_by_zero"]}
        else:  # REM/REMU
            # remainder = dividend; quotient is not architecturally observed
            return {"q_bits": None, "r_bits": dividend, "overflow": 0, "trace": ["div_by_zero"]}

    # Special INT_MIN / -1 case (signed DIV only)
    INT_MIN = [1] + [0]*31
    NEG_ONE = [1]*32
    if op == "DIV" and _eq_bits(dividend, INT_MIN) and _eq_bits(divisor, NEG_ONE):
        return {"q_bits": INT_MIN[:], "r_bits": zero_bits(32), "overflow": 1, "trace": ["int_min_div_minus1"]}
    if op == "REM" and _eq_bits(dividend, INT_MIN) and _eq_bits(divisor, NEG_ONE):
        return {"q_bits": None, "r_bits": zero_bits(32), "overflow": 0, "trace": ["int_min_div_minus1"]}

    # Prepare magnitudes
    if op in ("DIVU","REMU"):
        a_mag, a_neg = dividend[:], 0
        b_mag, b_neg = divisor[:],  0
    else:
        a_mag, a_neg = _abs_bits(dividend)
        b_mag, b_neg = _abs_bits(divisor)

    # Core unsigned division
    q_mag, r_mag, trace = _restoring_div_unsigned(a_mag, b_mag)

    # Apply signs for signed ops
    if op in ("DIVU","REMU"):
        q_bits = q_mag
        r_bits = r_mag
        overflow = 0
    else:
        q_neg = 1 if (a_neg ^ b_neg) else 0
        r_neg = a_neg  # remainder follows dividend sign
        q_bits = q_mag[:] if q_neg == 0 else twos_complement_negate(q_mag)
        r_bits = r_mag[:] if r_neg == 0 else twos_complement_negate(r_mag)
        overflow = 0

    return {"q_bits": q_bits, "r_bits": r_bits, "overflow": overflow, "trace": trace}
