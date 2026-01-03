from sqlalchemy import ForeignKey, Table
from typing import List
from sqlalchemy import String, Integer, Table, Column, Float, Date
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import date

class Base(DeclarativeBase):
    pass

class Assignments(Base):
    __tablename__ ="assignments"

    id:Mapped[int] = mapped_column(primary_key=True)
    resource: Mapped[int] = mapped_column(ForeignKey("resources.id"))
    tasks: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    hours: Mapped[float] = mapped_column(nullable=False)
    mode: Mapped[str] = mapped_column(nullable=False)

class Resources(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(Integer,unique=True)
    name: Mapped[str] = mapped_column(String(30),unique=True)
    dept: Mapped[int] = mapped_column(Integer)
    skill: Mapped[str] = mapped_column(String(30))
    units: Mapped[str] = mapped_column(String(30))
    #tasks: Mapped[List['Tasks']] = relationship('Tasks',secondary=Assignments.__table__,back_populates="resources")

pred_associations = Table(
    'pred_associations',
    Base.metadata,
    Column('taskid', Integer, ForeignKey('tasks.id'), primary_key=True),
    Column('predecessorid', Integer, ForeignKey('tasks.id'), primary_key=True)
)

class Tasks(Base):
    __tablename__ = "tasks"
    #This needs to be a self referential association table.

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    duration: Mapped[float] = mapped_column(Float)
    earlystart: Mapped[date] = mapped_column(Date,nullable=True)
    latestart: Mapped[date] = mapped_column(Date,nullable=True)
    earlyfinish: Mapped[date] = mapped_column(Date,nullable=True)
    latefinish: Mapped[date] = mapped_column(Date,nullable=True)
    predecessors: Mapped[List['Tasks']] = relationship("Tasks",secondary='pred_associations',
                                                       primaryjoin=id==pred_associations.c.taskid,
                                                       secondaryjoin=id==pred_associations.c.predecessorid,
                                                       back_populates="successors")
    successors: Mapped[List['Tasks']] = relationship("Tasks",secondary='pred_associations',
                                                     primaryjoin=id==pred_associations.c.predecessorid,
                                                     secondaryjoin=id==pred_associations.c.taskid,
                                                     back_populates="predecessors")