
"""
Logical/arithmetical shifter implemented without << or >>.

- SLL: shift left logical, fill with 0s
- SRL: shift right logical, fill with 0s
- SRA: shift right arithmetic, fill with sign bit (replication)
"""

from typing import Literal, List
from bitvec import Bits

ShiftOp = Literal["SLL","SRL","SRA"]

def _shift_once(bits: Bits, op: ShiftOp) -> Bits:
    w = len(bits)
    if op == "SLL":
        return bits[1:] + [0]
    elif op == "SRL":
        return [0] + bits[:-1]
    else: # SRA
        sign = bits[0]
        return [sign] + bits[:-1]

def shifter(bits: Bits, shamt: int, op: ShiftOp) -> Bits:
    if shamt < 0:
        raise ValueError("shamt must be non-negative")
    out = bits[:]
    # iterate one-by-one; a barrel shifter is optional later
    for _ in range(shamt):
        out = _shift_once(out, op)
    return out
