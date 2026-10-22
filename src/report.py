
from pathlib import Path
import pandas as pd


def generate_report(
    solver_stats: dict,
    overall_metrics: dict,
    machine_metrics: pd.DataFrame,
    output_dir: str = "data",
) -> Path:
    """Generate a human-readable text report of scheduling results."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_path = output_path / "scheduling_report.txt"

    lines = [
        "PRODUCTION PLANNING AND SCHEDULING REPORT",
        "=" * 45,
        "",
        "SOLVER RESULTS",
        "-" * 45,
        f"Solver status: {solver_stats['status']}",
        f"Makespan: {overall_metrics['makespan']} time units",
        f"Solver runtime: {solver_stats['wall_time']:.4f} seconds",
        f"Conflicts: {solver_stats['conflicts']}",
        f"Branches: {solver_stats['branches']}",
        "",
        "OVERALL METRICS",
        "-" * 45,
        f"Total processing time: "
        f"{overall_metrics['total_processing_time']} time units",
        f"Total maintenance time: "
        f"{overall_metrics['total_maintenance_time']} machine-time units",
        f"Average machine utilization: "
        f"{overall_metrics['average_machine_utilization_percent']:.2f}%",
        "",
        "MACHINE-WISE METRICS",
        "-" * 45,
        machine_metrics.to_string(index=False),
        "",
        "GENERATED FILES",
        "-" * 45,
        "data/schedule_output.csv",
        "data/machine_metrics.csv",
        "data/schedule_gantt.png",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return report_path
