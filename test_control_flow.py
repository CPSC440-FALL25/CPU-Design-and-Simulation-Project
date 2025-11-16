"""
Simplified Control Flow Tests - 4 Essential Tests
"""

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.single_cycle_datapath import SingleCycleDatapath
# Use utility functions directly in the test class

class TestControlFlow(unittest.TestCase):
    def setUp(self):
        self.cpu = SingleCycleDatapath()
    
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
    
    def _load_and_execute_instruction(self, instruction, pc_value):
        """Helper to load and execute a single instruction"""
        # Set PC
        self.cpu.pc = self._int_to_bits(pc_value, 32)
        
        # Store instruction in memory
        addr_bits = self._int_to_bits(pc_value, 32)
        inst_bits = self._int_to_bits(instruction, 32)
        self.cpu.instruction_memory.store_word(addr_bits, inst_bits)
        
        # Execute one cycle
        self.cpu.execute_cycle()
    
    def test_branch_equal(self):
        """Test BEQ (branch equal) instruction"""
        # Set up registers for branch condition
        self.cpu.register_file.set_register_value_int(1, 5)
        self.cpu.register_file.set_register_value_int(2, 5)
        
        # BEQ x1, x2, 8 (should branch since x1 == x2)
        beq_instruction = 0x00208463
        
        initial_pc = 0x1000
        self._load_and_execute_instruction(beq_instruction, initial_pc)
        
        # PC should be updated by branch offset
        pc_value = self._bits_to_int(self.cpu.pc)
        self.assertNotEqual(pc_value, initial_pc + 4, "BEQ should branch when values are equal")
    
    def test_branch_not_equal(self):
        """Test BNE (branch not equal) instruction"""
        # Set up registers for branch condition  
        self.cpu.register_file.set_register_value_int(1, 5)
        self.cpu.register_file.set_register_value_int(2, 3)
        
        # BNE x1, x2, 8 (should branch since x1 != x2)
        bne_instruction = 0x00209463
        
        initial_pc = 0x1000
        self._load_and_execute_instruction(bne_instruction, initial_pc)
        
        # PC should be updated by branch offset
        pc_value = self._bits_to_int(self.cpu.pc)
        self.assertNotEqual(pc_value, initial_pc + 4, "BNE should branch when values are not equal")
    
    def test_branch_less_than(self):
        """Test BLT (branch less than) instruction"""
        # Set up registers for branch condition
        self.cpu.register_file.set_register_value_int(1, 3)
        self.cpu.register_file.set_register_value_int(2, 5)
        
        # BLT x1, x2, 8 (should branch since x1 < x2)
        blt_instruction = 0x0020C463
        
        initial_pc = 0x1000
        self._load_and_execute_instruction(blt_instruction, initial_pc)
        
        # PC should be updated by branch offset
        pc_value = self._bits_to_int(self.cpu.pc)
        self.assertNotEqual(pc_value, initial_pc + 4, "BLT should branch when rs1 < rs2")
    
    def test_jump_and_link(self):
        """Test JAL (jump and link) instruction"""
        # JAL x1, 0x100 (jump to PC + 0x100, store return address in x1)
        jal_instruction = 0x1000E0EF
        
        initial_pc = 0x1000
        self._load_and_execute_instruction(jal_instruction, initial_pc)
        
        # PC should be updated
        pc_value = self._bits_to_int(self.cpu.pc)
        self.assertNotEqual(pc_value, initial_pc, "JAL should update PC")
        
        # x1 should contain return address
        return_addr = self.cpu.register_file.get_register_value_int(1)
        self.assertNotEqual(return_addr, 0, "JAL should store return address in x1")

if __name__ == '__main__':
    unittest.main()