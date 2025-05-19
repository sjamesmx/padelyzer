from fastapi import HTTPException, status

class AppException(HTTPException):
    """Base exception for application-specific errors."""
    def __init__(self, status_code: int, message: str, error_code: str = None):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code

class PadelException(HTTPException):
    """Base exception for Padelyzer application."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class VideoProcessingError(PadelException):
    """Exception raised when there's an error processing a video."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error processing video: {detail}"
        )

class AuthenticationError(PadelException):
    """Exception raised when there's an authentication error."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {detail}"
        )

class ResourceNotFoundError(PadelException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with id {resource_id} not found"
        )

class ValidationError(PadelException):
    """Exception raised when there's a validation error."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {detail}"
        )

class DatabaseError(PadelException):
    """Exception raised when there's a database error."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {detail}"
        ) 