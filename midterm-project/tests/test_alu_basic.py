
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from bitvec import bits_from_str, bits_to_hex, twos_complement_negate
from alu import alu

def hex32(bits):  # helper to pretty-print 32-bit result
    h = bits_to_hex(bits)
    return h[-8:]  # last 8 hex chars

def test_add_overflow_example():
    a = bits_from_str('0' + '1'*31)  # 0x7FFFFFFF
    b = bits_from_str('0'*31 + '1')  # 0x00000001
    res, flags = alu(a,b,"ADD")
    assert hex32(res) == "80000000"
    assert flags == {"N":1,"Z":0,"C":0,"V":1}

def test_sub_overflow_example():
    a = bits_from_str('1' + '0'*31)  # 0x80000000
    b = bits_from_str('0'*31 + '1')  # 0x00000001
    res, flags = alu(a,b,"SUB")
    assert hex32(res) == "7FFFFFFF"
    assert flags == {"N":0,"Z":0,"C":1,"V":1}

def test_add_negatives():
    # -1 + -1 = -2
    neg1 = bits_from_str('1'*32)                # -1 in two's complement
    res, flags = alu(neg1, neg1, "ADD")
    assert hex32(res) == "FFFFFFFE"
    assert flags["V"] == 0 and flags["N"] == 1 and flags["C"] == 1 and flags["Z"] == 0

def test_add_cancel_to_zero():
    # 13 + (-13) = 0
    pos13 = bits_from_str('0'*27 + '01101')
    neg13 = twos_complement_negate(pos13)
    res, flags = alu(pos13, neg13, "ADD")
    assert hex32(res) == "00000000"
    assert flags["Z"] == 1
