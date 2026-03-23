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
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"),nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"),nullable=False)
    hours: Mapped[float] = mapped_column(nullable=False)
    mode: Mapped[str] = mapped_column(String(30),default='total')
    resource: Mapped["Resources"] = relationship("Resources", back_populates="assignments")
    task: Mapped["Tasks"] = relationship("Tasks", back_populates="assignments")

class Resources(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30),unique=True,nullable=False)
    dept: Mapped[int] = mapped_column(Integer)
    skill: Mapped[str] = mapped_column(String(30))
    units: Mapped[str] = mapped_column(String(30))
    assignments: Mapped[List[Assignments]] = relationship("Assignments",back_populates="resource")

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
    assignments: Mapped[List[Assignments]] = relationship("Assignments", back_populates="task")
    
class ProjectData(Base):
    __tablename__ = "projectdata"
    id: Mapped[int] = mapped_column(primary_key=True)
    projstart: Mapped[date] = mapped_column(Date,nullable=False)