from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.internships import router as internships_router
from app.api.career_paths import router as career_paths_router
from app.api.feedback import router as feedback_router
from app.api.recommendations import router as recommendations_router
from app.api.resume import router as resume_router
from app.api.students import router as students_router
from app.core.config import settings
from app.core.database import engine


app = FastAPI(title="InternAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students_router)
app.include_router(auth_router)
app.include_router(career_paths_router)
app.include_router(feedback_router)
app.include_router(internships_router)
app.include_router(recommendations_router)
app.include_router(resume_router)


@app.get("/api/health")
def health() -> dict[str, bool | str]:
    db_connected = False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        pass

    return {"status": "ok", "db_connected": db_connected}
