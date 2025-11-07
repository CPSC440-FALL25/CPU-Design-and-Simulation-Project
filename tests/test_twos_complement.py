"""
Test suite for Two's Complement Operations using pytest

This module contains comprehensive tests for the two's complement functions
and helper utilities for RISC-V numeric operations.
"""

import pytest
import sys
import os

# Add the operations directory to the path so we can import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operations'))

from twos_complement import (
    encode_twos_complement,
    decode_twos_complement,
    sign_extend,
    zero_extend,
    truncate_bits
)


class TestEncodeTwosComplement:
    """Test cases for encode_twos_complement function"""
    
    @pytest.mark.parametrize("value,expected_bin,expected_hex,expected_overflow", [
        (42, '00000000000000000000000000101010', '0000002A', False),
        (-42, '11111111111111111111111111010110', 'FFFFFFD6', False),
        (0, '00000000000000000000000000000000', '00000000', False),
        (2147483647, '01111111111111111111111111111111', '7FFFFFFF', False),
        (-2147483648, '10000000000000000000000000000000', '80000000', False),
        (2147483648, '10000000000000000000000000000000', '80000000', True),
        (-2147483649, '01111111111111111111111111111111', '7FFFFFFF', True),
    ])
    def test_encode_various_values(self, value, expected_bin, expected_hex, expected_overflow):
        """Test encoding various values including edge cases and overflow"""
        result = encode_twos_complement(value)
        assert result['bin'] == expected_bin
        assert result['hex'] == expected_hex
        assert result['overflow_flag'] == expected_overflow
    
    def test_encode_specific_examples(self):
        """Test the specific examples from requirements"""
        # Test +13
        result = encode_twos_complement(13)
        assert result['bin'] == '00000000000000000000000000001101'
        assert result['hex'] == '0000000D'
        assert result['overflow_flag'] == False
        
        # Test -13
        result = encode_twos_complement(-13)
        assert result['bin'] == '11111111111111111111111111110011'
        assert result['hex'] == 'FFFFFFF3'
        assert result['overflow_flag'] == False
        
        # Test 2^31 (overflow)
        result = encode_twos_complement(2**31)
        assert result['overflow_flag'] == True


class TestDecodeTwosComplement:
    """Test cases for decode_twos_complement function"""
    
    @pytest.mark.parametrize("bits_input,expected_value,description", [
        ('00000000000000000000000000101010', 42, "Positive number (42)"),
        ('11111111111111111111111111010110', -42, "Negative number (-42)"),
        ('00000000000000000000000000000000', 0, "Zero"),
        ('01111111111111111111111111111111', 2147483647, "Max positive"),
        ('10000000000000000000000000000000', -2147483648, "Min negative"),
        (0x0000002A, 42, "Integer input (42)"),
        (0xFFFFFFD6, -42, "Integer input (-42)"),
        ('0b00000000000000000000000000101010', 42, "Binary string with 0b prefix"),
    ])
    def test_decode_various_inputs(self, bits_input, expected_value, description):
        """Test decoding various input formats"""
        result = decode_twos_complement(bits_input)
        assert result['value'] == expected_value
    
    def test_decode_invalid_input(self):
        """Test that invalid input raises appropriate error"""
        with pytest.raises(ValueError, match="Input must be a binary string or integer"):
            decode_twos_complement(3.14)  # Float should raise error


class TestRoundTrip:
    """Test that encode -> decode gives back the original value"""
    
    @pytest.mark.parametrize("value", [42, -42, 0, 1000, -1000, 2147483647, -2147483648])
    def test_round_trip_no_overflow(self, value):
        """Test round trip for values that don't overflow"""
        encoded = encode_twos_complement(value)
        assert not encoded['overflow_flag']  # Ensure no overflow for this test
        decoded = decode_twos_complement(encoded['bin'])
        assert decoded['value'] == value


class TestSignExtend:
    """Test cases for sign extension functionality"""
    
    @pytest.mark.parametrize("value,from_bits,to_bits,expected,description", [
        (0b0111, 4, 8, 0b00000111, "Positive 4-bit to 8-bit"),
        (0b1111, 4, 8, 0b11111111, "Negative 4-bit to 8-bit"),
        (0b0000, 4, 8, 0b00000000, "Zero 4-bit to 8-bit"),
        (0b1000, 4, 8, 0b11111000, "Most negative 4-bit to 8-bit"),
        (0x7F, 8, 16, 0x007F, "Positive 8-bit to 16-bit"),
        (0x80, 8, 16, 0xFF80, "Negative 8-bit to 16-bit"),
        (0x7FFF, 16, 32, 0x00007FFF, "Positive 16-bit to 32-bit"),
        (0x8000, 16, 32, 0xFFFF8000, "Negative 16-bit to 32-bit"),
    ])
    def test_sign_extend_various(self, value, from_bits, to_bits, expected, description):
        """Test sign extension with various bit widths"""
        result = sign_extend(value, from_bits, to_bits)
        assert result == expected, f"Failed: {description}"
    
    def test_sign_extend_errors(self):
        """Test sign extend error conditions"""
        with pytest.raises(ValueError, match="Bit widths must be positive"):
            sign_extend(42, 0, 8)
        
        with pytest.raises(ValueError, match="Cannot sign-extend to smaller width"):
            sign_extend(42, 8, 4)


