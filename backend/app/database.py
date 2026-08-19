"""CognoDB connection lifecycle and safe connectivity checks."""

from __future__ import annotations

import os
from typing import Final

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable


class DatabaseConfigurationError(Exception):
    """Raised when required database configuration is unavailable."""


class DatabaseConnectionError(Exception):
    """Raised when CognoDB cannot be reached or authenticated."""


REQUIRED_SETTINGS: Final = ("COGNODB_URI", "COGNODB_USERNAME", "COGNODB_PASSWORD")


class CognoDBConnection:
    """Owns the official Neo4j Bolt driver used for CognoDB Cloud."""

    def __init__(self) -> None:
        self._driver = None

    def connect(self) -> None:
        settings = {name: os.getenv(name) for name in REQUIRED_SETTINGS}
        if any(not value for value in settings.values()):
            raise DatabaseConfigurationError("CognoDB connection is not configured.")
        try:
            self._driver = GraphDatabase.driver(settings["COGNODB_URI"], auth=(settings["COGNODB_USERNAME"], settings["COGNODB_PASSWORD"]))
        except Exception as exc:
            raise DatabaseConnectionError("Unable to initialize the CognoDB connection.") from exc

    def verify_connectivity(self) -> None:
        if self._driver is None:
            self.connect()
        try:
            self._driver.verify_connectivity()
        except (AuthError, ServiceUnavailable, OSError) as exc:
            raise DatabaseConnectionError("Unable to connect to CognoDB. Check the service and credentials.") from exc
        except Exception as exc:
            raise DatabaseConnectionError("CognoDB connectivity check failed.") from exc

    def driver(self):
        """Return an initialized driver after a safe connectivity check."""
        self.verify_connectivity()
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None


database = CognoDBConnection()
