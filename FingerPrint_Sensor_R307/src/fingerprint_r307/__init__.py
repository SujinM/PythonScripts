"""
Fingerprint R307 Sensor Package

A Python library for interfacing with the R307 Fingerprint Sensor Module.
Provides easy-to-use APIs for fingerprint enrollment, verification, and management.
"""

__version__ = '1.0.0'
__author__ = 'Your Name'
__license__ = 'MIT'

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
