"""Enhanced password input with terminal UI."""

import getpass
import sys
from typing import Optional


def get_password_with_confirmation(prompt: str = "Enter password: ") -> str:
    """Get password with confirmation.

    Args:
        prompt: Password prompt text.

    Returns:
        Validated password.

    Raises:
        ValueError: If passwords don't match or password is empty.
    """
    while True:
        password = getpass.getpass(prompt)
        
        if not password:
            print("ERROR: Password cannot be empty", file=sys.stderr)
            retry = input("Try again? (y/n): ").lower()
            if retry != 'y':
                raise ValueError("Password cannot be empty")
            continue
        
        confirm = getpass.getpass("Confirm password: ")
        
        if password == confirm:
            return password
        
        print("ERROR: Passwords do not match", file=sys.stderr)
        retry = input("Try again? (y/n): ").lower()
        if retry != 'y':
            raise ValueError("Passwords do not match")


def get_password_simple(prompt: str = "Enter password: ") -> str:
    """Get password without confirmation (for decryption).

    Args:
        prompt: Password prompt text.

    Returns:
        Password.

    Raises:
        ValueError: If password is empty.
    """
    password = getpass.getpass(prompt)
    
    if not password:
        raise ValueError("Password cannot be empty")
    
    return password


def get_password_interactive(
    mode: str = "encrypt",
    custom_prompt: Optional[str] = None
) -> str:
    """Get password with interactive terminal UI.

    Args:
        mode: Operation mode ('encrypt' or 'decrypt').
        custom_prompt: Custom prompt text (optional).

    Returns:
        Password string.

    Raises:
        ValueError: If password validation fails.
    """
    print("\n" + "=" * 60)
    print(f"{mode.upper()} - Password Required")
    print("=" * 60)
    
    if mode == "encrypt":
        print("\nPassword Tips:")
        print("  • Use at least 12 characters")
        print("  • Mix uppercase, lowercase, numbers, and symbols")
        print("  • Avoid common words or patterns")
        print("  • Store it securely - lost passwords cannot be recovered!\n")
        
        prompt = custom_prompt or "Enter encryption password: "
        return get_password_with_confirmation(prompt)
    else:
        print("\nEnter the password used during encryption\n")
        prompt = custom_prompt or "Enter decryption password: "
        return get_password_simple(prompt)


def display_password_strength(password: str) -> None:
    """Display password strength indicator.

    Args:
        password: Password to check.
    """
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    strength = sum([has_upper, has_lower, has_digit, has_special])
    
    if length < 8:
        level = "Very Weak"
        indicator = "[-]"
    elif length < 12:
        level = "Weak"
        indicator = "[~]"
    elif length < 16 or strength < 3:
        level = "Moderate"
        indicator = "[+]"
    elif strength >= 4:
        level = "Strong"
        indicator = "[++]"
    else:
        level = "Good"
        indicator = "[++]"
    
    print(f"\n{indicator} Password Strength: {level}")
    print(f"   Length: {length} characters")
    print(f"   Diversity: {strength}/4 character types")
