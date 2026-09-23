"""Runtime settings. No secrets are embedded in the source tree."""
from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent

@dataclass(frozen=True)
class Settings:
    data_dir: Path
    origin: str = "http://127.0.0.1:8000"
    secure_cookies: bool = False
    demo_content: bool = True

    @classmethod
    def from_env(cls):
        origin = os.getenv("SITE_ORIGIN", "http://127.0.0.1:8000").rstrip("/")
        secure = os.getenv("SECURE_COOKIES", "0") == "1"
        if secure and not origin.startswith("https://"):
            raise RuntimeError("SECURE_COOKIES=1 erfordert eine HTTPS-SITE_ORIGIN.")
        return cls(Path(os.getenv("DATA_DIR", ROOT.parent / "data")), origin, secure,
                   os.getenv("DEMO_CONTENT", "1") == "1")
