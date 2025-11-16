
"""
Simple ALU that works on explicit bit-vectors (MSB-first).

Implements ADD and SUB using a ripple-carry adder built from logic gates.
Surfaces standard flags: N (negative), Z (zero), C (carry out of MSB), V (signed overflow).
"""

from typing import Dict, Literal, Tuple
from bitvec import Bits, add_rca, twos_complement_negate, is_negative, zero_bits

ALUOp = Literal["ADD","SUB"]

def _flags(result: Bits, carry_out: int, a: Bits, b: Bits, op: ALUOp) -> Dict[str, int]:
    N = 1 if is_negative(result) else 0
    Z = 1 if all(bit == 0 for bit in result) else 0
    C = 1 if carry_out == 1 else 0

    # Signed overflow V (two's-complement rule)
    a_sign = 1 if a[0] == 1 else 0
    b_sign = 1 if b[0] == 1 else 0
    r_sign = 1 if result[0] == 1 else 0

    if op == "ADD":
        V = 1 if (a_sign == b_sign and r_sign != a_sign) else 0
    else:  # SUB: a + (~b + 1); overflow iff sign(a) != sign(b) and sign(result) != sign(a)
        V = 1 if (a_sign != b_sign and r_sign != a_sign) else 0

    return {"N": N, "Z": Z, "C": C, "V": V}

def alu(a: Bits, b: Bits, op: ALUOp) -> Tuple[Bits, Dict[str, int]]:
    if len(a) != len(b):
        raise ValueError("width mismatch")
    if op not in ("ADD","SUB"):
        raise ValueError("unsupported op")

    if op == "ADD":
        res, cout = add_rca(a, b, 0)
        flags = _flags(res, cout, a, b, "ADD")
        return res, flags

    # SUB = a + (-b)
    minus_b = twos_complement_negate(b)
    res, cout = add_rca(a, minus_b, 0)
    flags = _flags(res, cout, a, b, "SUB")
    return res, flags

def flags_from_result(a: Bits, b: Bits, res: Bits, carry_out: int, op: ALUOp):
    return _flags(res, carry_out, a, b, op)
