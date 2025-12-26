"""
LANCH - Common Utility Functions
Shared utility functions used across the application
"""

from typing import Optional, Any, Dict, List, TypeVar, Callable
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
import re


T = TypeVar('T')


def format_currency(value: float | Decimal) -> str:
    """
    Format a number as Brazilian currency (R$)
    
    Args:
        value: The numeric value to format
        
    Returns:
        Formatted currency string (e.g., 'R$ 1.234,56')
        
    Examples:
        >>> format_currency(1234.56)
        'R$ 1.234,56'
        >>> format_currency(Decimal('99.99'))
        'R$ 99,99'
    """
    if isinstance(value, Decimal):
        value = float(value)
    
    # Format with 2 decimal places
    formatted = f"{value:,.2f}"
    
    # Replace comma and dot for Brazilian format
    formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    
    return f"R$ {formatted}"


def parse_currency(value: str) -> float:
    """
    Parse Brazilian currency string to float
    
    Args:
        value: Currency string (e.g., 'R$ 1.234,56')
        
    Returns:
        Float value
        
    Raises:
        ValueError: If string cannot be parsed as currency
        
    Examples:
        >>> parse_currency('R$ 1.234,56')
        1234.56
        >>> parse_currency('1.234,56')
        1234.56
    """
    if not value:
        raise ValueError("Currency string cannot be empty")
    
    # Remove currency symbol and spaces
    cleaned = value.replace('R$', '').replace(' ', '')
    
    # Replace Brazilian format to standard format
    cleaned = cleaned.replace('.', '').replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError as e:
        raise ValueError(f"Invalid currency format: {value}") from e


def validate_cpf(cpf: str) -> bool:
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas)
    
    Args:
        cpf: CPF string with or without formatting
        
    Returns:
        True if CPF is valid, False otherwise
        
    Examples:
        >>> validate_cpf('123.456.789-09')
        False
        >>> validate_cpf('00000000000')
        False
    """
    # Remove non-digit characters
    cpf = re.sub(r'\D', '', cpf)
    
    # Check length
    if len(cpf) != 11:
        return False
    
    # Check if all digits are the same
    if cpf == cpf[0] * 11:
        return False
    
    # Validate check digits
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    
    return True


def format_cpf(cpf: str) -> str:
    """
    Format CPF with mask (XXX.XXX.XXX-XX)
    
    Args:
        cpf: CPF string with or without formatting
        
    Returns:
        Formatted CPF string
        
    Examples:
        >>> format_cpf('12345678909')
        '123.456.789-09'
    """
    # Remove non-digit characters
    cpf = re.sub(r'\D', '', cpf)
    
    if len(cpf) != 11:
        return cpf  # Return as-is if invalid
    
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Value to return if denominator is zero
        
    Returns:
        Result of division or default value
        
    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
        >>> safe_divide(10, 0, default=-1)
        -1.0
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (ZeroDivisionError, TypeError):
        return default


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate a string to maximum length, adding suffix if truncated
    
    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
        
    Examples:
        >>> truncate_string('Hello World', 8)
        'Hello...'
        >>> truncate_string('Hello', 10)
        'Hello'
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def get_competencia_referencia(ano: int, mes: int) -> str:
    """
    Format competencia (period) reference as MM/YYYY
    
    Args:
        ano: Year (YYYY)
        mes: Month (1-12)
        
    Returns:
        Formatted reference string
        
    Examples:
        >>> get_competencia_referencia(2024, 12)
        '12/2024'
        >>> get_competencia_referencia(2024, 1)
        '01/2024'
    """
    return f"{mes:02d}/{ano}"


def parse_competencia_referencia(referencia: str) -> tuple[int, int]:
    """
    Parse competencia reference string to year and month
    
    Args:
        referencia: Reference string in format MM/YYYY
        
    Returns:
        Tuple of (ano, mes)
        
    Raises:
        ValueError: If string format is invalid
        
    Examples:
        >>> parse_competencia_referencia('12/2024')
        (2024, 12)
    """
    try:
        parts = referencia.split('/')
        if len(parts) != 2:
            raise ValueError("Invalid format")
        
        mes = int(parts[0])
        ano = int(parts[1])
        
        if not (1 <= mes <= 12):
            raise ValueError("Month must be between 1 and 12")
        
        return ano, mes
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid competencia reference: {referencia}") from e


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing illegal characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
        
    Examples:
        >>> sanitize_filename('my/file:name?.txt')
        'my_file_name_.txt'
    """
    # Replace illegal characters with underscore
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, '_', filename)
    
    # Remove control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
    
    # Limit length
    return truncate_string(sanitized, 255, '')


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of specified size
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
        
    Examples:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_get(dictionary: Dict[str, Any], keys: str, default: Any = None) -> Any:
    """
    Safely get a nested dictionary value using dot notation
    
    Args:
        dictionary: Dictionary to search
        keys: Dot-separated keys (e.g., 'user.profile.name')
        default: Default value if key not found
        
    Returns:
        Value at nested key or default
        
    Examples:
        >>> data = {'user': {'profile': {'name': 'John'}}}
        >>> deep_get(data, 'user.profile.name')
        'John'
        >>> deep_get(data, 'user.invalid.key', 'default')
        'default'
    """
    keys_list = keys.split('.')
    value = dictionary
    
    for key in keys_list:
        try:
            value = value[key]
        except (KeyError, TypeError, AttributeError):
            return default
    
    return value


def retry_on_exception(
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
include_exceptions: tuple = (Exception,)
) -> T:
    """
    Retry a function on exception
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
        include_exceptions: Tuple of exceptions to catch
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except include_exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    raise last_exception if last_exception else RuntimeError("Retry failed")
