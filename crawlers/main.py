from workflows.ufc_stats_flow import run_ufc_stats_flow
from prefect.schedules import Cron


if __name__ == "__main__":
    run_ufc_stats_flow.serve(
        name="ufc_stats_flow",
        schedules=[
            Cron(
                "0 0 * * 3"
            )
        ]
    )