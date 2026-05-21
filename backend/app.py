"""Application entry point"""

from . import create_app
from .extensions import db

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
