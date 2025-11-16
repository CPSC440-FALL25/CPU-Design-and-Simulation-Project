"""
RISC-V ALU Integration
Uses utils utilities for all arithmetic operations
Provides unified interface for single-cycle CPU datapath
"""

from typing import Dict, Tuple, Optional
from utils import Bits, zero_bits, left_pad, alu, mdu_mul, mdu_div, shifter
from .control_unit import ALUOperation


class IntegratedALU:
    """
    Integrated ALU using utils utilities
    Supports RV32I base + M extension operations
    """
    
    def __init__(self):
        pass
    
    def execute(self, operation: ALUOperation, operand_a: Bits, operand_b: Bits) -> Tuple[Bits, Dict[str, int]]:
        """
        Execute ALU operation and return result + flags
        
        Args:
            operation: ALU operation to perform
            operand_a: First operand (32-bit)
            operand_b: Second operand (32-bit)
            
        Returns:
            Tuple of (result_bits, flags_dict)
            flags_dict contains: N, Z, C, V flags
        """
        # Ensure operands are 32 bits
        if len(operand_a) != 32:
            operand_a = left_pad(operand_a, 32, 0)
        if len(operand_b) != 32:
            operand_b = left_pad(operand_b, 32, 0)
        
        # Initialize default flags
        flags = {"N": 0, "Z": 0, "C": 0, "V": 0}
        
        if operation == ALUOperation.ADD:
            result, flags = alu(operand_a, operand_b, "ADD")
            
        elif operation == ALUOperation.SUB:
            result, flags = alu(operand_a, operand_b, "SUB")
            
        elif operation == ALUOperation.AND:
            result = self._bitwise_and(operand_a, operand_b)
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.OR:
            result = self._bitwise_or(operand_a, operand_b)
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.XOR:
            result = self._bitwise_xor(operand_a, operand_b)
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.SLL:
            # Shift amount is bottom 5 bits of operand_b
            shift_amount = self._extract_shift_amount(operand_b)
            result = shifter(operand_a, shift_amount, "SLL")
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.SRL:
            shift_amount = self._extract_shift_amount(operand_b)
            result = shifter(operand_a, shift_amount, "SRL")
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.SRA:
            shift_amount = self._extract_shift_amount(operand_b)
            result = shifter(operand_a, shift_amount, "SRA")
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.SLT:
            # Set if operand_a < operand_b (signed)
            result = self._set_less_than_signed(operand_a, operand_b)
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.SLTU:
            # Set if operand_a < operand_b (unsigned)
            result = self._set_less_than_unsigned(operand_a, operand_b)
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.MUL:
            # 32x32 -> 32 multiply
            mdu_result = mdu_mul("MUL", operand_a, operand_b)
            result = mdu_result["rd_bits"]
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.DIV:
            # Division - determine signed vs unsigned based on operation
            div_result = mdu_div("DIV", operand_a, operand_b)
            result = div_result["q_bits"]
            flags = self._compute_logic_flags(result)
            flags["V"] = div_result["overflow"]  # Set overflow flag
            
        elif operation == ALUOperation.REM:
            # Remainder
            rem_result = mdu_div("REM", operand_a, operand_b)
            result = rem_result["r_bits"]
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.PASS_A:
            result = operand_a[:]
            flags = self._compute_logic_flags(result)
            
        elif operation == ALUOperation.PASS_B:
            result = operand_b[:]
            flags = self._compute_logic_flags(result)
            
        else:
            raise ValueError(f"Unsupported ALU operation: {operation}")
        
        return result, flags
    
    def _bitwise_and(self, a: Bits, b: Bits) -> Bits:
        """Bitwise AND operation"""
        return [a[i] & b[i] for i in range(len(a))]
    
    def _bitwise_or(self, a: Bits, b: Bits) -> Bits:
        """Bitwise OR operation"""
        return [a[i] | b[i] for i in range(len(a))]
    
    def _bitwise_xor(self, a: Bits, b: Bits) -> Bits:
        """Bitwise XOR operation"""
        return [a[i] ^ b[i] for i in range(len(a))]
    
    def _extract_shift_amount(self, operand: Bits) -> int:
        """Extract 5-bit shift amount from operand"""
        # Bottom 5 bits
        shift_bits = operand[27:32]  # Bits 4:0
        shift_amount = 0
        for bit in shift_bits:
            shift_amount = (shift_amount << 1) | bit
        return shift_amount
    
    def _set_less_than_signed(self, a: Bits, b: Bits) -> Bits:
        """Set if a < b (signed comparison)"""
        # Use SUB operation and check sign
        result, flags = alu(a, b, "SUB")
        # If result is negative, then a < b
        is_less = flags["N"]
        return [0] * 31 + [is_less]
    
    def _set_less_than_unsigned(self, a: Bits, b: Bits) -> Bits:
        """Set if a < b (unsigned comparison)"""
        # Convert to unsigned integers for comparison
        a_val = 0
        b_val = 0
        for bit in a:
            a_val = (a_val << 1) | bit
        for bit in b:
            b_val = (b_val << 1) | bit
        
        is_less = 1 if a_val < b_val else 0
        return [0] * 31 + [is_less]
    
    def _compute_logic_flags(self, result: Bits) -> Dict[str, int]:
        """Compute N and Z flags for logic operations"""
        flags = {"N": 0, "Z": 0, "C": 0, "V": 0}
        
        # N flag: result is negative (MSB = 1)
        flags["N"] = result[0]
        
        # Z flag: result is zero
        flags["Z"] = 1 if all(bit == 0 for bit in result) else 0
        
        return flags
    
    def execute_branch_compare(self, operation: str, operand_a: Bits, operand_b: Bits) -> bool:
        """
        Execute branch comparison operations
        Returns True if branch should be taken
        """
        if operation == "BEQ":
            # Branch if equal
            result, _ = alu(operand_a, operand_b, "SUB")
            return all(bit == 0 for bit in result)
            
        elif operation == "BNE":
            # Branch if not equal
            result, _ = alu(operand_a, operand_b, "SUB")
            return not all(bit == 0 for bit in result)
            
        elif operation == "BLT":
            # Branch if less than (signed)
            _, flags = alu(operand_a, operand_b, "SUB")
            return bool(flags["N"])
            
        elif operation == "BGE":
            # Branch if greater than or equal (signed)
            _, flags = alu(operand_a, operand_b, "SUB")
            return not bool(flags["N"])
            
        elif operation == "BLTU":
            # Branch if less than (unsigned)
            # Convert to unsigned for comparison
            a_val = sum(bit << (31-i) for i, bit in enumerate(operand_a))
            b_val = sum(bit << (31-i) for i, bit in enumerate(operand_b))
            return a_val < b_val
            
        elif operation == "BGEU":
            # Branch if greater than or equal (unsigned)
            a_val = sum(bit << (31-i) for i, bit in enumerate(operand_a))
            b_val = sum(bit << (31-i) for i, bit in enumerate(operand_b))
            return a_val >= b_val
            
        else:
            raise ValueError(f"Unsupported branch operation: {operation}")
