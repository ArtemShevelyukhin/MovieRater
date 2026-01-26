import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, FileResponse
from starlette.templating import Jinja2Templates

from models import Base, User, Room  # Импорт моделей
from database import engine, get_db  # Файл database.py с настройкой сессий
from schemas import RoomCreate
from routers import rooms, auth
app = FastAPI()

app.include_router(rooms.rooms)
app.include_router(auth.auth)
app.mount("/templates", StaticFiles(directory="templates", html=True), name="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # Создать таблицы

# @app.on_event("shutdown")
# def on_shutdown():
#     Base.metadata.drop_all(bind=engine)

@app.post("/auth/register")
def register(telegram_token: str, db: Session = Depends(get_db)):
    # Логика: Валидировать token с Telegram API, создать user
    user = User(telegram_id=telegram_token, username="example")
    db.add(user)
    db.commit()
    return {"message": "User registered"}

@app.get("/", response_class=HTMLResponse)
def hello_world():
    print('RUN: main.py -> hello_world')
    return FileResponse("templates/index.html")




@app.post("/rooms/{room_id}/movies/add")
def add_movie(room_id: int, kinopoisk_url: str, db: Session = Depends(get_db)):
    # Логика: Парсинг URL (используйте beautifulsoup4 для scraping)
    # Добавьте movie в БД, привяжите к room
    return {"message": "PASS"}  # Реализуйте

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)