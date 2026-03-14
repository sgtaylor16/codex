from tables.tables import Resources,Assignments, Tasks, ProjectData
from sqlalchemy import select
from typing import List
from orm import Session
from graphlib import TopologicalSorter, CycleError
from datetime import timedelta
import json


def add_business_days(start_date, business_days: int):
    current_date = start_date
    days_added = 0
    while days_added < business_days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:
            days_added += 1
    return current_date

def getTasks(session) -> List[Tasks]:
    """Returns a list of all tasks in the database"""
    stmt = select(Tasks)
    tasks = session.execute(stmt).scalars().all()
    return tasks

def taskDict(tasks:List[Tasks]) -> dict:
    """Returns a dictionary of tasks with task id as key and task predessor ids as values"""
    if len(tasks) == 0:
        return []
    return {task.id: {pred.id for pred in task.predecessors} for task in tasks}

def order_tasks() -> None:
    """Return tasks in valid predecessor order with simple start/finish offsets.

    The returned records include:
    - order: topological order number (1-based)
    - start_day: earliest day offset where task can start
    - finish_day: earliest day offset where task can finish
    """
    with Session() as session:
        tasks = getTasks(session)
        predecessor_ids = taskDict(tasks)

        task_by_id = {task.id: task for task in tasks}

        task_ids = set(task_by_id)
        for task_id, preds in predecessor_ids.items():
            for pred_id in preds:
                if pred_id not in task_ids:
                    raise ValueError(f"Predecessor task id {pred_id} not found for task {task_id}")

        sorter = TopologicalSorter(predecessor_ids)
        try:
            topological_order = list(sorter.static_order())
        except CycleError as exc:
            raise ValueError("Cycle detected in predecessor relationships. Scheduling requires a DAG.") from exc

        project_start = session.execute(
            select(ProjectData.projstart).limit(1)
        ).scalar_one_or_none()

        if project_start is None:
            raise ValueError("Project start date is not set in ProjectData.")


        for task_id in topological_order:
            onetask = task_by_id[task_id]
            duration = float(onetask.duration)
            if not predecessor_ids[task_id]:  # No predecessors
                start_day = 0.0
                onetask.earlystart = project_start
                onetask.earlyfinish = add_business_days(project_start, int(duration))
            else:
                earlieststart = None
                for onepred in onetask.predecessors:
                    if earlieststart is None:
                        earlieststart = onepred.earlyfinish
                    elif onepred.earlyfinish > earlieststart:
                        earlieststart = onepred.earlyfinish
                onetask.earlystart = earlieststart
                onetask.earlyfinish = add_business_days(earlieststart, int(duration))
                print(onetask.earlystart)
        
        session.commit()
    return None

        
def tasktojson(filename: str = 'tasks.json') -> None:
    with Session() as session:
        stmt = select(Tasks)
        tasks = session.execute(stmt).scalars().all()
        tasklist = []
        for task in tasks:
            taskdict = {
                'id': task.id,
                'name': task.name,
                'duration': task.duration,
                'earlystart': task.earlystart.isoformat() if task.earlystart else None,
                'earlyfinish': task.earlyfinish.isoformat() if task.earlyfinish else None,
                'predecessors': [pred.id for pred in task.predecessors]
            }
            tasklist.append(taskdict)
    with open(filename, 'w') as f:
        json.dump(tasklist, f, indent=4)

    return None