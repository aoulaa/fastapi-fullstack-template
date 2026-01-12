from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

from .health import router as health_router
from .items import router as items_router
from .login import router as login_router
from .logout import router as logout_router
from .tasks import router as tasks_router
from .users import router as users_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(login_router)
router.include_router(logout_router, dependencies=[Depends(get_current_user)])
router.include_router(users_router, dependencies=[Depends(get_current_user)])
router.include_router(tasks_router, dependencies=[Depends(get_current_user)])
router.include_router(items_router, dependencies=[Depends(get_current_user)])
