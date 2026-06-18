from dataclasses import dataclass
import os


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class AppConfig:
    project_id: str | None
    document_ai_location: str
    document_ai_processor_id: str | None
    vertex_ai_location: str
    gemini_model: str
    max_upload_mb: int
    max_pages: int
    max_questions: int
    max_source_chars: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT"),
            document_ai_location=os.getenv("DOCUMENT_AI_LOCATION", "us"),
            document_ai_processor_id=os.getenv("DOCUMENT_AI_PROCESSOR_ID"),
            vertex_ai_location=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            max_upload_mb=_env_int("MAX_UPLOAD_MB", 5),
            max_pages=_env_int("MAX_PAGES", 30),
            max_questions=_env_int("MAX_QUESTIONS", 20),
            max_source_chars=_env_int("MAX_SOURCE_CHARS", 80_000),
        )

    def missing_settings(self) -> list[str]:
        missing = []
        if not self.project_id:
            missing.append("GOOGLE_CLOUD_PROJECT")
        if not self.document_ai_processor_id:
            missing.append("DOCUMENT_AI_PROCESSOR_ID")
        return missing


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return value
