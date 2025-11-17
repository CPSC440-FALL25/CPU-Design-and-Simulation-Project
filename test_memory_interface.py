"""
Simplified Memory Interface Tests - 4 Essential Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.memory_interface import MemoryInterface
# Use utility functions directly in the test class

class TestMemoryInterface(unittest.TestCase):
    def setUp(self):
        self.memory = MemoryInterface()
    
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
    
    def test_memory_initialization(self):
        """Test memory initializes to zero"""
        # Check various memory locations
        for addr in [0x0, 0x100, 0x1000, 0x2000]:
            addr_bits = self._int_to_bits(addr, 32)
            result = self.memory.load_word(addr_bits)
            self.assertEqual(self._bits_to_int(result), 0)
    
    def test_word_operations(self):
        """Test word store and load operations"""
        address = 0x1000
        test_values = [0x12345678, 0xABCDEF00, 0x7FFFFFFF, 0x80000000]
        
        for value in test_values:
            addr_bits = self._int_to_bits(address, 32)
            value_bits = self._int_to_bits(value, 32)
            self.memory.store_word(addr_bits, value_bits)
            loaded_bits = self.memory.load_word(addr_bits)
            loaded_value = self._bits_to_int(loaded_bits)
            self.assertEqual(loaded_value, value)
            address += 4
    
    def test_byte_operations(self):
        """Test byte store and load operations"""
        address = 0x2000
        test_values = [0x12, 0xAB, 0x7F, 0x80]
        
        for value in test_values:
            addr_bits = self._int_to_bits(address, 32)
            # Store_byte expects 32-bit data, takes bottom 8 bits
            value_bits = self._int_to_bits(value, 32)
            self.memory.store_byte(addr_bits, value_bits)
            loaded_bits = self.memory.load_byte(addr_bits, True)
            loaded_value = self._bits_to_int(loaded_bits)
            self.assertEqual(loaded_value, value)
            address += 1
    
    def test_memory_independence(self):
        """Test that different memory locations are independent"""
        # Store different values at different addresses
        addresses = [0x1000, 0x1004, 0x1008, 0x100C]
        values = [0x11111111, 0x22222222, 0x33333333, 0x44444444]
        
        for addr, value in zip(addresses, values):
            addr_bits = self._int_to_bits(addr, 32)
            value_bits = self._int_to_bits(value, 32)
            self.memory.store_word(addr_bits, value_bits)
        
        # Verify each location has the correct value
        for addr, expected_value in zip(addresses, values):
            addr_bits = self._int_to_bits(addr, 32)
            loaded_bits = self.memory.load_word(addr_bits)
            loaded_value = self._bits_to_int(loaded_bits)
            self.assertEqual(loaded_value, expected_value)

if __name__ == '__main__':
    unittest.main()