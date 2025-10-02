from fastapi import FastAPI

from ratelimit.ratelimit import RateLimitMiddleware
from user.usercontroller import router as user_router
from auth.authcontroller import router as auth_router
from workspace.workspacecontroller import router as workspace_router
from dataset_builder.dataset_builder_controller import router as dataset_router


app = FastAPI()
app.add_middleware(RateLimitMiddleware, max_requests=5, window_seconds=10)


app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(auth_router, prefix="/auth", tags=["users"])
app.include_router(workspace_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(dataset_router, prefix="/datasets", tags=["datasets"])

