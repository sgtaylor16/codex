from tables.tables import Resources,Assignments, Tasks
from orm import Session
from datetime import datetime,date
from dateutil.parser import parse
import numpy as np
import pandas as pd
from typing import List
from checks import get_ResourceNumber, get_TaskNumber
from sqlalchemy import select

def ReadInTasks(filename:str):
    return None 

def AddResource(TaskUID,ResourceName,hours):
    return None

def countMonths(startdate:date,enddate:date) -> int:
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
    print(date_frame['AP'].value_counts().sort_index().to_list())

    hourmult = float(hours / date_frame['AP'].value_counts().sum() )
    daylist = date_frame['AP'].value_counts().sort_index().to_list()
    return [hourmult * x for x in daylist]

def calcHoursinMonthLevel(startdate:date,enddate:date,fte:float) -> List[float]:
    date_frame = pd.date_range(startdate,enddate,freq="B").to_frame()
    date_frame['AP'] = date_frame[0].apply(lambda x: str(x.year) + addzero(str(x.month)))
    date_frame['Hours'] = fte * 8.0
    return date_frame['Hours'].groupby(date_frame['AP']).sum().to_list()

def addAssignment(taskname,resourcename,hours):
    tasknumber = get_TaskNumber(taskname)
    resourcenumber = get_ResourceNumber(resourcename)
    with Session() as session:
        Assn1 = Assignments(resource = resourcenumber, tasks=tasknumber, hours = hours)

        session.add_all([Assn1])
        session.commit()

def getDate(option:str):
    startstmt = select(Tasks.startdate)
    endstmt = select(Tasks.enddate)
    with Session() as session:
        results_start = session.scalars(startstmt).fetchall()
        results_end = session.scalars(endstmt).fetchall()
        results = results_start + results_end
    if option == 'min':
        return min([parse(x) for x in results])
    elif option =='max':
        return max([parse(x) for x in results])

def getMinDate():
    return getDate('min')

def getMaxDate():
    return getDate('max')

def dtToAP(date:date) -> str:
    year = str(date.year)
    month = str(date.month)
    if len(month) == 1:
        month = '0' + month
    return int(year + month)

def dateIndex(startdate:date,enddate:date):
    beginDate = date(startdate.year,startdate.month,1)
    datelist = pd.date_range(beginDate,enddate,freq='MS').to_list()
    return [dtToAP(x) for x in datelist]

def readTasks(filename:str,map:dict=None):
    taskslist = pd.read_csv(filename)
    if map != None:
        tasklist = tasklist.rename(mapper=map,axis=1)
    taskslist = taskslist[['name','startdate','enddate']].to_dict(orient='records')
    instances = [Tasks(**row) for row in taskslist]
    with Session() as session:
        session.add_all(instances)
        session.commit()

def readResources(filename:str,map:dict=None):
    resourcelist = pd.read_csv(filename)
    if map != None:
        resourcelist = resourcelist.rename(mapper=map,axis=1)
    resourcelist = resourcelist[['name','dept','skill','units']].to_dict(orient='records')
    instances = [Resources(**row) for row in resourcelist]
    with Session() as session:
        session.add_all(instances)
        session.commit()

def readAssignments(filename:str,map:dict=None):
    assignlist = pd.read_csv(filename)
    if map != None:
        assignlist = assignlist.rename(mapper=map,axis=1)
    assignlist['tasks'] = assignlist['tasks'].apply(get_TaskNumber)
    assignlist['resource'] = assignlist['resource'].apply(get_ResourceNumber)
    assignlist= assignlist[['tasks','resource','hours','mode']].to_dict(orient='records')
    instances = [Assignments(**row) for row in assignlist]
    with Session() as session:
        session.add_all(instances)
        session.commit()

def createTable() -> pd.DataFrame:
    """
    Returns a pandas dataframe suitable to input into a loading
    """

    df = pd.DataFrame(columns = dateIndex(getMinDate(),getMaxDate()))
    stmt = select(Assignments)

    with Session() as session:
        results = session.scalars(stmt).all()
        for result in results:
            #Get Task
            task = session.scalars(select(Tasks).filter_by(id=result.tasks)).all()[0]
            starttask = parse(task.startdate)
            endtask = parse(task.enddate)
            #Get Resource
            resource = session.scalars(select(Resources).filter_by(id=result.tasks)).all()[0]
            #Get Hours
            hours = result.hours
            #get Mode
            if result.mode.lower() == 'total':
                tempdf = pd.DataFrame(columns=dateIndex(starttask,endtask),index=[resource.name], data=[calcHoursinMonth(starttask,endtask,hours)])
            elif result.mode.lower() == 'level':
                tempdf = pd.DataFrame(columns=dateIndex(starttask,endtask),index=[resource.name], data=[calcHoursinMonthLevel(starttask,endtask,hours)])
            else:
                raise ValueError("mode not total or level")
            df = pd.concat([df,tempdf],axis=0).fillna(0)

    return df



    
        
        





    