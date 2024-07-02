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

        with Session() as session:
            resource1= Resources(name='Stress',dept='85194',skill='DEF',units='Hours')
            
            Task1 = Tasks(name='Kick-Off',startdate = '3/14/24',enddate='6/15/24')
            Task2 = Tasks(name="Design",startdate='7/15/24',enddate='10/5/24')

            session.add_all([resource1,Task1,Task2])
            session.commit()

