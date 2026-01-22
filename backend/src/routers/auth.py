import hashlib
import hmac
import json
import os
import urllib.parse

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Annotated

from starlette.responses import HTMLResponse
from fastapi import Request
from starlette.templating import Jinja2Templates

from database import get_db
from models import Movie, Room, User
from utilites import parse_init_data
from schemas import MovieCreate, TelegramAuth  # создадим схемы ниже
from utilites import get_movie_info_from_kp_url
# from ..dependencies import get_current_user  # пока закомментируем или сделаем заглушку
templates = Jinja2Templates(directory="templates")

load_dotenv()  # Уже есть в database.py, но для безопасности
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

auth = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}}
)

def validate_telegram_hash(data: TelegramAuth) -> bool:
    """Проверка хэша от Telegram (из docs.telegram.org)."""
    check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.dict(exclude={'hash': True}).items()) if v is not None])
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return calculated_hash == data.hash


@auth.post("/validate-mini-app")
def validate_mini_app(db: Session = Depends(get_db)):
    parsed_data = parse_init_data(data.init_data)
    user_str = parsed_data.get('user')
    if not user_str:
        raise HTTPException(401, "Invalid initData")
    user_data = json.loads(urllib.parse.unquote(user_str))

    auth_data = TelegramAuth(  # Используйте схему из предыдущего ответа
        id=int(user_data['id']),
        username=user_data.get('username'),
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name'),
        auth_date=int(parsed_data['auth_date']),
        hash=parsed_data['hash']
    )

    if not validate_telegram_hash(auth_data):
        raise HTTPException(401, "Invalid hash")

    # Создайте/обновите пользователя в DB (как в /auth/telegram)
    return {"valid": True, "user_id": auth_data.id}