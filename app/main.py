from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router

app = FastAPI(
    title="HelpDesk API",
    description="API REST para gerenciamento de chamados de suporte técnico.",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(tickets_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}