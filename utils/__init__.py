"""
Utility modules for RISC-V CPU implementation
Contains bit-vector operations and arithmetic units
"""

from .bitvec import Bits, zero_bits, left_pad, add_rca, bits_to_hex
from .alu import alu
from .mdu import mdu_mul
from .mdu_div import mdu_div
from .shifter import shifter
from .twos_complement import encode_twos_complement, decode_twos_complement, sign_extend, zero_extend

__all__ = [
    'Bits', 'zero_bits', 'left_pad', 'add_rca', 'bits_to_hex',
    'alu', 'mdu_mul', 'mdu_div', 'shifter',
    'encode_twos_complement', 'decode_twos_complement', 'sign_extend', 'zero_extend'
]