"""
Two's-Complement toolkit (RV32) implemented with explicit bit-vectors and string math only.

Public API:
    encode_twos_complement(value) -> { 'bin': str, 'hex': str, 'overflow': 0/1 }
       - value may be int or decimal string; negatives start with '-'.
       - width fixed to 32.

    decode_twos_complement(bits) -> { 'value_str': str, 'sign': -1|0|+1 }
       - bits may be '0'/'1' string (underscores ok) or list of 0/1.
       - returns decimal string (tests can do int(value_str) if needed).

    sign_extend(bits, src_width, dst_width) -> list[0/1]
    zero_extend(bits, src_width, dst_width) -> list[0/1]
"""

from typing import List, Tuple, Dict, Union
from bitvec import Bits, zero_bits, add_rca, twos_complement_negate, bits_to_hex, bits_to_str

# Utilities: bit parsing/normalization

def _bits_from_str_or_list(x: Union[str, List[int]]) -> Bits:
    if isinstance(x, list):
        for b in x:
            if b not in (0, 1):
                raise ValueError("bits list must contain 0/1")
        return [int(b) for b in x]
    if isinstance(x, str):
        s = x.replace("_", "").strip()
        if not s or any(ch not in "01" for ch in s):
            raise ValueError("bits string must be only 0/1")
        return [1 if ch == "1" else 0 for ch in s]
    raise TypeError("bits must be str or list[0/1]")

def _pad_or_trim_32(bits: Bits) -> Bits:
    if len(bits) > 32:
        return bits[-32:]
    if len(bits) < 32:
        return [0] * (32 - len(bits)) + bits[:]
    return bits[:]

# Decimal-string helpers

def _strip_zeros(s: str) -> str:
    i, n = 0, len(s)
    while i < n - 1 and s[i] == '0':
        i += 1
    return s[i:]

# multiply-by-2 table per digit with incoming carry (0/1) -> (out_digit_char, carry_out)
_MUL2 = {
    # carry 0
    ('0','0'):('0',0), ('1','0'):('2',0), ('2','0'):('4',0), ('3','0'):('6',0), ('4','0'):('8',0),
    ('5','0'):('0',1), ('6','0'):('2',1), ('7','0'):('4',1), ('8','0'):('6',1), ('9','0'):('8',1),
    # carry 1  (means +1 from previous column)
    ('0','1'):('1',0), ('1','1'):('3',0), ('2','1'):('5',0), ('3','1'):('7',0), ('4','1'):('9',0),
    ('5','1'):('1',1), ('6','1'):('3',1), ('7','1'):('5',1), ('8','1'):('7',1), ('9','1'):('9',1),
}

# division-by-2 per digit with incoming remainder r (0/1) -> (quot_digit_char, r_out)
_DIV2 = {
    # r = 0
    (0,'0'):('0',0), (0,'1'):('0',1), (0,'2'):('1',0), (0,'3'):('1',1), (0,'4'):('2',0),
    (0,'5'):('2',1), (0,'6'):('3',0), (0,'7'):('3',1), (0,'8'):('4',0), (0,'9'):('4',1),
    # r = 1 (we had +10 from previous column)
    (1,'0'):('5',0), (1,'1'):('5',1), (1,'2'):('6',0), (1,'3'):('6',1), (1,'4'):('7',0),
    (1,'5'):('7',1), (1,'6'):('8',0), (1,'7'):('8',1), (1,'8'):('9',0), (1,'9'):('9',1),
}

# add carry (0/1) to a decimal digit -> (new_digit_char, new_carry)
_ADD_CARRY = {
    # carry 0: identity
    ('0',0):('0',0), ('1',0):('1',0), ('2',0):('2',0), ('3',0):('3',0), ('4',0):('4',0),
    ('5',0):('5',0), ('6',0):('6',0), ('7',0):('7',0), ('8',0):('8',0), ('9',0):('9',0),
    # carry 1: increment with wrap
    ('0',1):('1',0), ('1',1):('2',0), ('2',1):('3',0), ('3',1):('4',0), ('4',1):('5',0),
    ('5',1):('6',0), ('6',1):('7',0), ('7',1):('8',0), ('8',1):('9',0), ('9',1):('0',1),
}

def _dec_div2(dec: str) -> Tuple[str, int]:
    """Return (quotient_str, remainder_bit) for dec // 2 and dec % 2 using tables only."""
    dec = _strip_zeros(dec)
    rem = 0
    out = []
    for ch in dec:
        qd, rem = _DIV2[(rem, ch)]
        out.append(qd)
    return _strip_zeros("".join(out)), rem

def _dec_mul2(dec: str) -> str:
    dec = _strip_zeros(dec)
    carry = 0
    out = []
    for ch in reversed(dec):
        od, carry = _MUL2[(ch, str(carry))]
        out.append(od)
    if carry == 1:
        out.append('1')
    return _strip_zeros("".join(reversed(out)))

