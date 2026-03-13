from tables.tables import Resources,Assignments, Tasks
from sqlalchemy import select
from typing import List
from orm import Session

def getTasks(session) -> List[Tasks]:
    """Returns a list of all tasks in the database"""
    stmt = select(Tasks)
    tasks = session.execute(stmt).scalars().all()
    return tasks

def taskDict(tasks:List[Tasks]) -> dict:
    """Returns a dictionary of tasks with task id as key and task predessor ids as values"""
    return {task.id: {pred.id for pred in task.predecessors} for task in tasks}

def schedule_tasks_in_order() -> List[dict]:
    """Return tasks in valid predecessor order with simple start/finish offsets.

    The returned records include:
    - order: topological order number (1-based)
    - start_day: earliest day offset where task can start
    - finish_day: earliest day offset where task can finish
    """
    with Session() as session:
        tasks = session.execute(select(Tasks)).scalars().all()

        if len(tasks) == 0:
            return []

        task_by_id = {task.id: task for task in tasks}
        predecessor_ids = {task.id: {pred.id for pred in task.predecessors} for task in tasks}
        successor_ids = {task.id: set() for task in tasks}

        for task_id, preds in predecessor_ids.items():
            for pred_id in preds:
                if pred_id not in successor_ids:
                    raise ValueError(f"Predecessor task id {pred_id} not found for task {task_id}")
                successor_ids[pred_id].add(task_id)

        indegree = {task_id: len(preds) for task_id, preds in predecessor_ids.items()}
        ready = sorted([task_id for task_id, degree in indegree.items() if degree == 0])

        topological_order: List[int] = []
        while ready:
            current_id = ready.pop(0)
            topological_order.append(current_id)
            for succ_id in sorted(successor_ids[current_id]):
                indegree[succ_id] -= 1
                if indegree[succ_id] == 0:
                    ready.append(succ_id)
            ready.sort()

        if len(topological_order) != len(tasks):
            raise ValueError("Cycle detected in predecessor relationships. Scheduling requires a DAG.")

        earliest_start = {}
        earliest_finish = {}
        for task_id in topological_order:
            pred_finish_days = [earliest_finish[pred_id] for pred_id in predecessor_ids[task_id]]
            start_day = max(pred_finish_days) if pred_finish_days else 0.0
            duration = float(task_by_id[task_id].duration)
            finish_day = start_day + duration
            earliest_start[task_id] = start_day
            earliest_finish[task_id] = finish_day

        ordered_schedule = []
        for order, task_id in enumerate(topological_order, start=1):
            task = task_by_id[task_id]
            ordered_schedule.append(
                {
                    'order': order,
                    'id': task.id,
                    'name': task.name,
                    'duration': float(task.duration),
                    'predecessors': sorted(list(predecessor_ids[task_id])),
                    'start_day': earliest_start[task_id],
                    'finish_day': earliest_finish[task_id],
                }
            )

    return ordered_schedule

def schedule() -> List[dict]:
    """Backward-compatible wrapper for task scheduling."""
    return schedule_tasks_in_order()
        
def tasktojson() -> List[dict]:
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
    return tasklist