class TestZeroExtend:
    """Test cases for zero extension functionality"""
    
    @pytest.mark.parametrize("value,from_bits,to_bits,expected,description", [
        (0b0111, 4, 8, 0b00000111, "4-bit to 8-bit"),
        (0b1111, 4, 8, 0b00001111, "4-bit with high bit set"),
        (0b0000, 4, 8, 0b00000000, "Zero 4-bit to 8-bit"),
        (0xFF, 8, 16, 0x00FF, "8-bit to 16-bit"),
        (0x80, 8, 16, 0x0080, "8-bit with high bit set"),
        (0xFFFF, 16, 32, 0x0000FFFF, "16-bit to 32-bit"),
    ])
    def test_zero_extend_various(self, value, from_bits, to_bits, expected, description):
        """Test zero extension with various bit widths"""
        result = zero_extend(value, from_bits, to_bits)
        assert result == expected, f"Failed: {description}"
    
    def test_zero_extend_errors(self):
        """Test zero extend error conditions"""
        with pytest.raises(ValueError, match="Bit widths must be positive"):
            zero_extend(42, -1, 8)
        
        with pytest.raises(ValueError, match="Cannot zero-extend to smaller width"):
            zero_extend(42, 16, 8)


class TestTruncateBits:
    """Test cases for bit truncation functionality"""
    
    @pytest.mark.parametrize("value,to_bits,expected,description", [
        (0b11110101, 4, 0b0101, "8-bit to 4-bit"),
        (0b11110000, 4, 0b0000, "8-bit to 4-bit (zeros)"),
        (0xABCD, 8, 0xCD, "16-bit to 8-bit"),
        (0x12345678, 16, 0x5678, "32-bit to 16-bit"),
        (0xFFFFFFFF, 8, 0xFF, "32-bit all 1s to 8-bit"),
    ])
    def test_truncate_various(self, value, to_bits, expected, description):
        """Test bit truncation with various values"""
        result = truncate_bits(value, to_bits)
        assert result == expected, f"Failed: {description}"
    
    def test_truncate_errors(self):
        """Test truncate error conditions"""
        with pytest.raises(ValueError, match="Bit width must be positive"):
            truncate_bits(42, 0)


class TestRiscVScenarios:
    """Test common RISC-V instruction scenarios"""
    
    def test_i_type_immediate(self):
        """Test I-type immediate (12-bit to 32-bit sign extension)"""
        imm_12bit = 0b111111111010  # -6 in 12-bit two's complement
        extended = sign_extend(imm_12bit, 12, 32)
        decoded = decode_twos_complement(extended)
        assert decoded['value'] == -6
    
    def test_branch_offset(self):
        """Test branch offset (13-bit to 32-bit sign extension)"""
        branch_offset = 0b1111111110000  # -16 in 13-bit
        extended = sign_extend(branch_offset, 13, 32)
        decoded = decode_twos_complement(extended)
        assert decoded['value'] == -16
    
    def test_load_byte_zero_extension(self):
        """Test load byte zero-extension (8-bit to 32-bit)"""
        byte_value = 0b10101010  # 170 as unsigned byte
        extended = zero_extend(byte_value, 8, 32)
        assert extended == 170
    
    def test_load_byte_sign_extension(self):
        """Test load byte sign-extension (8-bit to 32-bit)"""
        byte_value = 0b10101010  # Should become negative when sign-extended
        extended_signed = sign_extend(byte_value, 8, 32)
        decoded_signed = decode_twos_complement(extended_signed)
        assert decoded_signed['value'] == -86


# Fixtures for common test data
@pytest.fixture
def overflow_test_cases():
    """Fixture providing test cases for overflow scenarios"""
    return [
        (2147483647, False),   # Max positive (no overflow)
        (-2147483648, False),  # Min negative (no overflow)
        (2147483648, True),    # Overflow positive
        (-2147483649, True),   # Overflow negative
    ]


def test_overflow_boundary_conditions(overflow_test_cases):
    """Test overflow detection at boundary conditions"""
    for value, should_overflow in overflow_test_cases:
        result = encode_twos_complement(value)
        assert result['overflow_flag'] == should_overflow


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])