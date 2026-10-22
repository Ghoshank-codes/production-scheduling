
import pandas as pd


def calculate_metrics(
    schedule_df: pd.DataFrame,
    maintenance_df: pd.DataFrame,
) -> tuple[dict, pd.DataFrame]:
    """
    Calculate overall scheduling metrics and machine-wise utilization.
    """

    if schedule_df.empty:
        raise ValueError("Cannot calculate metrics for an empty schedule.")

    # Overall schedule completion time
    makespan = int(schedule_df["end_time"].max())

    
    # Calculate maintenance duration within the schedule horizon.
    maintenance_time_by_machine = {}

    for machine_id in schedule_df["machine_id"].unique():
        machine_maintenance = maintenance_df[
            maintenance_df["Machine"] == machine_id
        ]

        # Clip maintenance intervals to the schedule horizon.
        intervals = []

        for _, row in machine_maintenance.iterrows():
            start = max(0, int(row["mnt_start"]))
            end = min(makespan, int(row["mnt_end"]))

            if end > start:
                intervals.append((start, end))

        # Merge overlapping intervals to avoid double-counting.
        intervals.sort()
        merged_intervals = []

        for start, end in intervals:
            if merged_intervals and start <= merged_intervals[-1][1]:
                previous_start, previous_end = merged_intervals[-1]
                merged_intervals[-1] = (
                    previous_start,
                    max(previous_end, end),
                )
            else:
                merged_intervals.append((start, end))

        maintenance_time_by_machine[machine_id] = sum(
            end - start for start, end in merged_intervals
        )

    # Calculate machine-wise metrics
    machine_metrics = []

    for machine_id, group in schedule_df.groupby("machine_id"):
        processing_time = int(group["duration"].sum())
        maintenance_time = maintenance_time_by_machine.get(
            machine_id, 0
        )

        available_time = max(0, makespan - maintenance_time)

        utilization = (
            processing_time / available_time * 100
            if available_time > 0
            else 0
        )

        machine_metrics.append({
            "machine_id": machine_id,
            "processing_time": processing_time,
            "maintenance_time": maintenance_time,
            "available_time": available_time,
            "utilization_percent": round(utilization, 2),
        })

    machine_metrics_df = pd.DataFrame(machine_metrics)

    # Overall metrics
    overall_metrics = {
        "makespan": makespan,
        "total_processing_time": int(schedule_df["duration"].sum()),
        "total_maintenance_time": int(
            machine_metrics_df["maintenance_time"].sum()
        ),
        "average_machine_utilization_percent": round(
            machine_metrics_df["utilization_percent"].mean(), 2
        ),
    }

    return overall_metrics, machine_metrics_df
