"""
RISC-V Memory Interface Implementation
Supports load/store operations with proper byte addressing
Uses utils bit-vector utilities for data representation
"""

from typing import Dict, List, Optional
from utils import Bits, zero_bits, left_pad, bits_to_hex, sign_extend, zero_extend


class MemoryInterface:
    def __init__(self, size_words: int = 1024):
        """
        Initialize memory with specified size in 32-bit words
        Memory is byte-addressable but aligned to word boundaries
        """
        self.size_words = size_words
        self.size_bytes = size_words * 4
        # Memory stored as 32-bit words (each is a Bits list)
        self.memory: Dict[int, Bits] = {}
        
    def _get_word_address(self, byte_address: int) -> int:
        """Convert byte address to word address"""
        return byte_address // 4
        
    def _get_byte_offset(self, byte_address: int) -> int:
        """Get byte offset within word (0-3)"""
        return byte_address % 4
    
    def _address_to_bits(self, address: int) -> Bits:
        """Convert integer address to 32-bit address"""
        # Convert to 32-bit representation
        addr_bits = []
        for i in range(31, -1, -1):
            addr_bits.append((address >> i) & 1)
        return addr_bits
    
    def _bits_to_address(self, address_bits: Bits) -> int:
        """Convert 32-bit address to integer"""
        if len(address_bits) != 32:
            raise ValueError("Address must be 32 bits")
        
        address = 0
        for bit in address_bits:
            address = (address << 1) | bit
        return address
    
    def load_word(self, address_bits: Bits) -> Bits:
        """
        Load 32-bit word from memory
        Address must be word-aligned (bottom 2 bits zero)
        """
        address = self._bits_to_address(address_bits)
        
        if address % 4 != 0:
            raise ValueError(f"Misaligned word access at address {address:#x}")
        
        word_addr = self._get_word_address(address)
        
        if word_addr in self.memory:
            return self.memory[word_addr][:]
        else:
            # Return zero for uninitialized memory
            return zero_bits(32)
    
    def store_word(self, address_bits: Bits, data_bits: Bits) -> None:
        """
        Store 32-bit word to memory
        Address must be word-aligned (bottom 2 bits zero)
        """
        address = self._bits_to_address(address_bits)
        
        if address % 4 != 0:
            raise ValueError(f"Misaligned word access at address {address:#x}")
        
        if len(data_bits) != 32:
            raise ValueError("Data must be 32 bits for word store")
        
        word_addr = self._get_word_address(address)
        self.memory[word_addr] = data_bits[:]
    
    def load_halfword(self, address_bits: Bits, unsigned: bool = False) -> Bits:
        """
        Load 16-bit halfword from memory
        Address must be halfword-aligned (bottom bit zero)
        """
        address = self._bits_to_address(address_bits)
        
        if address % 2 != 0:
            raise ValueError(f"Misaligned halfword access at address {address:#x}")
        
        word_addr = self._get_word_address(address)
        byte_offset = self._get_byte_offset(address)
        
        if word_addr in self.memory:
            word_data = self.memory[word_addr]
        else:
            word_data = zero_bits(32)
        
        # Extract 16-bit halfword based on byte offset
        if byte_offset == 0:
            # Bits 31:16
            halfword = word_data[0:16]
        elif byte_offset == 2:
            # Bits 15:0
            halfword = word_data[16:32]
        else:
            raise ValueError(f"Invalid halfword alignment at address {address:#x}")
        
        # Sign or zero extend to 32 bits
        if unsigned:
            return zero_extend(halfword, 16, 32)
        else:
            return sign_extend(halfword, 16, 32)
    
    def store_halfword(self, address_bits: Bits, data_bits: Bits) -> None:
        """
        Store 16-bit halfword to memory
        Address must be halfword-aligned (bottom bit zero)
        """
        address = self._bits_to_address(address_bits)
        
        if address % 2 != 0:
            raise ValueError(f"Misaligned halfword access at address {address:#x}")
        
        if len(data_bits) != 32:
            raise ValueError("Data must be 32 bits")
        
        # Take bottom 16 bits
        halfword = data_bits[16:32]
        
        word_addr = self._get_word_address(address)
        byte_offset = self._get_byte_offset(address)
        
        # Get existing word or create new one
        if word_addr in self.memory:
            word_data = self.memory[word_addr][:]
        else:
            word_data = zero_bits(32)
        
        # Update appropriate halfword
        if byte_offset == 0:
            # Update bits 31:16
            word_data[0:16] = halfword
        elif byte_offset == 2:
            # Update bits 15:0
            word_data[16:32] = halfword
        else:
            raise ValueError(f"Invalid halfword alignment at address {address:#x}")
        
        self.memory[word_addr] = word_data
    
    def load_byte(self, address_bits: Bits, unsigned: bool = False) -> Bits:
        """
        Load 8-bit byte from memory
        No alignment restrictions
        """
        address = self._bits_to_address(address_bits)
        
        word_addr = self._get_word_address(address)
        byte_offset = self._get_byte_offset(address)
        
        if word_addr in self.memory:
            word_data = self.memory[word_addr]
        else:
            word_data = zero_bits(32)
        
        # Extract 8-bit byte based on byte offset
        # Big-endian: byte 0 is bits 31:24, byte 1 is bits 23:16, etc.
        start_bit = byte_offset * 8
        byte_data = word_data[start_bit:start_bit+8]
        
        # Sign or zero extend to 32 bits
        if unsigned:
            return zero_extend(byte_data, 8, 32)
        else:
            return sign_extend(byte_data, 8, 32)
    
    def store_byte(self, address_bits: Bits, data_bits: Bits) -> None:
        """
        Store 8-bit byte to memory
        No alignment restrictions
        """
        address = self._bits_to_address(address_bits)
        
        if len(data_bits) != 32:
            raise ValueError("Data must be 32 bits")
        
        # Take bottom 8 bits
        byte_data = data_bits[24:32]
        
        word_addr = self._get_word_address(address)
        byte_offset = self._get_byte_offset(address)
        
        # Get existing word or create new one
        if word_addr in self.memory:
            word_data = self.memory[word_addr][:]
        else:
            word_data = zero_bits(32)
        
        # Update appropriate byte
        start_bit = byte_offset * 8
        word_data[start_bit:start_bit+8] = byte_data
        
        self.memory[word_addr] = word_data
    
    def load_instruction(self, pc_bits: Bits) -> Bits:
        """
        Load instruction from memory (always 32-bit word aligned)
        Used for instruction fetch
        """
        return self.load_word(pc_bits)
    
    def load_program(self, hex_file_path: str, base_address: int = 0) -> None:
        """
        Load program from hex file into memory
        """
        try:
            with open(hex_file_path, 'r') as f:
                lines = f.readlines()
            
            address = base_address
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                
                # Remove any whitespace and convert to uppercase
                hex_data = line.replace(' ', '').upper()
                
                if len(hex_data) == 8:  # 32-bit instruction
                    # Convert hex string to bits
                    instruction_bits = []
                    for hex_char in hex_data:
                        nibble = int(hex_char, 16)
                        for i in range(3, -1, -1):
                            instruction_bits.append((nibble >> i) & 1)
                    
                    # Store instruction
                    addr_bits = self._address_to_bits(address)
                    self.store_word(addr_bits, instruction_bits)
                    address += 4
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"Program file not found: {hex_file_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading program: {e}")
    
    def get_memory_state(self, start_word: int = 0, num_words: int = 16) -> str:
        """
        Return string representation of memory contents
        """
        result = f"Memory Contents (words {start_word}-{start_word + num_words - 1}):\n"
        for i in range(start_word, start_word + num_words):
            if i in self.memory:
                hex_val = bits_to_hex(self.memory[i])
                result += f"0x{i*4:08X}: {hex_val}\n"
            else:
                result += f"0x{i*4:08X}: 0x00000000\n"
        return result
        
    def _get_byte_offset(self, byte_address: int) -> int:
        """Get byte offset within word (0-3)"""
        return byte_address % 4
    
    def _address_to_bits(self, address: int) -> Bits:
        """Convert integer address to 32-bit address"""
        # Convert to 32-bit representation
        addr_bits = []
        for i in range(31, -1, -1):
            addr_bits.append((address >> i) & 1)
        return addr_bits
    
    def _bits_to_address(self, address_bits: Bits) -> int:
        """Convert 32-bit address to integer"""
        if len(address_bits) != 32:
            raise ValueError("Address must be 32 bits")
        
        address = 0
        for bit in address_bits:
            address = (address << 1) | bit
        return address
    
    def load_word(self, address_bits: Bits) -> Bits:
        addr = self._bits_to_address(address_bits) // 4
        return self.memory.get(addr, zero_bits(32))[:]
    
    def store_word(self, address_bits: Bits, data_bits: Bits) -> None:
        self.memory[self._bits_to_address(address_bits) // 4] = data_bits[:32]
    
    def load_halfword(self, address_bits: Bits, unsigned: bool = False) -> Bits:
        addr = self._bits_to_address(address_bits)
        word_data = self.memory.get(addr // 4, zero_bits(32))
        offset = addr % 4
        halfword = word_data[0:16] if offset == 0 else word_data[16:32]
        return zero_extend(halfword, 16, 32) if unsigned else sign_extend(halfword, 16, 32)
    
    def store_halfword(self, address_bits: Bits, data_bits: Bits) -> None:
        addr = self._bits_to_address(address_bits)
        word_addr, offset = addr // 4, addr % 4
        word_data = self.memory.get(word_addr, zero_bits(32))[:]
        if offset == 0: word_data[0:16] = data_bits[16:32]
        else: word_data[16:32] = data_bits[16:32]
        self.memory[word_addr] = word_data
    
    def load_byte(self, address_bits: Bits, unsigned: bool = False) -> Bits:
        addr = self._bits_to_address(address_bits)
        word_data = self.memory.get(addr // 4, zero_bits(32))
        start = (addr % 4) * 8
        byte_data = word_data[start:start+8]
        return zero_extend(byte_data, 8, 32) if unsigned else sign_extend(byte_data, 8, 32)
    
    def store_byte(self, address_bits: Bits, data_bits: Bits) -> None:
        addr = self._bits_to_address(address_bits)
        word_addr, start = addr // 4, (addr % 4) * 8
        word_data = self.memory.get(word_addr, zero_bits(32))[:]
        word_data[start:start+8] = data_bits[24:32]
        self.memory[word_addr] = word_data
    
    def load_program(self, hex_file_path: str, base_address: int = 0) -> None:
        with open(hex_file_path, 'r') as f:
            for i, line in enumerate(f):
                if (hex_data := line.strip()) and len(hex_data) == 8:
                    bits = [int(b) for c in hex_data for b in f"{int(c, 16):04b}"]
                    self.store_word(self._address_to_bits(base_address + i * 4), bits)
    
    def dump_memory(self, start_word: int = 0, num_words: int = 8) -> str:
        lines = [f"Memory Contents (words {start_word}-{start_word + num_words - 1}):"]
        for i in range(start_word, start_word + num_words):
            hex_val = bits_to_hex(self.memory.get(i, zero_bits(32)))
            lines.append(f"0x{i*4:08X}: {hex_val}")
        return "\n".join(lines)