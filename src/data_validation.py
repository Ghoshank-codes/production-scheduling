
import pandas as pd


def validate_jobs_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate job and task input data."""

    required_columns = [
        "job_id",
        "task_id",
        "machine_id",
        "processing_time",
    ]

    # Check required columns
    if not set(required_columns).issubset(df.columns):
        raise ValueError("Jobs CSV is missing required columns.")

    # Keep only the columns needed by the scheduler
    df = df[required_columns].copy()

    # Check missing values
    if df.isnull().values.any():
        raise ValueError("Missing values found in jobs data.")

    # Check integer data types
    for column in required_columns:
        if not pd.api.types.is_integer_dtype(df[column]):
            raise ValueError(f"{column} must contain integers.")

    # Check duplicate operations
    if df.duplicated(subset=["job_id", "task_id"]).any():
        raise ValueError("Duplicate job-task pairs found.")

    # Check positive processing times
    if df["processing_time"].le(0).any():
        raise ValueError("Processing times must be positive.")

    # Check non-negative IDs
    for column in ["job_id", "task_id", "machine_id"]:
        if df[column].lt(0).any():
            raise ValueError(f"{column} cannot contain negative values.")

    # Check consecutive task IDs starting from zero
    for job_id, group in df.groupby("job_id"):
        task_ids = sorted(group["task_id"].tolist())
        expected_ids = list(range(len(task_ids)))

        if task_ids != expected_ids:
            raise ValueError(
                f"Job {job_id} has missing or invalid task IDs: {task_ids}"
            )

    return df.sort_values(["job_id", "task_id"]).reset_index(drop=True)


def validate_maintenance_data(
    maintenance_df: pd.DataFrame,
    jobs_df: pd.DataFrame,
) -> pd.DataFrame:
    """Validate machine maintenance intervals."""

    required_columns = ["Machine", "mnt_start", "mnt_end"]

    # Check required columns
    if not set(required_columns).issubset(maintenance_df.columns):
        raise ValueError("Maintenance CSV is missing required columns.")

    maintenance_df = maintenance_df[required_columns].copy()

    # Check missing values
    if maintenance_df.isnull().values.any():
        raise ValueError("Missing values found in maintenance data.")

    # Check integer data types
    for column in required_columns:
        if not pd.api.types.is_integer_dtype(maintenance_df[column]):
            raise ValueError(f"{column} must contain integers.")

    # Check non-negative machine IDs and start times
    if maintenance_df["Machine"].lt(0).any():
        raise ValueError("Maintenance machine IDs cannot be negative.")

    if maintenance_df["mnt_start"].lt(0).any():
        raise ValueError("Maintenance start times cannot be negative.")

    # Check valid intervals
    if maintenance_df["mnt_end"].lt(
        maintenance_df["mnt_start"]
    ).any():
        raise ValueError(
            "Maintenance end time cannot precede start time."
        )

    # Check that maintenance refers to known machines
    known_machines = set(jobs_df["machine_id"])

    if not set(maintenance_df["Machine"]).issubset(known_machines):
        raise ValueError("Maintenance references an unknown machine.")

    return maintenance_df.reset_index(drop=True)
