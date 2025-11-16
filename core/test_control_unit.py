"""
Minimal test for RISC-V Control Unit
Tests essential control signal generation
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.control_unit import ControlUnit, ALUOperation


class TestControlUnit(unittest.TestCase):
    
    def setUp(self):
        self.control_unit = ControlUnit()
    
    def test_essential_control_signals(self):
        """Test control signal generation for essential instructions"""
        test_cases = [
            # (instruction, reg_write, alu_src_b, mem_read, mem_write, branch, jump, alu_op)
            (0x00500093, True, True, False, False, False, False, ALUOperation.ADD),    # ADDI
            (0x002081B3, True, False, False, False, False, False, ALUOperation.ADD),   # ADD
            (0x40110233, True, False, False, False, False, False, ALUOperation.SUB),   # SUB
            (0x000102B7, True, True, False, False, False, False, ALUOperation.PASS_B), # LUI
            (0x0032A023, False, True, False, True, False, False, ALUOperation.ADD),    # SW
            (0x0002A203, True, True, True, False, False, False, ALUOperation.ADD),     # LW
            (0x00418463, False, False, False, False, True, False, ALUOperation.SUB),   # BEQ
            (0x0000006F, True, True, False, False, False, True, ALUOperation.PASS_B),  # JAL
        ]
        
        for instruction, exp_reg_write, exp_alu_src_b, exp_mem_read, exp_mem_write, exp_branch, exp_jump, exp_alu_op in test_cases:
            with self.subTest(instruction=hex(instruction)):
                decoded, control = self.control_unit.decode_and_control(instruction)
                
                self.assertEqual(control.reg_write, exp_reg_write, f"reg_write mismatch for {decoded['operation']}")
                self.assertEqual(control.alu_src_b, exp_alu_src_b, f"alu_src_b mismatch for {decoded['operation']}")
                self.assertEqual(control.mem_read, exp_mem_read, f"mem_read mismatch for {decoded['operation']}")
                self.assertEqual(control.mem_write, exp_mem_write, f"mem_write mismatch for {decoded['operation']}")
                self.assertEqual(control.branch, exp_branch, f"branch mismatch for {decoded['operation']}")
                self.assertEqual(control.jump, exp_jump, f"jump mismatch for {decoded['operation']}")
                self.assertEqual(control.alu_op, exp_alu_op, f"alu_op mismatch for {decoded['operation']}")
    
    def test_decode_and_control_integration(self):
        """Test integrated decode and control functionality"""
        instruction = 0x00500093  # ADDI x1, x0, 5
        decoded, control = self.control_unit.decode_and_control(instruction)
        
        # Verify decoder output
        self.assertEqual(decoded['operation'], 'ADDI')
        self.assertEqual(decoded['rd'], 1)
        self.assertEqual(decoded['rs1'], 0)
        self.assertEqual(decoded['immediate'], 5)
        
        # Verify control signals
        self.assertTrue(control.reg_write)
        self.assertTrue(control.alu_src_b)
        self.assertFalse(control.mem_read)
        self.assertFalse(control.mem_write)
        self.assertEqual(control.alu_op, ALUOperation.ADD)


if __name__ == '__main__':
    unittest.main()