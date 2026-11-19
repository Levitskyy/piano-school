from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CourseOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    description: str
    kind: str
    price_minor: int | None
    currency: str
    mentorship_days: int | None
    is_active: bool


class LessonSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    description: str
    position: int
    duration_seconds: int | None


class LessonMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    kind: str
    url: str | None


class ModuleOut(BaseModel):
    id: UUID
    title: str
    description: str
    position: int
    lessons: list[LessonSummaryOut]


class CourseSummaryOut(BaseModel):
    id: UUID
    slug: str
    title: str
    subtitle: str | None
    description: str
    level: str
    cover_url: str | None
    offers: list[CourseOfferOut]


class CourseOut(CourseSummaryOut):
    modules: list[ModuleOut]


class CourseAccessOut(BaseModel):
    id: UUID
    source: str
    starts_at: datetime
    expires_at: datetime | None
    mentorship_ends_at: datetime | None
    offer: CourseOfferOut | None


class AccountCourseOut(BaseModel):
    access: CourseAccessOut
    course: CourseSummaryOut
    completed_lessons: int
    total_lessons: int


class ProgressOut(BaseModel):
    status: str
    last_position_seconds: int = Field(ge=0)
    completed_at: datetime | None


class LessonDetailOut(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    duration_seconds: int | None
    module_title: str
    course_slug: str
    course_title: str
    materials: list[LessonMaterialOut]
    progress: ProgressOut | None


class ProgressUpdateIn(BaseModel):
    status: str = Field(pattern="^(not_started|in_progress|completed)$")
    last_position_seconds: int = Field(default=0, ge=0)
