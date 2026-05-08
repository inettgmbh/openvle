from pymongo import MongoClient
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    ServerSelectionTimeoutError,
)

from .config import Settings
from .exceptions import MongoDBConnectionError

settings = Settings()

try:
    # Connect to MongoDB
    client = MongoClient(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        username=settings.mongodb_user,
        password=settings.mongodb_password,
        authSource="admin",
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )
    # Test connection is reachable
    client.admin.command("ping")
    db = client[settings.mongodb_database]
except ServerSelectionTimeoutError as e:
    # Add local logger call with exception msg
    raise MongoDBConnectionError()
except ConnectionFailure as e:
    # Add local logger call with exception msg
    raise MongoDBConnectionError()
except ConfigurationError as e:
    # Add local logger call with exception msg
    raise MongoDBConnectionError()
