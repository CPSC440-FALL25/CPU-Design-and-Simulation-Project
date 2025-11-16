"""
Ttest for RISC-V Instruction Decoder
Tests essential functionality with test_base.hex instructions
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.instruction_decoder import InstructionDecoder, InstructionType


class TestInstructionDecoder(unittest.TestCase):
    
    def setUp(self):
        self.decoder = InstructionDecoder()
    
    def test_essential_instructions(self):
        """Test essential instruction types from test_base.hex"""
        test_cases = [
            (0x00500093, 'ADDI', InstructionType.I_TYPE),   # ADDI x1, x0, 5
            (0x002081B3, 'ADD', InstructionType.R_TYPE),    # ADD x3, x1, x2
            (0x40110233, 'SUB', InstructionType.R_TYPE),    # SUB x4, x2, x1
            (0x000102B7, 'LUI', InstructionType.U_TYPE),    # LUI x5, 16
            (0x0032A023, 'SW', InstructionType.S_TYPE),     # SW x3, 0(x5)
            (0x0002A203, 'LW', InstructionType.I_TYPE),     # LW x4, 0(x5)
            (0x00418463, 'BEQ', InstructionType.B_TYPE),    # BEQ x3, x4, 8
            (0x0000006F, 'JAL', InstructionType.J_TYPE),    # JAL x0, 0
        ]
        
        for instruction, exp_op, exp_type in test_cases:
            with self.subTest(instruction=hex(instruction)):
                decoded = self.decoder.decode(instruction)
                self.assertEqual(decoded['operation'], exp_op)
                self.assertEqual(decoded['instruction_type'], exp_type)
    
    def test_format_instruction(self):
        """Test instruction formatting"""
        decoded = self.decoder.decode(0x00500093)  # ADDI x1, x0, 5
        formatted = self.decoder.format_instruction(decoded)
        self.assertEqual(formatted, "ADDI x1, x0, 5")


if __name__ == '__main__':
    unittest.main()