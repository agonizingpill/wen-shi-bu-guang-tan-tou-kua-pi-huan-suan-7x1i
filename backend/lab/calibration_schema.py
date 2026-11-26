from datetime import date

from pydantic import BaseModel, Field, model_validator

from .constants import Mode
from .settings import BLOCK_MINUTES


class FitRequest(BaseModel):
    probe_id: int = Field(gt=0)
    mode: Mode
    reference_day: date
    release_day: date
    start_minute: int = Field(ge=0, le=1410, multiple_of=BLOCK_MINUTES)
    end_minute: int = Field(ge=30, le=1440, multiple_of=BLOCK_MINUTES)

    @model_validator(mode="after")
    def fit_window(self):
        if not 30 <= self.end_minute - self.start_minute <= 180:
            raise ValueError("换算窗口须含连续 3 到 18 个十分钟段。")
        if self.release_day < self.reference_day:
            raise ValueError("生效日须等于或晚于基准采样日。")
        return self
