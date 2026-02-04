from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import ForeignKey, Integer, create_mock_engine, create_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, Session


class Base(DeclarativeBase):
    pass

class Hero(Base):
    __tablename__ = "hero"
    id: Mapped[int | None] = mapped_column(default=None, primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    age: Mapped[int | None] = mapped_column(default=None, index=True)
    secret_name: Mapped[str] = mapped_column()

    def __str__(self):
        return f'Name: {self.name}, Age: {self.age}'

if __name__ == '__main__':
    h = Hero(name='Fro', age=25, secret_name='Sty')

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(h)
        session.commit()

    with Session(engine) as session:
        hero = session.query(Hero).where(Hero.name == 'Fro').one()
        print(hero)
        hero.name = "qwe"
        session.commit()

    with Session(engine) as session:
        hero_all = session.query(Hero).all()
        for hero in hero_all:
            print(hero)
