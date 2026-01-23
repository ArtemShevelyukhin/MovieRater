from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

class UserBase(BaseModel):
    telegram_id: str
    username: str

class UserCreate(UserBase):
    pass  # Для создания пользователя

class User(UserBase):
    id: int
    rooms: Optional[List["Room"]] = None  # Вложенные комнаты, optional для избежания циклов

class RoomBase(BaseModel):
    name: str
    is_private: bool = True

class RoomCreate(RoomBase):
    pass  # Для создания комнаты (id генерируется сервером)

class Room(RoomBase):
    id: str  # NanoID как str
    members: Optional[List[User]] = None  # Вложенные пользователи

class MovieBase(BaseModel):
    title: str
    year: int
    kinopoisk_url: str
    kinopoisk_id: int
    added_by: str = None
    discussion_date: Optional[datetime] = None
    poster_url: Optional[str] = None
    poster_preview_url: Optional[str] = None

class MovieCreate(BaseModel):
    kinopoisk_url: str  # Для добавления фильма
    added_by: str = None

    @field_validator("kinopoisk_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

# class Movie(MovieBase):
#     id: int
#     added_date: datetime

class RatingBase(BaseModel):
    movie_id: int
    score: float | None

    @field_validator('score')
    def validate_score(cls, value: float) -> float:
        if value is None:
            return value
        if not 1 <= value <= 10 or (value * 2) % 1 != 0:  # Шаг 0.5
            raise ValueError('Score must be between 1 and 10 with 0.5 step')
        return value

class RatingCreate(RatingBase):
    pass  # Для создания оценки

class Rating(RatingBase):
    id: int

class RoomMemberBase(BaseModel):
    room_id: int
    user_id: int

class RoomMemberCreate(RoomMemberBase):
    pass  # Для добавления члена комнаты

class RoomMember(RoomMemberBase):
    pass

class TelegramAuth(BaseModel):
    id: int  # telegram_id
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
