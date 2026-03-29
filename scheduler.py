from tables.tables import Resources,Assignments, Tasks, ProjectData
from sqlalchemy import select
from typing import List
from orm import Session
from graphlib import TopologicalSorter, CycleError
from datetime import timedelta
import json
import plotly.graph_objects as go


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
    """Writes tasks to a json file with the following format:
[
    {
        "id": 1,
        "name": "Task 1",
        "duration": 5,
        "earlystart": "2023-01-01",
        "earlyfinish": "2023-01-06",
        "predecessors": [2, 3]
    },
    ...
]
"""
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


def plot_network(output_html: str = None, show: bool = True):
    """Plot a task dependency network where edges point predecessor -> successor.

    Args:
        output_html: Optional output file path to save an interactive HTML diagram.
        show: If True, opens the interactive plot window.

    Returns:
        A Plotly Figure object for further customization.
    """
    with Session() as session:
        tasks = getTasks(session)

        if not tasks:
            raise ValueError("No tasks found. Load tasks before plotting the dependency network.")

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
            raise ValueError(
                "Cycle detected in predecessor relationships. Diagram requires a DAG."
            ) from exc

        successor_ids = {task_id: set() for task_id in predecessor_ids}
        for task_id, preds in predecessor_ids.items():
            for pred_id in preds:
                successor_ids[pred_id].add(task_id)

        durations = {task.id: float(task.duration) for task in tasks}

        # Forward pass: earliest start/finish in day offsets.
        earliest_start = {}
        earliest_finish = {}
        for task_id in topological_order:
            preds = predecessor_ids[task_id]
            start = 0.0 if not preds else max(earliest_finish[pred] for pred in preds)
            earliest_start[task_id] = start
            earliest_finish[task_id] = start + durations[task_id]

        project_duration = max(earliest_finish.values())

        # Backward pass: latest start/finish in day offsets.
        latest_finish = {}
        latest_start = {}
        for task_id in reversed(topological_order):
            succs = successor_ids[task_id]
            finish = project_duration if not succs else min(latest_start[succ] for succ in succs)
            latest_finish[task_id] = finish
            latest_start[task_id] = finish - durations[task_id]

        tolerance = 1e-9
        critical_nodes = {
            task_id
            for task_id in topological_order
            if abs(latest_start[task_id] - earliest_start[task_id]) <= tolerance
        }
        critical_edges = set()
        for task_id, preds in predecessor_ids.items():
            for pred_id in preds:
                if pred_id in critical_nodes and task_id in critical_nodes:
                    if abs(earliest_finish[pred_id] - earliest_start[task_id]) <= tolerance:
                        critical_edges.add((pred_id, task_id))

        # Compute horizontal layer by longest predecessor chain.
        levels = {}
        for task_id in topological_order:
            preds = predecessor_ids[task_id]
            levels[task_id] = 0 if not preds else max(levels[pred] + 1 for pred in preds)

        level_groups = {}
        for task_id, level in levels.items():
            level_groups.setdefault(level, []).append(task_id)

        positions = {}
        for level, ids in level_groups.items():
            ids.sort()
            count = len(ids)
            for index, task_id in enumerate(ids):
                # Spread nodes in each column around y=0 for readability.
                y = (count - 1) / 2 - index
                positions[task_id] = (level, y)

        normal_edge_x = []
        normal_edge_y = []
        critical_edge_x = []
        critical_edge_y = []
        annotations = []
        node_radius = 0.12

        for task_id, preds in predecessor_ids.items():
            x1_raw, y1_raw = positions[task_id]
            for pred_id in preds:
                x0_raw, y0_raw = positions[pred_id]
                dx = x1_raw - x0_raw
                dy = y1_raw - y0_raw
                length = (dx * dx + dy * dy) ** 0.5
                if length == 0:
                    continue

                ux = dx / length
                uy = dy / length
                x0 = x0_raw + ux * node_radius
                y0 = y0_raw + uy * node_radius
                x1 = x1_raw - ux * node_radius
                y1 = y1_raw - uy * node_radius

                if (pred_id, task_id) in critical_edges:
                    critical_edge_x.extend([x0, x1, None])
                    critical_edge_y.extend([y0, y1, None])
                    arrow_color = "#d62728"
                else:
                    normal_edge_x.extend([x0, x1, None])
                    normal_edge_y.extend([y0, y1, None])
                    arrow_color = "#7A7A7A"

                annotations.append(
                    dict(
                        x=x1,
                        y=y1,
                        ax=x0,
                        ay=y0,
                        xref="x",
                        yref="y",
                        axref="x",
                        ayref="y",
                        showarrow=True,
                        arrowhead=3,
                        arrowsize=1,
                        arrowwidth=1.5,
                        arrowcolor=arrow_color,
                    )
                )

        edge_trace = go.Scatter(
            x=normal_edge_x,
            y=normal_edge_y,
            mode="lines",
            line=dict(width=1.5, color="#7A7A7A"),
            hoverinfo="none",
            showlegend=False,
        )

        critical_edge_trace = go.Scatter(
            x=critical_edge_x,
            y=critical_edge_y,
            mode="lines",
            line=dict(width=3.0, color="#d62728"),
            hoverinfo="none",
            showlegend=False,
        )

        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        for task_id in topological_order:
            task = task_by_id[task_id]
            x, y = positions[task_id]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{task.id}: {task.name}")
            slack = latest_start[task_id] - earliest_start[task_id]
            critical_text = "Yes" if task_id in critical_nodes else "No"
            node_hover.append(
                f"Task {task.id}<br>Name: {task.name}<br>Duration: {task.duration}<br>"
                f"Predecessors: {sorted(predecessor_ids[task_id])}<br>"
                f"Slack: {slack:.2f} days<br>Critical: {critical_text}"
            )

        node_colors = ["#d62728" if task_id in critical_nodes else "#1f77b4" for task_id in topological_order]

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            marker=dict(size=20, color=node_colors, line=dict(width=1, color="#FFFFFF")),
            hovertext=node_hover,
            hoverinfo="text",
            showlegend=False,
        )

        fig = go.Figure(data=[edge_trace, critical_edge_trace, node_trace])
        fig.update_layout(
            title="Task Dependency Network (Critical Path Highlighted)",
            xaxis=dict(title="Dependency Level", showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
            margin=dict(l=40, r=40, t=60, b=40),
            annotations=annotations,
        )

        if output_html:
            fig.write_html(output_html)
        if show:
            fig.show()

        return fig

