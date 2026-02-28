"""
Custom exceptions for fingerprint sensor operations.
"""


class FingerprintSensorError(Exception):
    """Base exception for all fingerprint sensor errors."""
    pass


class SensorInitializationError(FingerprintSensorError):
    """Raised when sensor initialization fails."""
    pass


class EnrollmentError(FingerprintSensorError):
    """Raised when fingerprint enrollment fails."""
    pass


class VerificationError(FingerprintSensorError):
    """Raised when fingerprint verification fails."""
    pass


class ConfigurationError(FingerprintSensorError):
    """Raised when configuration operation fails."""
    pass


class DeletionError(FingerprintSensorError):
    """Raised when fingerprint deletion fails."""
    pass


class ImageCaptureError(FingerprintSensorError):
    """Raised when image capture fails."""
    pass


class TemplateError(FingerprintSensorError):
    """Raised when template operations fail."""
    pass
