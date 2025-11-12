
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from bitvec import bits_from_str, bits_to_str
from shifter import shifter

def test_sll_srl_sra():
    x = bits_from_str('1001')  # -7 in 4-bit? (not relevant), just shape
    assert bits_to_str(shifter(x,1,"SLL"),0) == '0010'
    assert bits_to_str(shifter(x,1,"SRL"),0) == '0100'
    assert bits_to_str(shifter(x,1,"SRA"),0) == '1100'

def test_multi_shifts():
    x = bits_from_str('00000000000000000000000000001101')  # 13
    # Expect full nibble-grouping across 32 bits:
    assert bits_to_str(shifter(x,2,"SLL")) == '0000_0000_0000_0000_0000_0000_0011_0100'
    assert bits_to_str(shifter(x,2,"SRL")) == '0000_0000_0000_0000_0000_0000_0000_0011'

