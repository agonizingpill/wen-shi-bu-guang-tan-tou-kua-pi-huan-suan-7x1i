from datetime import date

from pydantic import BaseModel, Field, model_validator

from .constants import Mode
from .installation import Serial
from .settings import BLOCK_MINUTES


class ReferencePair(BaseModel):
    offset_seconds: int = Field(ge=0, le=599)
    raw_lux: float = Field(ge=0, le=100000, allow_inf_nan=False)
    reference_lux: float = Field(ge=0, le=100000, allow_inf_nan=False)


class CaptureSegment(BaseModel):
    probe_id: int = Field(gt=0)
    day: date
    mode: Mode
    start_minute: int = Field(ge=0, le=1430, multiple_of=BLOCK_MINUTES)
    reference_serial: Serial
    source: str = Field(min_length=4, max_length=100)
    points: list[ReferencePair] = Field(min_length=4, max_length=60)

    @model_validator(mode="after")
    def check_offsets(self):
        if len({point.offset_seconds for point in self.points}) != len(self.points):
            raise ValueError("同一分钟段的测量秒数不可重复。")
        return self


class WitnessNote(BaseModel):
    note: str = Field(min_length=4, max_length=180)
