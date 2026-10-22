
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


def plot_gantt(
    schedule_df: pd.DataFrame,
    maintenance_df: pd.DataFrame,
) -> None:
    """Plot the production schedule and machine maintenance periods."""

    if schedule_df.empty:
        raise ValueError("Cannot plot an empty schedule.")

    machines = sorted(schedule_df["machine_id"].unique())
    machine_positions = {
        machine_id: position
        for position, machine_id in enumerate(machines)
    }

    makespan = int(schedule_df["end_time"].max())

    fig, ax = plt.subplots(
        figsize=(14, max(4, len(machines) * 1.3))
    )

    # Draw production tasks.
    for _, task in schedule_df.iterrows():
        machine_id = task["machine_id"]
        start = task["start_time"]
        duration = task["duration"]
        job_id = task["job_id"]
        task_id = task["task_id"]
        position = machine_positions[machine_id]

        ax.barh(
            position,
            duration,
            left=start,
            height=0.5,
            edgecolor="black",
        )

        ax.text(
            start + duration / 2,
            position,
            f"J{job_id}-T{task_id}",
            ha="center",
            va="center",
            fontsize=8,
        )

        # Show duration above each task when there is enough space.
        if duration >= 3:
            ax.text(
                start + duration / 2,
                position + 0.32,
                f"{duration} units",
                ha="center",
                va="bottom",
                fontsize=7,
            )

    # Draw maintenance periods.
    for _, maintenance in maintenance_df.iterrows():
        machine_id = maintenance["Machine"]

        if machine_id not in machine_positions:
            continue

        start = maintenance["mnt_start"]
        duration = maintenance["mnt_end"] - start

        if duration <= 0:
            continue

        position = machine_positions[machine_id]

        ax.barh(
            position,
            duration,
            left=start,
            height=0.5,
            color="gray",
            alpha=0.6,
            edgecolor="black",
            hatch="//",
        )

        if duration >= 3:
            ax.text(
                start + duration / 2,
                position,
                "Maintenance",
                ha="center",
                va="center",
                fontsize=7,
            )

    # Add a legend explaining the chart elements.
    legend_items = [
        Patch(
            facecolor="C0",
            edgecolor="black",
            label="Production task",
        ),
        Patch(
            facecolor="gray",
            edgecolor="black",
            hatch="//",
            alpha=0.6,
            label="Maintenance",
        ),
    ]

    ax.legend(handles=legend_items, loc="upper right")

    ax.set_yticks(range(len(machines)))
    ax.set_yticklabels([f"Machine {m}" for m in machines])
    ax.set_xlabel("Time units")
    ax.set_ylabel("Machine")
    ax.set_title(f"Production Schedule (Makespan: {makespan})")
    ax.set_xlim(left=0)
    ax.set_xticks(range(0, makespan + 2))
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()
    fig.savefig(
    "data/schedule_gantt.png",
    dpi=300,
    bbox_inches="tight",
)