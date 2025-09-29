from fastapi import FastAPI
from user.usercontroller import router as user_router
from auth.authcontroller import router as auth_router
from workspace.workspacecontroller import router as workspace_router


app = FastAPI()


app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(auth_router, prefix="/auth", tags=["users"])
app.include_router(workspace_router, prefix="/workspaces", tags=["workspaces"])

