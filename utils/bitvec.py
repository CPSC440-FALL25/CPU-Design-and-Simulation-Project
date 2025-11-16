
"""
Bit-vector utilities implemented with explicit bits and boolean logic only.

- Bits are represented as lists of ints 0/1, MSB-first (index 0 is the sign bit for 32-bit).
- No use of host-language arithmetic operators (+ - * / % << >>) inside this module.
- Conversions to/from hex are done via manual nibble lookups (no hex()/format()).
"""

from typing import List, Tuple

Bit = int  # 0 or 1
Bits = List[Bit]  # MSB-first representation

def _assert_bits(bits: Bits) -> None:
    if not isinstance(bits, list) or not all(b in (0,1) for b in bits):
        raise TypeError("bits must be a list of 0/1 ints")
    if len(bits) == 0:
        raise ValueError("bits must be non-empty")

def zero_bits(width: int) -> Bits:
    if width <= 0:
        raise ValueError("width must be positive")
    return [0] * width

def one_bits(width: int) -> Bits:
    if width <= 0:
        raise ValueError("width must be positive")
    return [1] * width

def left_pad(bits: Bits, width: int, fill: Bit = 0) -> Bits:
    _assert_bits(bits)
    if width < len(bits):
        raise ValueError("width smaller than bits length for left_pad")
    return [fill] * (width - len(bits)) + bits[:]

def trim_width(bits: Bits, width: int) -> Bits:
    _assert_bits(bits)
    if width <= 0:
        raise ValueError("width must be positive")
    # Keep the rightmost 'width' bits (LSBs), then re-pad to width by dropping MSBs
    return bits[-width:]

def bits_from_str(s: str) -> Bits:
    """Create bits from a string like '0001_1010' (underscores allowed)."""
    s = s.replace("_", "").strip()
    if not s or any(ch not in "01" for ch in s):
        raise ValueError("binary string must contain only 0/1")
    return [1 if ch == "1" else 0 for ch in s]

def bits_to_str(bits: Bits, group: int = 4) -> str:
    """Pretty MSB-first string with underscores every 'group' bits."""
    _assert_bits(bits)
    out = "".join("1" if b else "0" for b in bits)
    if group > 0:
        parts = []
        # group from rightmost side for nibble alignment
        for i in range(len(out), 0, -group):
            start = max(0, i - group)
            parts.append(out[start:i])
        return "_".join(reversed(parts))
    return out

_HEX_LUT = {
    "0000": "0","0001": "1","0010": "2","0011": "3",
    "0100": "4","0101": "5","0110": "6","0111": "7",
    "1000": "8","1001": "9","1010": "A","1011": "B",
    "1100": "C","1101": "D","1110": "E","1111": "F",
}

def bits_to_hex(bits: Bits, width_multiple: int = 4) -> str:
    """Return zero-padded uppercase hex string without '0x' (manual lookup)."""
    _assert_bits(bits)
    # Left-pad to nibble boundary
    rem = len(bits) % width_multiple
    pad = 0 if rem == 0 else (width_multiple - rem)
    padded = [0]*pad + bits[:]
    out_chars = []
    for i in range(0, len(padded), 4):
        nibble = "".join("1" if b else "0" for b in padded[i:i+4])
        out_chars.append(_HEX_LUT[nibble])
    return "".join(out_chars)

def invert_bits(bits: Bits) -> Bits:
    _assert_bits(bits)
    return [1 - b for b in bits]

def _half_adder(a: Bit, b: Bit) -> Tuple[Bit, Bit]:
    """Return (sum, carry)."""
    # sum = a XOR b; carry = a AND b
    s = (a ^ b)  # bool xor on single bits is allowed
    c = (a & b)
    return s, c

def _full_adder(a: Bit, b: Bit, cin: Bit) -> Tuple[Bit, Bit]:
    """Return (sum, carry_out)."""
    s1, c1 = _half_adder(a, b)
    s2, c2 = _half_adder(s1, cin)
    # carry out = (a&b) OR (cin&(a XOR b))
    cout = (c1 | c2)
    return s2, cout

def add_rca(a: Bits, b: Bits, cin: Bit = 0) -> Tuple[Bits, Bit]:
    """
    Ripple-carry add MSB-first bit-vectors a + b + cin.
    Returns (sum_bits, carry_out_of_MSB).
    """
    _assert_bits(a); _assert_bits(b)
    if len(a) != len(b):
        raise ValueError("width mismatch")
    width = len(a)
    # Process from LSB to MSB; our bits are MSB-first
    res = [0] * width
    carry = cin
    for i in range(width-1, -1, -1):
        s, carry = _full_adder(a[i], b[i], carry)
        res[i] = s
    return res, carry

def twos_complement_negate(bits: Bits) -> Bits:
    """Return -bits (two's complement): invert + add 1 via the adder."""
    _assert_bits(bits)
    inv = invert_bits(bits)
    one = zero_bits(len(bits)); one[-1] = 1
    res, _ = add_rca(inv, one, 0)
    return res

def is_negative(bits: Bits) -> bool:
    _assert_bits(bits)
    return bits[0] == 1
