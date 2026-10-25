"""Exceptions for the CPIV measurement core."""

from __future__ import annotations


class MeasurementError(Exception):
    """Base class for measurement-pipeline failures."""


class LicenceMissingError(MeasurementError):
    """Raised when a market-data path is used without a written licence record."""


class ReconciliationError(MeasurementError):
    """Raised when pair statuses do not reconcile to the attempted total."""


class FreezeError(MeasurementError):
    """Raised when a primary or holdout run is attempted without a frozen protocol."""


class ConfigError(MeasurementError):
    """Raised when a configuration file is missing required structure."""
