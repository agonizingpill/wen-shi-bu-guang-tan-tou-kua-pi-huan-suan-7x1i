from enum import StrEnum


class Role(StrEnum):
    TECHNICIAN = "technician"
    SUPERVISOR = "supervisor"
    VIEWER = "viewer"


class Mode(StrEnum):
    LOW = "low"
    HIGH = "high"


class SegmentState(StrEnum):
    DRAFT = "draft"
    WITNESSED = "witnessed"
    RECALLED = "recalled"
    DISCARDED = "discarded"


class CalibrationState(StrEnum):
    QUEUED = "queued"
    READY = "ready"
    REJECTED = "rejected"
    AWAITING_RECAPTURE = "awaiting_recapture"
    ACTIVE = "active"
    RETIRED = "retired"
