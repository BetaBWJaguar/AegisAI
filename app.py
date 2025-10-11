from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, HTTPException

from error.expectionhandler import ExpectionHandler, expection_handler, validation_exception_handler, \
    http_exception_handler
from ratelimit.ratelimit import RateLimitMiddleware
from user.usercontroller import router as user_router
from auth.authcontroller import router as auth_router
from workspace.workspacecontroller import router as workspace_router
from dataset_builder.dataset_builder_controller import router as dataset_router
from template.templatecontroller import router as template_router
from data_scraper.scrapper_controller import router as scrapper_router
from auditmanager.auditlog_controller import router as audit_router


app = FastAPI()
app.add_middleware(RateLimitMiddleware, max_requests=5, window_seconds=10)

app.add_exception_handler(ExpectionHandler, expection_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(auth_router, prefix="/auth", tags=["users"])
app.include_router(workspace_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(dataset_router, prefix="/datasets", tags=["datasets"])
app.include_router(template_router,prefix="/templates", tags=["templates"])
app.include_router(scrapper_router, prefix="/scrapper", tags=["scrapper"])
app.include_router(audit_router,prefix="/auditlog", tags=["auditlog"])

