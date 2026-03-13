"""
validation.py — Comprehensive input validation utilities for Rhea platform.

Provides secure validation for emails, passwords, API keys, and other user inputs.
Prevents injection attacks and ensures data integrity.
"""

import re
import logging
from typing import Optional, Union
from pydantic import BaseModel, validator, EmailStr
from fastapi import HTTPException

log = logging.getLogger("rhea.validation")

# Regex patterns for validation
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
API_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Security constraints
MAX_EMAIL_LENGTH = 254
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 8
MAX_SAFE_STRING_LENGTH = 100
MAX_TEXT_LENGTH = 10000


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_email(email: str) -> str:
    """
    Validate email address with comprehensive checks.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email (lowercase, stripped)
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email is required")
    
    email = email.strip().lower()
    
    if len(email) > MAX_EMAIL_LENGTH:
        raise ValidationError(f"Email too long (max {MAX_EMAIL_LENGTH} characters)")
    
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Invalid email format")
    
    # Additional security checks
    if '..' in email:
        raise ValidationError("Email contains invalid characters")
    
    if email.startswith('.') or email.endswith('.'):
        raise ValidationError("Email cannot start or end with a dot")
    
    return email


def validate_password(password: str) -> str:
    """
    Validate password strength and security.
    
    Args:
        password: Password to validate
        
    Returns:
        Password as-is (do not modify for security)
        
    Raises:
        ValidationError: If password doesn't meet security requirements
    """
    if not password:
        raise ValidationError("Password is required")
    
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError(f"Password too long (max {MAX_PASSWORD_LENGTH} characters)")
    
    # Check for common weak patterns
    if password.lower() in ['password', '12345678', 'qwerty', 'admin']:
        raise ValidationError("Password is too common")
    
    # Check for at least one letter and one digit
    if not re.search(r'[a-zA-Z]', password):
        raise ValidationError("Password must contain at least one letter")
    
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")
    
    return password


def validate_safe_string(value: str, field_name: str = "value", 
                        min_length: int = 1, max_length: int = MAX_SAFE_STRING_LENGTH,
                        required: bool = True) -> str:
    """
    Validate string that contains only safe characters (alphanumeric, dot, underscore, dash).
    
    Args:
        value: String to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        required: Whether the field is required
        
    Returns:
        Validated string
        
    Raises:
        ValidationError: If string is invalid
    """
    if not value:
        if required:
            raise ValidationError(f"{field_name} is required")
        return ""
    
    value = value.strip()
    
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} too long (max {max_length} characters)")
    
    if not SAFE_STRING_PATTERN.match(value):
        raise ValidationError(f"{field_name} contains invalid characters")
    
    return value


def validate_api_key(key: str) -> str:
    """
    Validate API key format.
    
    Args:
        key: API key to validate
        
    Returns:
        Validated API key
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not key:
        raise ValidationError("API key is required")
    
    key = key.strip()
    
    if len(key) < 10:
        raise ValidationError("API key too short")
    
    if len(key) > 100:
        raise ValidationError("API key too long")
    
    if not API_KEY_PATTERN.match(key):
        raise ValidationError("API key contains invalid characters")
    
    return key


def validate_text_input(text: str, field_name: str = "text",
                      max_length: int = MAX_TEXT_LENGTH,
                      required: bool = True) -> str:
    """
    Validate general text input with XSS prevention.
    
    Args:
        text: Text to validate
        field_name: Name of the field for error messages
        max_length: Maximum allowed length
        required: Whether the field is required
        
    Returns:
        Sanitized text
        
    Raises:
        ValidationError: If text is invalid
    """
    if not text:
        if required:
            raise ValidationError(f"{field_name} is required")
        return ""
    
    text = text.strip()
    
    if len(text) > max_length:
        raise ValidationError(f"{field_name} too long (max {max_length} characters)")
    
    # Basic XSS prevention - remove script tags and JavaScript events
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    return text


def validate_oauth_params(code: str = "", state: str = "", error: str = "") -> dict:
    """
    Validate OAuth callback parameters.
    
    Args:
        code: Authorization code
        state: OAuth state parameter
        error: Error parameter
        
    Returns:
        Validated parameters
        
    Raises:
        ValidationError: If parameters are invalid
    """
    validated = {}
    
    if error:
        # OAuth error occurred, validate error message
        validated["error"] = validate_text_input(error, "error", max_length=200, required=False)
        return validated
    
    if not code:
        raise ValidationError("Authorization code is required")
    
    # Validate code format (should be URL-safe base64)
    if not re.match(r'^[A-Za-z0-9_\-/+=]+$', code):
        raise ValidationError("Invalid authorization code format")
    
    validated["code"] = code
    
    if state:
        # State should be URL-safe
        if not re.match(r'^[A-Za-z0-9_\-]+$', state):
            raise ValidationError("Invalid state parameter")
        validated["state"] = state
    
    return validated


# Pydantic models for automatic validation
class ValidatedAuthRequest(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password_strength(cls, v):
        return validate_password(v)
    
    @validator('email')
    def normalize_email(cls, v):
        return validate_email(v)


class ValidatedCreateKeyRequest(BaseModel):
    label: str = ""
    
    @validator('label')
    def validate_label(cls, v):
        if v:
            return validate_safe_string(v, "label", max_length=50, required=False)
        return v


class ValidatedCheckoutRequest(BaseModel):
    plan: str
    success_url: str = ""
    cancel_url: str = ""
    
    @validator('plan')
    def validate_plan(cls, v):
        allowed_plans = ["free", "pro", "enterprise"]
        if v not in allowed_plans:
            raise ValueError(f"Invalid plan. Allowed: {allowed_plans}")
        return v
    
    @validator('success_url', 'cancel_url')
    def validate_urls(cls, v):
        if v:
            # Basic URL validation
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("Invalid URL format")
            if len(v) > 500:
                raise ValueError("URL too long")
        return v


def handle_validation_error(func):
    """Decorator to convert ValidationError to HTTPException."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return wrapper
