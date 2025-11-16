"""
Simplified Integrated ALU Tests - 4 Essential Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.integrated_alu import IntegratedALU
from core.control_unit import ALUOperation
# Use utility functions directly in the test class

class TestIntegratedALU(unittest.TestCase):
    def setUp(self):
        self.alu = IntegratedALU()
    
    def _int_to_bits(self, value: int, width: int = 32):
        """Convert integer to bits"""
        bits = []
        for i in range(width-1, -1, -1):
            bits.append((value >> i) & 1)
        return bits
    
    def _bits_to_int(self, bits):
        """Convert bits to integer"""
        result = 0
        for bit in bits:
            result = (result << 1) | bit
        return result
    
    def test_arithmetic_operations(self):
        """Test basic arithmetic operations"""
        # Test addition
        a_bits = self._int_to_bits(10, 32)
        b_bits = self._int_to_bits(5, 32)
        result, flags = self.alu.execute(ALUOperation.ADD, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 15)
        
        # Test subtraction
        a_bits = self._int_to_bits(10, 32)
        b_bits = self._int_to_bits(3, 32)
        result, flags = self.alu.execute(ALUOperation.SUB, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 7)
    
    def test_logical_operations(self):
        """Test logical operations"""
        # Test AND
        a_bits = self._int_to_bits(0b1100, 32)
        b_bits = self._int_to_bits(0b1010, 32)
        result, flags = self.alu.execute(ALUOperation.AND, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 0b1000)
        
        # Test OR
        result, flags = self.alu.execute(ALUOperation.OR, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 0b1110)
        
        # Test XOR
        result, flags = self.alu.execute(ALUOperation.XOR, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 0b0110)
    
    def test_shift_operations(self):
        """Test shift operations"""
        # Test shift left logical
        a_bits = self._int_to_bits(5, 32)
        b_bits = self._int_to_bits(2, 32)
        result, flags = self.alu.execute(ALUOperation.SLL, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 20)
        
        # Test shift right logical
        a_bits = self._int_to_bits(20, 32)
        b_bits = self._int_to_bits(2, 32)
        result, flags = self.alu.execute(ALUOperation.SRL, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 5)
    
    def test_comparison_operations(self):
        """Test comparison operations"""
        # Test set less than
        a_bits = self._int_to_bits(5, 32)
        b_bits = self._int_to_bits(10, 32)
        result, flags = self.alu.execute(ALUOperation.SLT, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 1)  # 5 < 10 is true
        
        a_bits = self._int_to_bits(10, 32)
        b_bits = self._int_to_bits(5, 32)
        result, flags = self.alu.execute(ALUOperation.SLT, a_bits, b_bits)
        self.assertEqual(self._bits_to_int(result), 0)  # 10 < 5 is false

if __name__ == '__main__':
    unittest.main()