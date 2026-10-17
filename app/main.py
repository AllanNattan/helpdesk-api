from fastapi import FastAPI

app = FastAPI(
    title="HelpDesk API",
    description="API REST para gerenciamento de chamados de suporte técnico.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}