"""Core module package for fingerprint sensor functionality."""

from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.core.exceptions import (
    FingerprintSensorError,
    EnrollmentError,
    VerificationError,
    ConfigurationError
)

__all__ = [
    'FingerprintSensor',
    'FingerprintSensorError',
    'EnrollmentError',
    'VerificationError',
    'ConfigurationError',
]
