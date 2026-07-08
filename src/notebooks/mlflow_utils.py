from typing import Any

from loguru import logger
import mlflow


def setup_experiment(
    experiment_name: str = "rag-cultural-events",
    tracking_uri: str = "sqlite:///mlruns.db",
) -> None:
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    logger.info(f"MLflow experiment: {experiment_name} (uri: {tracking_uri})")


def log_run(
    run_name: str,
    params: dict[str, Any] | None = None,
    metrics: dict[str, float] | None = None,
    artifacts: list[str] | None = None,
) -> str:
    with mlflow.start_run(run_name=run_name) as run:
        if params:
            mlflow.log_params(params)
        if metrics:
            mlflow.log_metrics(metrics)
        for path in artifacts or []:
            mlflow.log_artifact(path)
        logger.info(f"MLflow run '{run_name}' logged (id: {run.info.run_id})")
        return run.info.run_id
