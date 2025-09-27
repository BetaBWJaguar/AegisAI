from fastapi import FastAPI
from user.usercontroller import router as user_router


app = FastAPI()


app.include_router(user_router, prefix="/users", tags=["users"])
