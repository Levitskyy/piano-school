from fastapi import APIRouter

from app.api.routes import account, admin, auth, courses, individual_lessons

router = APIRouter()


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


router.include_router(auth.router)
router.include_router(account.router)
router.include_router(courses.router)
router.include_router(individual_lessons.router)
router.include_router(admin.router)
