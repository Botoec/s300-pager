from fastapi import FastAPI, Body
from pydantic import BaseModel
import structlog
from telegram_bot.application.services import AuthService

logger = structlog.get_logger()

class QrData(BaseModel):
    qr_data: str
    user_id: int

def create_webapp_adapter(auth_service: AuthService):
    app = FastAPI()

    @app.post("/qr-scan")
    async def receive_qr(data: QrData = Body(...)):
        logger.info("Received QR from webapp", user_id=data.user_id)
        await auth_service.handle_qr_scan(data.qr_data, data.user_id)
        return {"status": "processed"}

    return app