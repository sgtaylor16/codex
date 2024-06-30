from dateutil.parser import parse
from tables.tables import Resources,Tasks
from orm import Session
from sqlalchemy import select

def is_date(string, fuzzy=False) -> bool:
    """
    Return whether the string can be interpreted as a date.
    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

def is_Resource(resource:str) -> bool:
    stmt = select(Resources).where(Resources.name == resource)
    with Session() as session:
        results = session.execute(stmt).all()
    if len(results) == 1:
        return True
    else:
        return False
    
def get_ResourceNumber(resourcename:str) -> int:
    if is_Resource(resourcename):
        stmt = select(Resources.id).where(Resources.name == resourcename)
        with Session() as session:
            return session.execute(stmt).one()[0]
    else:
        raise ValueError

def is_Task(task:str) -> bool:
    stmt = select(Tasks).where(Tasks.name == task)
    with Session() as session:
        results = session.execute(stmt).all()
    if len(results) == 1:
        return True
    else:
        return False
    
def get_TaskNumber(taskname:str) -> int:
    if is_Task(taskname):
        stmt = select(Tasks.id).where(Tasks.name == taskname)
        with Session() as session:
            return session.execute(stmt).one()[0]
    else:
        raise ValueError
            

        
