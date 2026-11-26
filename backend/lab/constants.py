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
    DISCARDED = "discarded"


class CalibrationState(StrEnum):
    QUEUED = "queued"
    READY = "ready"
    REJECTED = "rejected"
    ACTIVE = "active"
    RETIRED = "retired"
