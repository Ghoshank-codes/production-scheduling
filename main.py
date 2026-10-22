
import pandas as pd

from src.data_validation import (
    validate_jobs_data,
    validate_maintenance_data,
)
from src.scheduler import solve_schedule
from src.validation import validate_schedule
from src.metrics import calculate_metrics
from src.visualization import plot_gantt
from src.report import generate_report


def main():
    # 1. Load CSV files
    jobs_df = pd.read_csv("data/sample_data.csv")
    maintenance_df = pd.read_csv("data/sample_data2.csv")

    print("CSV files loaded successfully.")

    # 2. Validate input data
    jobs_df = validate_jobs_data(jobs_df)
    maintenance_df = validate_maintenance_data(
        maintenance_df, jobs_df
    )

    print("Input data validation passed.")

    # 3. Solve the scheduling problem
    scheduled_df, solver_stats = solve_schedule(
        jobs_df, maintenance_df
    )

    print("\nSolver statistics:")
    print(solver_stats)

    # 4. Stop if no feasible schedule exists
    if scheduled_df is None:
        print("No feasible schedule was found.")
        return

    print("\nGenerated schedule:")
    print(scheduled_df.to_string(index=False))

    # 5. Validate the generated schedule
    print("\nSchedule validation:")
    validation_results = validate_schedule(
    scheduled_df,
    maintenance_df,
    jobs_df,
)

    if not all(validation_results.values()):
        print("Schedule validation failed. Review the results.")
        return

    # 6. Calculate performance metrics
    overall_metrics, machine_metrics = calculate_metrics(
        scheduled_df, maintenance_df
    )

    print("\nOverall metrics:")
    for metric, value in overall_metrics.items():
        print(f"{metric}: {value}")

    print("\nMachine-wise metrics:")
    print(machine_metrics.to_string(index=False))

    # 7. Export results
    scheduled_df.to_csv("data/schedule_output.csv", index=False)
    machine_metrics.to_csv(
        "data/machine_metrics.csv", index=False
    )

    print("\nResults saved to the data folder.")

    report_path = generate_report(
    solver_stats,
    overall_metrics,
    machine_metrics,
    )

    print(f"Scheduling report saved to: {report_path}")

    # 8. Plot the Gantt chart
    plot_gantt(scheduled_df, maintenance_df)


if __name__ == "__main__":
    main()