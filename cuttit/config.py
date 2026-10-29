"""Settings, read from environment variables (see .env.example)."""

import os
from dataclasses import dataclass, field


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    anthropic_model: str = field(default_factory=lambda: _env("CUTTIT_CLAUDE_MODEL", "claude-opus-5-5"))
    gemini_api_key: str | None = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: _env("CUTTIT_GEMINI_MODEL", "gemini-2.5-flash"))

    database_url: str | None = field(default_factory=lambda: _env("DATABASE_URL"))

    r2_account_id: str | None = field(default_factory=lambda: _env("R2_ACCOUNT_ID"))
    r2_access_key: str | None = field(default_factory=lambda: _env("R2_ACCESS_KEY_ID"))
    r2_secret_key: str | None = field(default_factory=lambda: _env("R2_SECRET_ACCESS_KEY"))
    r2_bucket: str = field(default_factory=lambda: _env("R2_BUCKET", "cuttit"))

    # Font used for burned-in captions. Must cover Malayalam (e.g. Noto Sans Malayalam).
    caption_font: str = field(default_factory=lambda: _env("CUTTIT_CAPTION_FONT", "Noto Sans Malayalam"))
    fonts_dir: str | None = field(default_factory=lambda: _env("CUTTIT_FONTS_DIR"))

    work_dir: str = field(default_factory=lambda: _env("CUTTIT_WORK_DIR", "/tmp/cuttit"))
    max_job_attempts: int = field(default_factory=lambda: int(_env("CUTTIT_MAX_ATTEMPTS", "3")))


settings = Settings()
