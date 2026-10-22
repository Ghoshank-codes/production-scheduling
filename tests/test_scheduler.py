
import pandas as pd
import pytest
from src.data_validation import validate_jobs_data
from src.scheduler import solve_schedule
from src.validation import validate_schedule


def test_scheduler_returns_feasible_schedule():
    jobs_df = pd.DataFrame({
        "job_id": [0, 0, 1, 1],
        "task_id": [0, 1, 0, 1],
        "machine_id": [0, 1, 1, 0],
        "processing_time": [3, 2, 2, 1],
    })

    maintenance_df = pd.DataFrame({
        "Machine": [0],
        "mnt_start": [4],
        "mnt_end": [5],
    })

    schedule_df, stats = solve_schedule(
        jobs_df, maintenance_df
    )

    assert schedule_df is not None
    assert stats["status"] in ("OPTIMAL", "FEASIBLE")

    results = validate_schedule(
        schedule_df, maintenance_df
    )

    assert all(results.values())


def test_scheduler_respects_job_precedence():
    jobs_df = pd.DataFrame({
        "job_id": [0, 0],
        "task_id": [0, 1],
        "machine_id": [0, 1],
        "processing_time": [3, 2],
    })

    maintenance_df = pd.DataFrame(
        columns=["Machine", "mnt_start", "mnt_end"]
    )

    schedule_df, stats = solve_schedule(
        jobs_df, maintenance_df
    )

    assert schedule_df is not None

    schedule_df = schedule_df.sort_values("task_id")
    tasks = schedule_df.to_dict("records")

    assert tasks[0]["end_time"] <= tasks[1]["start_time"]


def test_jobs_data_rejects_missing_values():
    jobs_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "processing_time": [None],
    })

    with pytest.raises(ValueError, match="Missing values"):
        validate_jobs_data(jobs_df)


def test_jobs_data_rejects_negative_processing_time():
    jobs_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "processing_time": [-3],
    })

    with pytest.raises(ValueError, match="positive"):
        validate_jobs_data(jobs_df)


def test_scheduler_avoids_maintenance():
    jobs_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "processing_time": [3],
    })

    maintenance_df = pd.DataFrame({
        "Machine": [0],
        "mnt_start": [0],
        "mnt_end": [5],
    })

    schedule_df, stats = solve_schedule(
        jobs_df, maintenance_df
    )

    assert schedule_df is not None

    task = schedule_df.iloc[0]

    # The task must start after maintenance ends.
    assert task["start_time"] >= 5


def test_tasks_do_not_overlap_on_same_machine():
    jobs_df = pd.DataFrame({
        "job_id": [0, 1],
        "task_id": [0, 0],
        "machine_id": [0, 0],
        "processing_time": [3, 2],
    })

    maintenance_df = pd.DataFrame(
        columns=["Machine", "mnt_start", "mnt_end"]
    )

    schedule_df, stats = solve_schedule(
        jobs_df, maintenance_df
    )

    assert schedule_df is not None

    tasks = schedule_df.sort_values("start_time").to_dict("records")

    for i in range(len(tasks) - 1):
        assert tasks[i]["end_time"] <= tasks[i + 1]["start_time"]



def test_scheduler_handles_late_maintenance():
    jobs_df = pd.DataFrame({
        "job_id": [0, 0],
        "task_id": [0, 1],
        "machine_id": [1, 0],
        "processing_time": [102, 3],
    })

    maintenance_df = pd.DataFrame({
        "Machine": [0],
        "mnt_start": [100],
        "mnt_end": [105],
    })

    schedule_df, stats = solve_schedule(
        jobs_df, maintenance_df
    )

    assert schedule_df is not None

    # The first task runs on machine 1 from time 0 to 102.
    first_task = schedule_df[
        schedule_df["task_id"] == 0
    ].iloc[0]

    # The second task must wait for maintenance to finish.
    second_task = schedule_df[
        schedule_df["task_id"] == 1
    ].iloc[0]

    assert first_task["end_time"] == 102
    assert second_task["start_time"] >= 105


def test_metrics_do_not_double_count_overlapping_maintenance():
    from src.metrics import calculate_metrics

    schedule_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "start_time": [0],
        "end_time": [30],
        "duration": [30],
    })

    maintenance_df = pd.DataFrame({
        "Machine": [0, 0],
        "mnt_start": [10, 15],
        "mnt_end": [20, 25],
    })

    overall_metrics, machine_metrics_df = calculate_metrics(
        schedule_df, maintenance_df
    )

    assert machine_metrics_df.iloc[0]["maintenance_time"] == 15
    assert machine_metrics_df.iloc[0]["available_time"] == 15
    assert machine_metrics_df.iloc[0]["utilization_percent"] == 200.0



def test_validation_detects_missing_task():
    from src.validation import validate_schedule

    jobs_df = pd.DataFrame({
        "job_id": [0, 0],
        "task_id": [0, 1],
        "machine_id": [0, 1],
        "processing_time": [3, 4],
    })

    # Only task 0 is present; task 1 is missing.
    schedule_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "start_time": [0],
        "end_time": [3],
        "duration": [3],
    })

    maintenance_df = pd.DataFrame(
        columns=["Machine", "mnt_start", "mnt_end"]
    )

    results = validate_schedule(
        schedule_df, maintenance_df, jobs_df
    )

    assert results["task_completeness"] is False


def test_validation_detects_duplicate_task():
    from src.validation import validate_schedule

    jobs_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "processing_time": [3],
    })

    # Task 0 appears twice.
    schedule_df = pd.DataFrame({
        "job_id": [0, 0],
        "task_id": [0, 0],
        "machine_id": [0, 0],
        "start_time": [0, 3],
        "end_time": [3, 6],
        "duration": [3, 3],
    })

    maintenance_df = pd.DataFrame(
        columns=["Machine", "mnt_start", "mnt_end"]
    )

    results = validate_schedule(
        schedule_df, maintenance_df, jobs_df
    )

    assert results["task_completeness"] is False


def test_validation_detects_wrong_machine_assignment():
    from src.validation import validate_schedule

    jobs_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "processing_time": [3],
    })

    schedule_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [1],  # Incorrect machine
        "start_time": [0],
        "end_time": [3],
        "duration": [3],
    })

    maintenance_df = pd.DataFrame(
        columns=["Machine", "mnt_start", "mnt_end"]
    )

    results = validate_schedule(
        schedule_df, maintenance_df, jobs_df
    )

    assert results["task_assignments"] is False


def test_validation_detects_wrong_processing_time():
    from src.validation import validate_schedule

    jobs_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "processing_time": [3],
    })

    schedule_df = pd.DataFrame({
        "job_id": [0],
        "task_id": [0],
        "machine_id": [0],
        "start_time": [0],
        "end_time": [4],
        "duration": [4],  # Incorrect duration
    })

    maintenance_df = pd.DataFrame(
        columns=["Machine", "mnt_start", "mnt_end"]
    )

    results = validate_schedule(
        schedule_df, maintenance_df, jobs_df
    )

    assert results["task_assignments"] is False
