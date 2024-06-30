from tables.tables import Resources,Assignments, Tasks
from orm import Session
from datetime import date
import numpy as np
import pandas as pd
from typing import List
from checks import get_ResourceNumber, get_TaskNumber

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
    
def calcHoursinMonth(startdate:date,enddate:date,hours:float) -> List[int]:

    def addzero(x:str) -> str:
        if len(x) == 1:
            return '0' + str(x)
        else:
            return x

    # Create a sample date range
    date_frame = pd.date_range(startdate,enddate, freq='B').to_frame()
    date_frame['AP'] = date_frame[0].apply(lambda x: str(x.year) + addzero(str(x.month)))
    return date_frame['AP'].value_counts().sort_index().to_list()

def addAssignment(taskname,resourcename,hours):
    tasknumber = get_TaskNumber(taskname)
    resourcenumber = get_ResourceNumber(resourcename)
    with Session() as session:
        Assn1 = Assignments(resource = resourcenumber, tasks=tasknumber, hours = hours)

        session.add_all([Assn1])
        session.commit()
        
        





    