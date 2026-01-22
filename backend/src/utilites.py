import asyncio
import json
import os
import urllib
from datetime import datetime
from typing import Optional, Any, Annotated
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Header, Request
from httpx import Response
from sqlalchemy.orm import Session

from database import get_db
from models import Movie, User
from schemas import MovieCreate, MovieBase


async def get_movie_info_from_kp_url(create_movie_data: MovieCreate) -> Movie:
    """
    Получает информацию о фильме по ссылке Кинопоиск

    Примеры url:
    - https://www.kinopoisk.ru/film/4926453/
    - https://www.kinopoisk.ru/series/1234567/

    Возвращает: MovieBase или поднимает исключение
    """
    film_url = create_movie_data.kinopoisk_url
    load_dotenv()
    KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")
    KINOPOISK_API_BASE_URL = os.getenv('KINOPOISK_API_BASE_URL')
    KINOPOISK_API_VERSION = os.getenv('KINOPOISK_API_VERSION')

    if not ("kinopoisk.ru/film/" in film_url or "kinopoisk.ru/series/" in film_url):
        raise ValueError("Некорректная ссылка на Кинопоиск")

    try:
        parsed_url = urlparse(film_url)
        film_id = int(parsed_url.path.strip("/").split("/")[-1])
    except (ValueError, IndexError):
        raise ValueError(f"Не удалось извлечь ID фильма из ссылки: {film_url}")

    try:
        response = await get_film_data_from_kinopoisk(KINOPOISK_API_BASE_URL, KINOPOISK_API_KEY, KINOPOISK_API_VERSION, film_id)

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Некорректный JSON от Kinopoisk API")

        try:
            poster_url = data['posterUrl']
            poster_url_preview = data['posterUrlPreview']

            movie_data = Movie(
                title=data['nameRu'],
                year=data['year'],
                kinopoisk_url=data['webUrl'].strip('/'),
                kinopoisk_id=data['kinopoiskId'],
                poster_url=await download_and_save_film_poster(poster_url, data['kinopoiskId']),
                poster_preview_url=await download_and_save_film_poster(poster_url_preview, data['kinopoiskId'], 'preview')
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Ошибка валидации данных фильма: {str(e)}")

    except Exception as e:
        raise RuntimeError(f"Неизвестная ошибка при получении данных фильма {film_url}: {e}")

    return movie_data


async def get_film_data_from_kinopoisk(KINOPOISK_API_BASE_URL: str | None, KINOPOISK_API_KEY: str | None, KINOPOISK_API_VERSION: str | None, film_id: int) -> Response:
    url = f"{KINOPOISK_API_BASE_URL}/{KINOPOISK_API_VERSION}/films/{film_id}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": KINOPOISK_API_KEY,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="External API unavailable",
        )
    return response


async def download_and_save_film_poster(poster_url, film_id, suffix = '') -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(poster_url, follow_redirects=True, timeout=10.0)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="External API unavailable",
        )

    extension = poster_url.split('.')[-1]
    file_name = f"{film_id}{suffix}.{extension}"
    file_path = os.path.join('static', 'film_posters', file_name)

    with open(file_path, 'wb+') as f:
        f.write(response.content)  # content — байты ответа
    return file_path

#
# if __name__ == '__main__':
#     asyncio.run(get_movie_info_from_kp_url('https://www.kinopoisk.ru/film/4926453/?utm_referrer=www.google.com'))

def parse_init_data(init_data: str) -> dict:
    return {k: v for k, v in [pair.split('=') for pair in init_data.split('&')]}


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    # 1. Сначала ищем в Query-параметрах (наш новый способ)
    encoded_init_data = request.query_params.get("_auth")

    if encoded_init_data:
        init_data = urllib.parse.unquote(encoded_init_data)
    else:
        # 2. Если нет в URL, ищем в заголовках (для fetch)
        init_data = request.headers.get("X-Telegram-Init-Data")
    telegram_data = parse_init_data(init_data)

    user_data_str = telegram_data.get("user")
    if not user_data_str:
        raise HTTPException(401, "Invalid initData")

    user_data = json.loads(urllib.parse.unquote(user_data_str))
    telegram_id = str(user_data.get("id"))

    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=telegram_data.get("username"),
            current_room=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user