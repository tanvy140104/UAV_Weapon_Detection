from datetime import datetime
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from backend.config import PROJECT_ROOT


class SessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    source_type: Literal["file", "camera"] = "file"
    source: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_type == "camera":
            if not self.source.isascii() or not self.source.isdigit() or int(self.source) > 99:
                raise ValueError("Camera index must be an integer from 0 to 99")
            self.source = str(int(self.source))
        else:
            source = Path(self.source)
            allowed = (PROJECT_ROOT / "data" / "videos").resolve()
            resolved = (PROJECT_ROOT / source).resolve()
            if source.is_absolute() or not resolved.is_relative_to(allowed):
                raise ValueError("Video must be a relative path inside data/videos")
            self.source = resolved.relative_to(PROJECT_ROOT).as_posix()
        return self


class SessionResponse(BaseModel):
    session_id: str
    status: Literal["RUNNING", "STOPPED", "ERROR"]
    source_type: str
    source: str = ""
    created_at: datetime | None = None
    last_error: str | None = None
