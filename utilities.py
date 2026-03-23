from tables.tables import Resources,Assignments, Tasks,pred_associations, ProjectData
from orm import Session
from datetime import datetime,date
from dateutil.parser import parse
import numpy as np
import pandas as pd
from typing import List
from checks import get_ResourceNumber, get_TaskNumber
from sqlalchemy import select
import json
import plotly.express as px

def checkcolumns(df:pd.DataFrame, requiredcolumns:List[str]) -> bool:
    for col in requiredcolumns:
        if col not in df.columns:
            return False
    return True

def ReadInTasks(filename:str):
    """
    Reads in tasks from a csv file and adds them to the database. The csv file must have the following columns:
    - id: unique identifier for the task
    - name: name of the task
    - duration: duration of the task in days
    - earlystart: (optional) early start date of the task in YYYY-MM-DD format
    """
    df = pd.read_csv(filename)
    requiredcolumns = ['id','name','duration','earlystart']
    if not checkcolumns(df,requiredcolumns):
        raise ValueError("Missing required columns in tasks file")
    for index, row in df.iterrows():
        with Session() as session:
            Task1 = Tasks(id = row['id'],
                          name = row['name'],
                          duration = int(row['duration']),
                          earlystart = parse(row['earlystart']).date() if pd.notna(row['earlystart']) else None)
            session.add_all([Task1])
            session.commit()

def ReadInPredecessors(filename:str):
    """Reads in predecessors from a csv file and adds them to the database. The csv file must have the following columns:
    - id: unique identifier for the predecessor relationship
    - task_id: id of the task
    - predecessor_id: id of the predecessor task
    """
    requiredcolumns = ['id','task_id','predecessor_id']
    df = pd.read_csv(filename)
    if not checkcolumns(df,requiredcolumns):
        raise ValueError("Missing required columns in predecessors file")
    with Session() as session:
        for index, row in df.iterrows():
            task= session.query(Tasks).filter_by(id=int(row['task_id'])).first()
            predecessor= session.query(Tasks).filter_by(id=int(row['predecessor_id'])).first()
            task.predecessors.append(predecessor)
        session.commit()

def ReadInResources(filename:str):
    """Reads in resources from a csv file and adds them to the database. The csv file must have the following columns:
    - id: unique identifier for the resource
    - name: name of the resource
    - dept: department of the resource
    - skill: skill of the resource
    - units: units of the resource (e.g. 1 for full-time, 0.5 for half-time)
    """
    requiredcolumns = ['id','name','dept','skill','units']
    df = pd.read_csv(filename)
    if not checkcolumns(df,requiredcolumns):
        raise ValueError("Missing required columns in resources file")

    for index, row in df.iterrows():
        with Session() as session:
            Resource1 = Resources(id = row['id'],
                                  name = row['name'],
                                  dept = row['dept'],
                                  skill = row['skill'],
                                  units = row['units'])
            session.add_all([Resource1])
            session.commit()

def ReadInAssignments(filename:str):
    """Reads in assignments from a csv file and adds them to the database. The csv file must have the following columns:
    - id: unique identifier for the assignment
    - task: id of the task
    - resource: id of the resource
    - hours: number of hours assigned
    - mode: 'total' or 'level' (if 'total', hours are spread evenly across the duration of the task; if 'level', hours are spread according to the resource's availability)
    """
    requiredcolumns = ['id','task_id','resource_id','hours','mode']
    allowedmodes = ['total','level']
    df = pd.read_csv(filename)

    if not all(df['mode'].isin(allowedmodes)):
        raise ValueError("Invalid mode in assignments file. Allowed modes are 'total' and 'level'")
    
    if not checkcolumns(df,requiredcolumns):
        raise ValueError("Missing required columns in assignments file")
    for index, row in df.iterrows():
        with Session() as session:
            Assn1 = Assignments(id = row['id'],
                                resource = session.query(Resources).filter_by(id=int(row['resource_id'])).first(), 
                                task = session.query(Tasks).filter_by(id=int(row['task_id'])).first(),
                                hours = row['hours'],
                                mode = row['mode'])
            session.add_all([Assn1])
            session.commit()

def populatedb(tables:dict[str,str], dbdelete:bool=False):
    """Populates the database with resources, tasks, predecessors, and assignments from csv files."""
    if dbdelete:
        with Session() as session:
            session.query(Assignments).delete()
            session.query(pred_associations).delete()
            session.query(Tasks).delete()
            session.query(Resources).delete()
            session.query(ProjectData).delete()
            session.commit()

    if 'tasks' in tables.keys():
            ReadInTasks(tables['tasks'])
            print("Tasks read in successfully")

    if 'resources' in tables.keys():
            ReadInResources(tables['resources'])
            print("Resources read in successfully")

    if 'predecessors' in tables.keys():
            ReadInPredecessors(tables['predecessors'])
            print("Predecessors read in successfully")

    if 'assignments' in tables.keys():
            ReadInAssignments(tables['assignments'])
            print("Assignments read in successfully")

def createHoursTable() -> pd.DataFrame:
    """Creates a pandas dataframe with resources as rows and APs as columns, with the values being the number of hours assigned to each resource in each AP."""
    df = pd.DataFrame(columns = APindex(getMinDate(),getMaxDate()))
    stmt = select(Assignments)

    with Session() as session:
        results = session.scalars(stmt).all()
        for result in results:
            #Get Task
            task = session.scalars(select(Tasks).filter_by(id=result.task_id)).all()[0]
            #Get Resource
            resource = session.scalars(select(Resources).filter_by(id=result.resource_id)).all()[0]
            #Get Hours
            hours = result.totalhours
            #get Mode
            if result.mode.lower() == 'total':
                tempdf = pd.DataFrame(columns=APindex(task.earlystart,task.earlyfinish),index=[resource.name], data=[calcHoursinMonth(task.earlystart,task.earlyfinish,hours)])
            elif result.mode.lower() == 'level':
                tempdf = pd.DataFrame(columns=APindex(task.earlystart,task.earlyfinish),index=[resource.name], data=[calcHoursinMonthLevel(task.earlystart,task.earlyfinish,hours)])
            else:
                raise ValueError("mode not total or level")
            df = pd.concat([df,tempdf],axis=0).fillna(0)

    return df

