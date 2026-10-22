
import collections
import pandas as pd
from ortools.sat.python import cp_model


def solve_schedule(
    jobs_df: pd.DataFrame,
    maintenance_df: pd.DataFrame,
):
    """Optimize the job-shop schedule and return the result."""

    # Convert job rows into the format required by the scheduler.
    jobs_data = [
        list(zip(group["machine_id"], group["processing_time"]))
        for _, group in jobs_df.groupby("job_id", sort=True)
    ]

    # Identify machines and calculate the planning horizon.
    machines = sorted(jobs_df["machine_id"].unique())

    total_processing_time = sum(
    duration
    for job in jobs_data
    for _, duration in job
    )

    total_maintenance_time = int(
        (maintenance_df["mnt_end"] - maintenance_df["mnt_start"]).sum()
    )

    latest_maintenance_end = (
        int(maintenance_df["mnt_end"].max())
        if not maintenance_df.empty
        else 0
    )

    horizon = max(
        1,
        total_processing_time + total_maintenance_time,
        latest_maintenance_end + total_processing_time,
    )

    # Create the optimization model.
    model = cp_model.CpModel()

    task_type = collections.namedtuple(
        "Task", "start end interval"
    )

    all_tasks = {}
    machine_to_intervals = collections.defaultdict(list)

    # Add fixed maintenance intervals to the model.
    for _, row in maintenance_df.iterrows():
        machine = int(row["Machine"])
        start = int(row["mnt_start"])
        end = int(row["mnt_end"])

        if end == start:
            continue

        interval = model.new_fixed_size_interval_var(
            start,
            end - start,
            f"maintenance_M{machine}_{start}_{end}",
        )

        machine_to_intervals[machine].append(interval)

    # Create task variables and intervals.
    for job_id, job in enumerate(jobs_data):
        for task_id, (machine, duration) in enumerate(job):
            start_var = model.new_int_var(
                0, horizon, f"start_{job_id}_{task_id}"
            )
            end_var = model.new_int_var(
                0, horizon, f"end_{job_id}_{task_id}"
            )

            interval_var = model.new_interval_var(
                start_var,
                duration,
                end_var,
                f"task_{job_id}_{task_id}",
            )

            all_tasks[job_id, task_id] = task_type(
                start_var, end_var, interval_var
            )

            machine_to_intervals[int(machine)].append(interval_var)

    # Each machine can process only one operation at a time.
    for machine in machines:
        model.add_no_overlap(machine_to_intervals[machine])

    # Operations within a job must follow their specified order.
    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job) - 1):
            model.add(
                all_tasks[job_id, task_id + 1].start
                >= all_tasks[job_id, task_id].end
            )

    # Minimize the makespan (total time until all jobs finish).
    makespan_var = model.new_int_var(
        0, horizon, "makespan"
    )

    model.add_max_equality(
        makespan_var,
        [
            all_tasks[job_id, len(job) - 1].end
            for job_id, job in enumerate(jobs_data)
        ],
    )

    model.minimize(makespan_var)

    # Solve the model.
    solver = cp_model.CpSolver()
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, {
            "status": solver.status_name(status),
            "wall_time": solver.wall_time,
            "conflicts": solver.num_conflicts,
            "branches": solver.num_branches,
        }

    # Extract the solution into a DataFrame.
    schedule = []

    for job_id, job in enumerate(jobs_data):
        for task_id, (machine, duration) in enumerate(job):
            start = solver.value(
                all_tasks[job_id, task_id].start
            )
            end = solver.value(
                all_tasks[job_id, task_id].end
            )

            schedule.append({
                "job_id": sorted(jobs_df["job_id"].unique())[job_id],
                "task_id": task_id,
                "machine_id": int(machine),
                "start_time": start,
                "end_time": end,
                "duration": duration,
            })

    schedule_df = pd.DataFrame(schedule)

    # Return solver statistics as well.
    stats = {
        "status": solver.status_name(status),
        "makespan": solver.value(makespan_var),
        "wall_time": solver.wall_time,
        "conflicts": solver.num_conflicts,
        "branches": solver.num_branches,
    }

    return schedule_df, stats
