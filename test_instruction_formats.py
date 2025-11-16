"""
Simplified Instruction Format Tests - 4 Essential Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.instruction_decoder import InstructionDecoder, InstructionType, ExtensionType

class TestInstructionFormats(unittest.TestCase):
    def setUp(self):
        self.decoder = InstructionDecoder()
    
    def test_r_type_instructions(self):
        """Test R-type instruction decoding"""
        # ADD x1, x2, x3
        instruction = 0x003100B3
        decoded = self.decoder.decode(instruction)
        
        self.assertEqual(decoded['instruction_type'], InstructionType.R_TYPE)
        self.assertEqual(decoded['operation'], "ADD")
        self.assertEqual(decoded['rs1'], 2)
        self.assertEqual(decoded['rs2'], 3)
        self.assertEqual(decoded['rd'], 1)
    
    def test_i_type_instructions(self):
        """Test I-type instruction decoding"""
        # ADDI x1, x0, 5
        instruction = 0x00500093
        decoded = self.decoder.decode(instruction)
        
        self.assertEqual(decoded['instruction_type'], InstructionType.I_TYPE)
        self.assertEqual(decoded['operation'], "ADDI")
        self.assertEqual(decoded['rs1'], 0)
        self.assertEqual(decoded['rd'], 1)
        self.assertEqual(decoded['immediate'], 5)
    
    def test_s_type_instructions(self):
        """Test S-type instruction decoding"""
        # SW x1, 0(x0)
        instruction = 0x00102023
        decoded = self.decoder.decode(instruction)
        
        self.assertEqual(decoded['instruction_type'], InstructionType.S_TYPE)
        self.assertEqual(decoded['operation'], "SW")
        self.assertEqual(decoded['rs1'], 0)
        self.assertEqual(decoded['rs2'], 1)
        self.assertEqual(decoded['immediate'], 0)
    
    def test_b_type_instructions(self):
        """Test B-type instruction decoding"""
        # BEQ x1, x2, 0
        instruction = 0x00208063
        decoded = self.decoder.decode(instruction)
        
        self.assertEqual(decoded['instruction_type'], InstructionType.B_TYPE)
        self.assertEqual(decoded['operation'], "BEQ")
        self.assertEqual(decoded['rs1'], 1)
        self.assertEqual(decoded['rs2'], 2)
        self.assertEqual(decoded['immediate'], 0)

if __name__ == '__main__':
    unittest.main()