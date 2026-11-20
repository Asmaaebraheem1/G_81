"""Shared Flask extensions."""

from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

jwt = JWTManager()
csrf = CSRFProtect()
migrate = Migrate()
