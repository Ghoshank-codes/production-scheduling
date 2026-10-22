
from pathlib import Path

import pandas as pd

from src.report import generate_report


def test_generate_report(tmp_path):
    solver_stats = {
        "status": "OPTIMAL",
        "wall_time": 0.05,
        "conflicts": 0,
        "branches": 5,
    }

    overall_metrics = {
        "makespan": 12,
        "total_processing_time": 21,
        "total_maintenance_time": 2,
        "average_machine_utilization_percent": 62.38,
    }

    machine_metrics = pd.DataFrame({
        "machine_id": [0, 1],
        "processing_time": [5, 10],
        "maintenance_time": [0, 1],
        "available_time": [12, 11],
        "utilization_percent": [41.67, 90.91],
    })

    report_path = generate_report(
        solver_stats,
        overall_metrics,
        machine_metrics,
        output_dir=str(tmp_path),
    )

    assert report_path.exists()

    report = report_path.read_text(encoding="utf-8")

    assert "OPTIMAL" in report
    assert "Makespan: 12 time units" in report
    assert "Total processing time: 21 time units" in report
    assert "62.38%" in report
    assert "MACHINE-WISE METRICS" in report
