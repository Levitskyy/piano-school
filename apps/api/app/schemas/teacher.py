from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class TeacherLessonBookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    student_name: str
    student_email: str
    offer_title: str
    status: str
    starts_at: datetime
    ends_at: datetime
    meeting_url: str | None
    created_at: datetime


class TeacherLessonUpdateIn(BaseModel):
    meeting_url: HttpUrl | None
