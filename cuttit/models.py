"""Data passed between the pipeline steps."""

from pydantic import BaseModel, Field


class Segment(BaseModel):
    """One spoken sentence or phrase, timed in seconds from the start of its clip."""
    start: float
    end: float
    text: str


class ClipTranscript(BaseModel):
    clip: int                      # index into the job's clip list
    duration: float
    language: str = "ml"
    segments: list[Segment] = Field(default_factory=list)


class KeepRange(BaseModel):
    """A piece of one source clip that goes into the final video, in output order."""
    clip: int
    start: float
    end: float


class EditPlan(BaseModel):
    """What Claude decides. The renderer turns this into a video."""
    keep: list[KeepRange]
    hook_text: str = ""            # short on-screen title for the first seconds; empty for none
    notes: str = ""                # one line on what was cut and why, shown to the reviewer


class CaptionLine(BaseModel):
    """A caption on the output timeline."""
    start: float
    end: float
    text: str
