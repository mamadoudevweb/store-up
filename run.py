"""Application entry point."""
from __future__ import annotations

import os

from src.app import create_app

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    app.run()
