"""CarbonWise backend entrypoint."""

from app import create_app
from app.core.config import Config

app = create_app(Config)


if __name__ == "__main__":
    app.run(
        host=app.config.get("HOST", "127.0.0.1"),
        port=int(app.config.get("PORT", 5000)),
        debug=app.config.get("DEBUG", False),
    )
