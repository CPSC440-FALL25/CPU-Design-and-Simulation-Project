"""
Simplified Register File Tests - 4 Essential Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.register_file import RegisterFile

class TestRegisterFile(unittest.TestCase):
    def setUp(self):
        self.reg_file = RegisterFile()
    
    def test_register_initialization(self):
        """Test that all registers initialize to zero"""
        for i in range(32):
            self.assertEqual(self.reg_file.get_register_value_int(i), 0)
    
    def test_x0_hardwired_zero(self):
        """Test that x0 is always zero regardless of write attempts"""
        # Try to write to x0
        self.reg_file.set_register_value_int(0, 42)
        self.reg_file.set_register_value_int(0, -100)
        # x0 should still be zero
        self.assertEqual(self.reg_file.get_register_value_int(0), 0)
    
    def test_register_read_write(self):
        """Test basic read/write operations"""
        test_values = [1, 0x7FFFFFFF, 42, 100]
        test_registers = [1, 5, 15, 31]
        
        for reg, value in zip(test_registers, test_values):
            self.reg_file.set_register_value_int(reg, value)
            self.assertEqual(self.reg_file.get_register_value_int(reg), value)
    
    def test_register_independence(self):
        """Test that registers are independent"""
        # Set different values in different registers
        self.reg_file.set_register_value_int(1, 100)
        self.reg_file.set_register_value_int(2, 200)
        self.reg_file.set_register_value_int(3, 300)
        
        # Verify each register has the correct value
        self.assertEqual(self.reg_file.get_register_value_int(1), 100)
        self.assertEqual(self.reg_file.get_register_value_int(2), 200)
        self.assertEqual(self.reg_file.get_register_value_int(3), 300)

if __name__ == '__main__':
    unittest.main()