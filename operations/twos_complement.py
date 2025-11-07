"""
Two's Complement Operations for RISC-V (32-bit)

This module provides functions for encoding/decoding two's complement representations
and helper functions for sign extension, zero extension, and bit manipulation.
"""


def encode_twos_complement(value: int) -> dict:
    """
    Encode an integer to 32-bit two's complement representation.
    
    Args:
        value: Idnteger to encode (can be positive or negative)
        
    Returns:
        dict with keys:
        - 'bin': Binary string representation (32 bits)
        - 'hex': Hexadecimal string representation (8 hex digits)
        - 'overflow_flag': Boolean indicating if value overflows 32-bit range
    """
    XLEN = 32
    MAX_POSITIVE = (1 << (XLEN - 1)) - 1  # 2^31 - 1 = 2147483647
    MIN_NEGATIVE = -(1 << (XLEN - 1))     # -2^31 = -2147483648
    
    # Check for overflow
    overflow_flag = value > MAX_POSITIVE or value < MIN_NEGATIVE
    
    # Convert to 32-bit two's complement (with wraparound for overflow)
    if value >= 0:
        # Positive numbers: mask to 32 bits
        twos_comp = value & ((1 << XLEN) - 1)
    else:
        # Negative numbers: use two's complement formula
        twos_comp = ((1 << XLEN) + value) & ((1 << XLEN) - 1)
    
    # Format binary string (32 bits with leading zeros)
    bin_str = f"{twos_comp:032b}"
    
    # Format hex string (8 hex digits with leading zeros)
    hex_str = f"{twos_comp:08X}"
    
    return {
        'bin': bin_str,
        'hex': hex_str,
        'overflow_flag': overflow_flag
    }


def decode_twos_complement(bits) -> dict:
    """
    Decode a 32-bit two's complement representation back to a signed integer.
    
    Args:
        bits: Either a binary string (e.g., '11111111111111111111111111010110') 
              or an integer representing the bit pattern
        
    Returns:
        dict with key:
        - 'value': The decoded signed integer value
    """
    XLEN = 32
    
    # Handle different input types
    if isinstance(bits, str):
        # Remove any '0b' prefix and whitespace
        bits = bits.replace('0b', '').replace(' ', '')
        # Convert binary string to integer
        bit_pattern = int(bits, 2)
    elif isinstance(bits, int):
        # Already an integer, ensure it's within 32-bit range
        bit_pattern = bits & ((1 << XLEN) - 1)
    else:
        raise ValueError("Input must be a binary string or integer")
    
    # Check if the sign bit (MSB) is set
    sign_bit = bit_pattern & (1 << (XLEN - 1))
    
    if sign_bit:
        # Negative number: subtract 2^32 to get the negative value
        value = bit_pattern - (1 << XLEN)
    else:
        # Positive number: value is the bit pattern itself
        value = bit_pattern
    
    return {'value': value}


def sign_extend(value: int, from_bits: int, to_bits: int = 32) -> int:
    """
    Sign-extend a value from a smaller bit width to a larger bit width.
    Preserves the sign by replicating the MSB (sign bit).
    
    Args:
        value: The value to sign-extend
        from_bits: Current bit width of the value
        to_bits: Target bit width (default: 32 for RISC-V)
        
    Returns:
        int: Sign-extended value
        
    Example:
        sign_extend(0b1111, 4, 8) -> 0b11111111 (-1 in 4-bit becomes -1 in 8-bit)
        sign_extend(0b0111, 4, 8) -> 0b00000111 (7 in 4-bit becomes 7 in 8-bit)
    """
    if from_bits <= 0 or to_bits <= 0:
        raise ValueError("Bit widths must be positive")
    if from_bits > to_bits:
        raise ValueError("Cannot sign-extend to smaller width")
    
    # Mask to get only the relevant bits from the source
    mask = (1 << from_bits) - 1
    value = value & mask
    
    # Check if the sign bit is set
    sign_bit = value & (1 << (from_bits - 1))
    
    if sign_bit:
        # Negative number: set all higher-order bits to 1
        extension_mask = ((1 << (to_bits - from_bits)) - 1) << from_bits
        return value | extension_mask
    else:
        # Positive number: higher-order bits remain 0
        return value


def zero_extend(value: int, from_bits: int, to_bits: int = 32) -> int:
    """
    Zero-extend a value from a smaller bit width to a larger bit width.
    Fills higher-order bits with zeros.
    
    Args:
        value: The value to zero-extend
        from_bits: Current bit width of the value
        to_bits: Target bit width (default: 32 for RISC-V)
        
    Returns:
        int: Zero-extended value
        
    Example:
        zero_extend(0b1111, 4, 8) -> 0b00001111
        zero_extend(0b0111, 4, 8) -> 0b00000111
    """
    if from_bits <= 0 or to_bits <= 0:
        raise ValueError("Bit widths must be positive")
    if from_bits > to_bits:
        raise ValueError("Cannot zero-extend to smaller width")
    
    # Mask to get only the relevant bits from the source
    mask = (1 << from_bits) - 1
    return value & mask


def truncate_bits(value: int, to_bits: int) -> int:
    """
    Truncate a value to a specific bit width (keep only the lower bits).
    
    Args:
        value: The value to truncate
        to_bits: Target bit width
        
    Returns:
        int: Truncated value
        
    Example:
        truncate_bits(0b11110101, 4) -> 0b0101
    """
    if to_bits <= 0:
        raise ValueError("Bit width must be positive")
    
    mask = (1 << to_bits) - 1
    return value & mask