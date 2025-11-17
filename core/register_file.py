"""
RISC-V Register File Implementation
32 registers (x0-x31) with x0 hardwired to zero
Uses utils bit-vector utilities for data representation
"""

from typing import List, Optional
from utils import Bits, zero_bits, left_pad, encode_twos_complement, decode_twos_complement


class RegisterFile:
    def __init__(self):
        # 32 registers, each 32 bits wide
        # Register x0 is hardwired to zero
        self.registers: List[Bits] = [zero_bits(32) for _ in range(32)]
    
    def read_register(self, reg_num: int) -> Bits:
        """
        Read from register reg_num
        Returns 32-bit value as bit vector
        """
        if not (0 <= reg_num <= 31):
            raise ValueError(f"Invalid register number: {reg_num}")
        
        # x0 is always zero
        if reg_num == 0:
            return zero_bits(32)
        
        return self.registers[reg_num][:]  # Return copy
    
    def write_register(self, reg_num: int, value: Bits) -> None:
        """
        Write value to register reg_num
        x0 writes are ignored (hardwired to zero)
        """
        if not (0 <= reg_num <= 31):
            raise ValueError(f"Invalid register number: {reg_num}")
        
        # x0 is hardwired to zero - ignore writes
        if reg_num == 0:
            return
        
        # Ensure value is 32 bits
        if len(value) != 32:
            if len(value) < 32:
                value = left_pad(value, 32, 0)  # Zero extend
            else:
                value = value[-32:]  # Truncate to 32 bits
        
        self.registers[reg_num] = value[:]
    
    def read_two_registers(self, rs1: int, rs2: int) -> tuple[Bits, Bits]:
        """
        Read two registers simultaneously (common operation)
        """
        return self.read_register(rs1), self.read_register(rs2)
    
    def get_register_value_int(self, reg_num: int) -> int:
        """
        Get register value as signed integer (for debugging/testing)
        """
        bits = self.read_register(reg_num)
        decoded = decode_twos_complement(bits)
        return int(decoded['value_str'])
    
    def set_register_value_int(self, reg_num: int, value: int) -> None:
        """
        Set register value from signed integer (for debugging/testing)
        """
        encoded = encode_twos_complement(str(value))
        # Convert hex string to bits
        hex_str = encoded['hex'][2:]  # Remove '0x'
        bits = []
        for hex_char in hex_str:
            nibble = int(hex_char, 16)
            for i in range(3, -1, -1):
                bits.append((nibble >> i) & 1)
        self.write_register(reg_num, bits)
    
    def reset(self) -> None:
        """
        Reset all registers to zero
        """
        self.registers = [zero_bits(32) for _ in range(32)]
    
    def get_register_state(self) -> str:
        """
        Return string representation of all non-zero registers
        """
        result = "Register File State:\n"
        for i in range(32):
            if i == 0:
                result += f"x{i:2d} (zero): 0x00000000\n"
            else:
                value = self.get_register_value_int(i)
                if value != 0:
                    result += f"x{i:2d}: 0x{value & 0xFFFFFFFF:08X} ({value})\n"
        return result