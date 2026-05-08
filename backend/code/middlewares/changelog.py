import uuid
from datetime import datetime, timezone
from typing import TypeVar

from fastapi import Request

from core.core_utils import prepare_changelog_values
from core.mariadb import SessionLocal
from models.base import DBBaseModel
from models.changelog import Changelog as ChangelogModel

ModelType = TypeVar("ModelType", bound=DBBaseModel)


class ChangelogMiddleware:
    def __init__(self, model: type[ModelType]):
        self.object = model

    async def __call__(self, request: Request):
        # Break early if method is not PUT or POST
        method = request.method
        if method not in ["PUT", "POST"]:
            return

        # Break early if the object is being created
        if "id" not in request.path_params:
            return

        try:
            request_body = await request.json()
        except:
            return

        if "hashed_password" in request_body or "password_new" in request_body:
            return

        objectId = request.path_params["id"]

        # Connect to DB
        db = SessionLocal()

        object_old = db.get(self.object, uuid.UUID(objectId))

        values_old = {}
        values_new = {}

        try:
            for var in request_body:
                old_value = getattr(object_old, var)
                if request_body[var] != old_value:
                    values_old[var] = old_value
                    values_new[var] = request_body[var]
        except AttributeError:
            db.close()
            return

        # If no there are no new values, return
        if not values_new:
            db.close()
            return

        # Remove unchanged values
        unchanged_keys = [
            key for key, val in values_new.items() if val == values_old[key]
        ]
        for key in unchanged_keys:
            values_old.pop(key)
            values_new.pop(key)

        # Create a new Changelog instance
        value_old, value_new = prepare_changelog_values(values_old, values_new)
        new_changelog = ChangelogModel(
            id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            valueOld=value_old,
            valueNew=value_new,
            object=str(self.object.__name__),
            objectId=uuid.UUID(objectId),
            userId=request.user.id,
        )

        # Add the changelog to the session and commit the changes
        db.add(new_changelog)
        db.commit()
        db.refresh(new_changelog)
        db.close()
