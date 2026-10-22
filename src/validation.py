
import pandas as pd



def validate_schedule(
    schedule_df: pd.DataFrame,
    maintenance_df: pd.DataFrame,
    jobs_df: pd.DataFrame | None = None,
) -> dict:

    """Validate task timing, precedence, machine conflicts, and maintenance."""

    results = {
        "valid_schedule": True,
        "job_precedence": True,
        "machine_conflicts": True,
        "maintenance_conflicts": True,
        "task_completeness": True,
        "task_assignments": True,
    }

    # 1. Check whether the schedule is empty.
    if schedule_df.empty:
        results["valid_schedule"] = False
        print("Invalid schedule: schedule is empty.")

    else:
        # 2. Check start times, durations, and end times.
        for _, task in schedule_df.iterrows():
            if (
                task["start_time"] < 0
                or task["duration"] <= 0
                or task["end_time"] <= task["start_time"]
                or task["end_time"] - task["start_time"]
                != task["duration"]
            ):
                results["valid_schedule"] = False
                print(
                    f"Invalid timing: Job {task['job_id']}, "
                    f"Task {task['task_id']}"
                )
    
    # Check that every expected task appears exactly once.
    if jobs_df is not None:
        expected_tasks = set(
            zip(jobs_df["job_id"], jobs_df["task_id"])
        )
        actual_tasks = list(
            zip(schedule_df["job_id"], schedule_df["task_id"])
        )

        if (
            len(actual_tasks) != len(set(actual_tasks))
            or set(actual_tasks) != expected_tasks
        ):
            results["task_completeness"] = False
            print(
                "Task completeness violation: tasks are missing "
                "or duplicated."
            )
        
        
        # Check machine and duration only for uniquely identified tasks.
        # Duplicate task IDs are already handled by task_completeness.
        if not schedule_df.duplicated(
            subset=["job_id", "task_id"]
        ).any():
            expected = jobs_df.set_index(
                ["job_id", "task_id"]
            )[["machine_id", "processing_time"]]

            actual = schedule_df.set_index(
                ["job_id", "task_id"]
            )[["machine_id", "duration"]]

            common_tasks = expected.index.intersection(actual.index)

            for task_key in common_tasks:
                expected_machine = expected.loc[
                    task_key, "machine_id"
                ]
                expected_duration = expected.loc[
                    task_key, "processing_time"
                ]

                actual_machine = actual.loc[
                    task_key, "machine_id"
                ]
                actual_duration = actual.loc[
                    task_key, "duration"
                ]

                if (
                    expected_machine != actual_machine
                    or expected_duration != actual_duration
                ):
                    results["task_assignments"] = False
                    print(
                        f"Assignment mismatch for task {task_key}: "
                        "machine or duration differs from input."
                    )




    # 3. Check job precedence.
    for job_id, group in schedule_df.groupby("job_id"):
        group = group.sort_values("task_id")
        tasks = group.to_dict("records")

        for i in range(len(tasks) - 1):
            if tasks[i]["end_time"] > tasks[i + 1]["start_time"]:
                results["job_precedence"] = False
                print(f"Precedence violation in Job {job_id}")

    # 4. Check machine conflicts.
    for machine_id, group in schedule_df.groupby("machine_id"):
        tasks = group.sort_values("start_time").to_dict("records")

        for i in range(len(tasks) - 1):
            if tasks[i]["end_time"] > tasks[i + 1]["start_time"]:
                results["machine_conflicts"] = False
                print(f"Machine conflict on Machine {machine_id}")

    # 5. Check maintenance conflicts.
    for _, task in schedule_df.iterrows():
        for _, maintenance in maintenance_df.iterrows():
            if task["machine_id"] != maintenance["Machine"]:
                continue

            overlaps = (
                task["start_time"] < maintenance["mnt_end"]
                and task["end_time"] > maintenance["mnt_start"]
            )

            if overlaps:
                results["maintenance_conflicts"] = False
                print(
                    f"Maintenance conflict: Job {task['job_id']}, "
                    f"Task {task['task_id']}, "
                    f"Machine {task['machine_id']}"
                )

    # 6. Print final results.
    for check, passed in results.items():
        print(f"{check}: {'PASS' if passed else 'FAIL'}")

    if all(results.values()):
        print("All schedule validation checks passed!")
    else:
        print("Schedule validation failed.")

    return results
