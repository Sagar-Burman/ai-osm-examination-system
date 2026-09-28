from fastapi import FastAPI

app = FastAPI(title="AI OSM Examination System")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AI OSM Examination System backend is running"
    }