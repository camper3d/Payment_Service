from fastapi import FastAPI
from app.api import payments
from app.middleware.auth import APIKeyMiddleware

app = FastAPI(
    title="Payment Processing Service",
    description="Cервис процессинга платежей",
    version="1.0.0"
)

app.add_middleware(APIKeyMiddleware)
app.include_router(payments.router)


@app.get("/health")
async def health_check():
    return {"status": "OK"}