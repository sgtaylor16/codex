from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from tables.tables import Base
from tables.tables import Resources, Tasks, Assignments



engine =create_engine('sqlite:///codex.db')

Session = sessionmaker(engine)

def createdb():
    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.create_all(engine)