def _dec_add_small(dec: str, add_one: int) -> str:
    """Add 0 or 1 to decimal string using carry table only."""
    carry = 1 if add_one == 1 else 0
    out = []
    for ch in reversed(_strip_zeros(dec)):
        od, carry = _ADD_CARRY[(ch, carry)]
        out.append(od)
    if carry == 1:
        out.append('1')
    return _strip_zeros("".join(reversed(out)))

def _dec_compare(a: str, b: str) -> int:
    """Return -1 if a<b, 0 if a==b, 1 if a>b for positive decimal strings."""
    a = _strip_zeros(a); b = _strip_zeros(b)
    if len(a) < len(b): return -1
    if len(a) > len(b): return 1
    if a == b: return 0
    return -1 if a < b else 1

# Conversions between decimal string and 32-bit Bits

def _dec_to_u32_bits(dec: str) -> Bits:
    """Convert unsigned decimal string to 32-bit bit vector via repeated //2 and %2."""
    q = _strip_zeros(dec)
    if q == '0':
        return [0]*32
    bits_rev = []
    # keep extracting remainders until quotient is zero
    for _ in range(128):  # generous guard
        q, r = _dec_div2(q)
        bits_rev.append(r)
        if q == '0':
            break
    bits = list(reversed(bits_rev))
    if len(bits) < 32:
        bits = [0]*(32 - len(bits)) + bits
    elif len(bits) > 32:
        bits = bits[-32:]
    return bits

def _u32_bits_to_dec(bits: Bits) -> str:
    """Convert unsigned 32-bit bit vector to decimal string via *2 then +bit."""
    s = '0'
    for b in bits:
        s = _dec_mul2(s)
        if b == 1:
            s = _dec_add_small(s, 1)
    return _strip_zeros(s)

# Public API

def sign_extend(bits: Bits, src_width: int, dst_width: int) -> Bits:
    if dst_width < src_width:
        return bits[-dst_width:]
    sign = bits[0] if len(bits) >= 1 else 0
    return [sign]*(dst_width - src_width) + bits[-src_width:]

def zero_extend(bits: Bits, src_width: int, dst_width: int) -> Bits:
    if dst_width < src_width:
        return bits[-dst_width:]
    return [0]*(dst_width - src_width) + bits[-src_width:]

def truncate_bits(value: int, to_bits: int) -> int:
    """
    Keep only the lowest `to_bits` bits of `value`.
    Examples:
      truncate_bits(0b11110101, 4) -> 0b0101
    """
    if to_bits <= 0:
        raise ValueError("Bit width must be positive")
    mask = (1 << to_bits) - 1
    return value & mask


def encode_twos_complement(value: Union[int, str]) -> Dict[str, Union[str, int]]:
    """Encode signed decimal value to 32-bit two's-complement.
    Returns {'bin': <nibble-grouped bits>, 'hex': '0x........', 'overflow': 0/1}.
    """
    # normalize to decimal string
    if isinstance(value, int):
        dec = str(value)
    elif isinstance(value, str):
        dec = value.strip()
    else:
        raise TypeError("value must be int or decimal string")

    neg = dec.startswith('-')
    mag = dec[1:] if neg else dec
    if mag == '': mag = '0'
    mag = _strip_zeros(mag)

    # Range checks
    MAX_POS = '2147483647'
    MAX_NEG_MAG = '2147483648'
    overflow = 0
    if neg:
        if _dec_compare(mag, MAX_NEG_MAG) == 1:
            overflow = 1
    else:
        if _dec_compare(mag, MAX_POS) == 1:
            overflow = 1

    # Build 32-bit pattern
    mag_bits = _dec_to_u32_bits(mag)   # unsigned magnitude
    bits32 = twos_complement_negate(mag_bits) if neg else mag_bits
    bits32 = _pad_or_trim_32(bits32)

    return {
        'bin': bits_to_str(bits32),
        'hex': '0x' + bits_to_hex(bits32)[-8:],
        'overflow': overflow,
    }

def decode_twos_complement(bits: Union[str, List[int]]) -> Dict[str, Union[str, int]]:
    """Decode a 32-bit two's-complement bit pattern into a signed decimal *string*.
    Returns {'value_str': <decimal string>, 'sign': -1|0|+1}.
    """
    b = _pad_or_trim_32(_bits_from_str_or_list(bits))
    if b == [0]*32:
        return {'value_str': '0', 'sign': 0}
    if b[0] == 1:
        mag = twos_complement_negate(b)
        return {'value_str': '-' + _u32_bits_to_dec(mag), 'sign': -1}
    else:
        return {'value_str': _u32_bits_to_dec(b), 'sign': +1}
