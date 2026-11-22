from fastapi import APIRouter

from app.api.routes import (
    account,
    admin,
    auth,
    courses,
    individual_lessons,
    payments,
    teacher,
)
from app.config import get_settings

router = APIRouter()


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


router.include_router(auth.router)
router.include_router(account.router)
if get_settings().courses_enabled:
    router.include_router(courses.router)
router.include_router(individual_lessons.router)
router.include_router(payments.router)
router.include_router(teacher.router)
router.include_router(admin.router)
