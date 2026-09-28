from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.exams import router as exams_router
from app.routers.questions import router as questions_router


app = FastAPI(title="AI OSM Examination System")

app.include_router(auth_router)
app.include_router(exams_router)
app.include_router(questions_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AI OSM Examination System backend is running"
    }