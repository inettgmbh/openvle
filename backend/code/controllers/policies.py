import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import Settings
from core.exceptions import (
    BadRequestError,
    InvalidStatusError,
    ObjectDeleteIntegrityError,
    RelationNotFound,
)
from middlewares.i18n import _
from models import Changelog, ObjectPermission, PoliciesUser, Policy, Tag
from schemas.policies import PolicyCreate, PolicyUpdate, PolicyUserAgree

from .base import CRUDBase
from .object_permissions import CRUDObjectPermission

settings = Settings()


class CRUDPolicy(CRUDBase[Policy, PolicyCreate, PolicyUpdate]):
    # Get Policy by name
    def get_by_name(self, db: Session, *, name: str) -> Policy | None:
        return db.query(Policy).filter(Policy.name == name).first()

    # Get PolicyUser by id and user_id
    def get_policy_user(
        self, db: Session, id: Any, user_id: Any
    ) -> Policy | None:
        obj = (
            db.query(PoliciesUser)
            .filter(
                PoliciesUser.policy_id == id, PoliciesUser.user_id == user_id
            )
            .first()
        )
        if not obj:
            raise RelationNotFound(
                model_name_1="Policy",
                obj_id_1=id,
                model_name_2="User",
                obj_id_2=user_id,
            )
        return obj

    def get_outstanding(self, db: Session, user_id: Any) -> list | None:
        agreed_ids = db.query(PoliciesUser.policy_id).filter(
            PoliciesUser.user_id == user_id
        )
        outstanding = (
            db.query(Policy.id)
            .filter(
                Policy.active.is_(True),
                ~Policy.id.in_(agreed_ids.scalar_subquery()),
            )
            .all()
        )
        return [row[0] for row in outstanding]

    # Create Policy
    def create(
        self, db: Session, request: Request, *, obj_in: PolicyCreate
    ) -> Policy:
        obj_in_data = jsonable_encoder(obj_in)
        self._initialize_object_fields(
            db=db, obj_data_in=obj_in_data, request=request
        )
        self.db_obj.active = False
        self.db_obj = self._commit(db, self.db_obj)
        CRUDObjectPermission(ObjectPermission).create_full(
            db, request, "Policy", self.db_obj.id, request.user.id
        )
        db.refresh(self.db_obj)
        return self.db_obj

    # Update Policy
    def update(
        self, id: Any, db: Session, request: Request, *, obj_in: PolicyUpdate
    ) -> Policy:
        self.db_obj = self.get(db, id)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        # Check if Policy.active is being changed
        POLICY_ACTIVE: bool
        if "active" in update_data:
            POLICY_ACTIVE = update_data["active"]
        else:
            POLICY_ACTIVE = self.db_obj.active

        if obj_in.name or obj_in.description or obj_in.content:
            # Only update rest of fields if POLICY_ACTIVE is False
            if not POLICY_ACTIVE:
                obj_data = jsonable_encoder(self.db_obj)
                for field in obj_data:
                    if field in update_data:
                        setattr(self.db_obj, field, update_data[field])
            else:
                raise InvalidStatusError(
                    current_status="Active",
                    action="policy_update",
                    valid_status_list=["Inactive"],
                )

        self.db_obj.active = POLICY_ACTIVE
        self._update_meta(request)
        return self._commit(db, self.db_obj)

    # Create Policy - User object
    def agree_to_policy(
        self, id: Any, db: Session, request: Request, *, obj_in: PolicyUserAgree
    ) -> PoliciesUser:
        self.db_obj = self.get(db, id)
        policy_user = PoliciesUser()
        policy_user.id = uuid.uuid4()
        # Check if user already agreed
        agreed_check = (
            db.query(PoliciesUser)
            .filter(
                PoliciesUser.user_id == request.user.id,
                PoliciesUser.policy_id == self.db_obj.id,
            )
            .first()
        )
        if agreed_check:
            raise BadRequestError(
                message=_("User already agreed to this policy.")
            )
        policy_user.user_id = request.user.id
        policy_user.policy_id = self.db_obj.id
        policy_user.createdAt = datetime.now(timezone.utc)
        policy_user.updatedAt = datetime.now(timezone.utc)
        policy_user.createdById = request.user.id
        policy_user.updatedById = request.user.id
        db.add(policy_user)
        self._commit(db)
        db.refresh(policy_user)
        return policy_user

    # Delete Policy with ID
    def delete(self, db: Session, id: int) -> Policy | None:
        self.db_obj = self.get(db, id)
        # Check if Policy is still active
        if self.db_obj.active:
            raise InvalidStatusError(
                current_status="Active",
                action="policy_delete",
                valid_status_list=["Inactive"],
            )
        try:
            # Delete Policy - User relations
            policy_users = db.query(PoliciesUser).filter(
                PoliciesUser.policy_id == id
            )
            for pol_user in policy_users:
                db.delete(pol_user)
            db.commit()
        except:
            raise BadRequestError(
                message=_(
                    "Unable to delete PoliciesUser relations with Policy ID: {id}."
                ).format(id=id)
            )
        try:
            db.delete(self.db_obj)
            # Delete changelogs
            changelogs = db.query(Changelog).filter(Changelog.objectId == id)
            for changelog in changelogs:
                db.delete(changelog)
            # Delete object permissions
            object_permissions = db.query(ObjectPermission).filter(
                ObjectPermission.object_id == id
            )
            for perm in object_permissions:
                db.delete(perm)
            tags = db.query(Tag).filter(
                Tag.objectId == id, Tag.objectType == self.model.__name__
            )
            for tag in tags:
                db.delete(tag)
            self._commit(db)
            return {
                "detail": _("{model} with ID {id} has been deleted.").format(
                    model=self.model.__name__, id=id
                )
            }
        except IntegrityError:
            raise ObjectDeleteIntegrityError(model_name=Policy.__name__)


policy = CRUDPolicy(Policy)
