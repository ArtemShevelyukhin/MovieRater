from datetime import datetime
from typing import List
from nanoid import generate

from sqlalchemy import ForeignKey, Boolean, DateTime, Integer, String, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column()
    current_room: Mapped[str | None] = mapped_column()
    rooms: Mapped[List["Room"]] = relationship(secondary='room_members', back_populates='members')  # Many-to-Many

class Room(Base):
    __tablename__ = 'rooms'
    id: Mapped[str] = mapped_column(String(255), primary_key=True, unique=True)
    name: Mapped[str] = mapped_column()
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)  # MVP: private
    members: Mapped[List["User"]] = relationship(secondary='room_members', back_populates='rooms')  # Many-to-Many
    movies_list: Mapped[List["MoviesInRoom"]] = relationship(back_populates='room')

    # Метод для генерации ID (вызывать при создании)
    @classmethod
    def create_with_id(cls, name: str, is_private: bool = True):
        unique_id = generate(size=9)  # 21 символов, ~128 бит энтропии
        return cls(id=unique_id, name=name, is_private=is_private)

class Movie(Base):
    __tablename__ = 'movies'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    year: Mapped[int] = mapped_column()
    kinopoisk_url: Mapped[str] = mapped_column()
    kinopoisk_id: Mapped[int] = mapped_column(unique=True, index=True)
    poster_url: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Локальный URL, напр. /static/posters/movie_id.jpg
    poster_preview_url: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Локальный URL, напр. /static/posters/movie_id.jpg

class Rating(Base):
    __tablename__ = 'ratings'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id'), primary_key=True)
    score: Mapped[float] = mapped_column(Float)  # 1-10 с шагом 0.5

    user: Mapped["User"] = relationship()
    movie: Mapped["Movie"] = relationship()

class RoomMember(Base):  # Для Many-to-Many
    __tablename__ = 'room_members'
    room_id: Mapped[str] = mapped_column(ForeignKey('rooms.id'), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)

class MoviesInRoom(Base):
    __tablename__ = 'movies_in_room'
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id'), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(255), ForeignKey('rooms.id'), primary_key=True)
    added_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    added_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    discussion_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Отношения (Back-references)
    room: Mapped["Room"] = relationship(back_populates="movies_list")
    movie: Mapped["Movie"] = relationship()


