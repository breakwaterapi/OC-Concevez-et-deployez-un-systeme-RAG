"""Build the Faiss index without starting the API server.

Reuses the exact same use cases as `POST /rebuild` (see `api.bootstrap`), so the result is
identical to calling the endpoint. Usage: `make build-index` or
`uv run python scripts/build_index.py`.
"""

from loguru import logger

from api.bootstrap import bootstrap, get_data_use_cases
from api.common.logging import configure_logging


def main() -> None:
    configure_logging()
    bootstrap()

    use_cases = get_data_use_cases()
    events = use_cases.prepare.execute()
    n_chunks, n_parents = use_cases.build_index.execute(events)

    logger.success(f"Index built: {n_chunks} chunks from {n_parents} events.")


if __name__ == "__main__":
    main()
