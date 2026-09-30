from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.exams import router as exams_router
from app.routers.questions import router as questions_router
from app.routers.sheets import router as sheets_router
from app.routers.ocr import router as ocr_router
from app.routers.allocation import router as allocation_router
from app.routers.examiner import router as examiner_router
from app.routers.marks import router as marks_router
from app.routers.submission import router as submission_router
from app.routers.ai import router as ai_router
from app.routers import annotations
from app.routers.flags import router as flags_router
from app.routers.analytics import router as analytics_router
from app.routers.moderation import router as moderation_router
from app.routers.audit import router as audit_router
from app.routers.results import router as results_router


app = FastAPI(title="AI OSM Examination System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(exams_router)
app.include_router(questions_router)
app.include_router(sheets_router)
app.include_router(ocr_router)
app.include_router(allocation_router)
app.include_router(examiner_router)
app.include_router(marks_router)
app.include_router(submission_router)
app.include_router(ai_router)
app.include_router(annotations.router)
app.include_router(flags_router)
app.include_router(analytics_router)
app.include_router(moderation_router)
app.include_router(audit_router)
app.include_router(results_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AI OSM Examination System backend is running"
    }