def countMonths(startdate:date,enddate:date) -> int:
    """Counts the number of months between two dates, inclusive"""
    if (startdate.month == enddate.month) and (startdate.year == enddate.year):
        return 1
    elif (startdate.year == enddate.year):
        return enddate.month - startdate.month + 1
    elif (enddate.year - startdate.year) > 0:
        return enddate.month + (13 - enddate.month) + 12*(startdate.year - startdate.year - 1)
    
def addzero(x:str) -> str:
    if len(x) == 1:
        return '0' + str(x)
    else:
        return x
    
def calcHoursinMonth(startdate:date,enddate:date,hours:float) -> List[int]:
    """
    Returns a list of hours in each month. Total will equal hours
    """
    # Create a sample date range
    date_frame = pd.date_range(startdate,enddate, freq='B').to_frame()
    date_frame['AP'] = date_frame[0].apply(lambda x: str(x.year) + addzero(str(x.month)))

    hourmult = float(hours / date_frame['AP'].value_counts().sum() )
    daylist = date_frame['AP'].value_counts().sort_index().to_list()
    return [hourmult * x for x in daylist]

def calcHoursinMonthLevel(startdate:date,enddate:date,fte:float) -> List[float]:
    """Returns a list of hours in each month. Total will equal fte * 8 * number of business days"""
    date_frame = pd.date_range(startdate,enddate,freq="B").to_frame()
    date_frame['AP'] = date_frame[0].apply(lambda x: str(x.year) + addzero(str(x.month)))
    date_frame['Hours'] = fte * 8.0
    return date_frame['Hours'].groupby(date_frame['AP']).sum().to_list()

def getDate(option:str) -> date:
    startstmt = select(Tasks.earlystart)
    endstmt = select(Tasks.earlyfinish)
    with Session() as session:
        results_start = session.scalars(startstmt).fetchall()
        results_end = session.scalars(endstmt).fetchall()
        results = results_start + results_end
    if option == 'min':
        return min([x for x in results])
    elif option =='max':
        return max([x for x in results])

def getMinDate() -> date:
    return getDate('min')

def getMaxDate() -> date:
    return getDate('max')

def dtToAP(date:date) -> str:
    year = str(date.year)
    month = str(date.month)
    if len(month) == 1:
        month = '0' + month
    return int(year + month)

def APindex(startdate:date,enddate:date) -> List[str]:
    """Returns a list of APs between two dates, inclusive"""
    beginDate = date(startdate.year,startdate.month,1)
    datelist = pd.date_range(beginDate,enddate,freq='MS').to_list()
    return [dtToAP(x) for x in datelist]

def createTable() -> pd.DataFrame:
    """
    Returns a pandas dataframe suitable to input into a loading
    """

    df = pd.DataFrame(columns = APindex(getMinDate(),getMaxDate()))

    with Session() as session:
        results = session.scalars(select(Assignments)).all()
        for result in results:
            #Get Task
            task = session.scalars(select(Tasks).filter_by(id=result.task_id)).all()[0]
            starttask = parse(task.earlystart)
            endtask = parse(task.earlyfinish)
            #Get Resource
            resource = session.scalars(select(Resources).filter_by(id=result.resource_id)).all()[0]
            #Get Hours
            hours = result.hours
            #get Mode
            if result.mode.lower() == 'total':
                tempdf = pd.DataFrame(columns=APindex(starttask,endtask),index=[resource.name], data=[calcHoursinMonth(starttask,endtask,hours)])
            elif result.mode.lower() == 'level':
                tempdf = pd.DataFrame(columns=APindex(starttask,endtask),index=[resource.name], data=[calcHoursinMonthLevel(starttask,endtask,hours)])
            else:
                raise ValueError("mode not total or level")
            df = pd.concat([df,tempdf],axis=0).fillna(0)

    return df

def findSuccessors(task:Tasks,session) -> List[Tasks]: 
    """Returns a list of successor tasks for a given task"""
    stmt = select(Tasks).where(Tasks.predecessors.contains(task)) # type: ignore
    suctasks = session.execute(stmt).scalars().all()
    return suctasks

def gantt_from_json(filename: str) -> None:
    """
    Renders an interactive Plotly Gantt chart from a JSON schedule file.

    The JSON file should be a list of task objects with the fields:
        id, name, duration, earlystart, earlyfinish, predecessors

    Example usage:
        gantt_from_json("trial.json")
    """
    with open(filename, "r") as f:
        tasks = json.load(f)

    df = pd.DataFrame(tasks)[["id", "name", "earlystart", "earlyfinish"]]
    df = df.dropna(subset=["earlystart", "earlyfinish"])
    df = df[df["earlystart"] != ""]
    df["Task"] = df["id"].astype(str) + ": " + df["name"]
    df = df.sort_values(["earlystart", "id"]).reset_index(drop=True)

    fig = px.timeline(
        df,
        x_start="earlystart",
        x_end="earlyfinish",
        y="Task",
        title="Project Schedule",
        template="plotly_white",
    )
    fig.update_yaxes(autorange="reversed")
    fig.show()




    
        
        





    