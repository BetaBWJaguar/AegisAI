from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, HTTPException

from error.expectionhandler import ExpectionHandler, expection_handler, validation_exception_handler, http_exception_handler
from ratelimit.ratelimit import RateLimitMiddleware
from user.usercontroller import router as user_router
from auth.authcontroller import router as auth_router
from user.utility.failedloginattempt_service import FailedLoginAttemptService
from utility.client_ip_middleware import ClientIPMiddleware
from workspace.workspacecontroller import router as workspace_router
from dataset_builder.dataset_builder_controller import router as dataset_router
from template.templatecontroller import router as template_router
from data_scraper.scrapper_controller import router as scrapper_router
from auditmanager.auditlog_controller import router as audit_router
from device.devicecontroller import router as device_router
from revokedtokenservice.revoked_token_service import RevokedTokenService
from multilangsetup.multilang_controller import router as multilang_router


app = FastAPI()
app.add_middleware(RateLimitMiddleware, max_requests=5, window_seconds=10)
app.add_middleware(ClientIPMiddleware)

app.add_exception_handler(ExpectionHandler, expection_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(multilang_router, prefix="/multilang", tags=["multilang"])
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(workspace_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(dataset_router, prefix="/datasets", tags=["datasets"])
app.include_router(template_router,prefix="/templates", tags=["templates"])
app.include_router(scrapper_router, prefix="/scrapper", tags=["scrapper"])
app.include_router(audit_router,prefix="/auditlog", tags=["auditlog"])
app.include_router(device_router, prefix="/devices", tags=["devices"])

revoked_service = RevokedTokenService("config.json")
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(revoked_service.cleanup_expired, "interval", hours=1)
    scheduler.add_job(FailedLoginAttemptService.remove_expired_attempts_for_all_users,"interval", minutes=10)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
