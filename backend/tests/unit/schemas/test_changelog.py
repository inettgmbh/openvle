"""Tests for schemas/changelog.py - Changelog schema validation."""

import uuid
from datetime import datetime, timezone

from schemas.changelog import Changelog


class TestChangelog:
    def test_valid_changelog(self):
        cl = Changelog(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld="old",
            valueNew="new",
            object="User",
            objectId=uuid.uuid4(),
            userId=uuid.uuid4(),
        )
        assert cl.valueOld == "old"
        assert cl.valueNew == "new"
        assert cl.object == "User"
