"""Custom exceptions for the Padelyzer application.

This module defines custom exceptions used throughout the application for consistent error handling.
"""

class PadelException(Exception):
    """Custom exception for Padel-specific errors.
    
    This exception is used for business logic errors and validation failures
    that are specific to the padel domain.
    
    Attributes:
        message (str): A human-readable error message
        status_code (int): HTTP status code to return (default: 400)
    """
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AppException(Exception):
    """General application exception.
    
    This exception is used for unexpected errors and system-level failures
    that are not specific to the padel domain.
    
    Attributes:
        message (str): A human-readable error message
        status_code (int): HTTP status code to return (default: 500)
    """
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message) 