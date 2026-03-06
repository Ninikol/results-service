from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "ResultsService")
    app_env: str = os.getenv("APP_ENV", "dev")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://results_user:results_pass@localhost:5432/results_db",
    )


settings = Settings()
