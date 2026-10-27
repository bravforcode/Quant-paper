"""Measurement core for the CPIV abstention-aware protocol.

The core is deliberately data-independent: every market-data entry point goes
through the licence gate in :mod:`research.cpiv.measurement.config`.
"""

from research.cpiv.measurement.errors import (
    ConfigError,
    FreezeError,
    LicenceMissingError,
    MeasurementError,
    ReconciliationError,
)
from research.cpiv.measurement.status import (
    PairRecord,
    ReasonCode,
    Stage,
    TerminalStatus,
    funnel,
    reconcile,
)

__all__ = [
    "ConfigError",
    "FreezeError",
    "LicenceMissingError",
    "MeasurementError",
    "PairRecord",
    "ReasonCode",
    "ReconciliationError",
    "Stage",
    "TerminalStatus",
    "funnel",
    "reconcile",
]
