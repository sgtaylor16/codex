from sqlalchemy import ForeignKey
from typing import List
from sqlalchemy import String, Integer, Table, Column, Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class Assignments(Base):
    __tablename__ ="assignments"

    id:Mapped[int] = mapped_column(primary_key=True)
    resource: Mapped[int] = mapped_column(ForeignKey("resources.id"))
    tasks: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    hours: Mapped[float] = mapped_column()

class Resources(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30),unique=True)
    dept: Mapped[int] = mapped_column(Integer)
    skill: Mapped[str] = mapped_column(String(30))
    units: Mapped[str] = mapped_column(String(30))
    tasks: Mapped[List['Tasks']] = relationship('Tasks',secondary=Assignments.__table__,back_populates="resources")

class Tasks(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30),unique=True)
    enddate: Mapped[str] = mapped_column(String(30))
    startdate: Mapped[str] = mapped_column(String(30))
    resources: Mapped[List['Resources']] = relationship('Resources',secondary=Assignments.__table__,back_populates="tasks")