from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from controllers.users import CRUDUser
from core import dependencies
from models.users import User as UserModel
from schemas.users import User, UserSelf, UserUpdatePassword

router = APIRouter(
    prefix="/me",
    tags=["me"],
    responses={404: {"detail": "Not found"}},
)


# Get own user object
@router.get(
    "",
    status_code=200,
    response_model=UserSelf,
    operation_id="me_read",
    summary="Get own user",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_me(
    request: Request,
    db: Session = Depends(dependencies.get_db),
):
    return CRUDUser(UserModel).get(db, id=request.user.id)


# Get effective permission list of own user
@router.get(
    "/permissions",
    status_code=200,
    operation_id="me_permissions_read",
    summary="Get list of own permissions",
    dependencies=[Depends(dependencies.get_current_user)],
)
def get_me_permissions(
    request: Request,
    db: Session = Depends(dependencies.get_db),
):
    return CRUDUser(UserModel).get_effective_permissions_new(
        db=db, id=request.user.id
    )


# Update own password
@router.put(
    "/password",
    status_code=200,
    response_model=User,
    operation_id="me_password_update",
    summary="Update own password",
    dependencies=[Depends(dependencies.get_current_user)],
)
def update_me_password(
    *,
    user_in: UserUpdatePassword,
    db: Session = Depends(dependencies.get_db),
    request: Request,
) -> User:
    return CRUDUser(UserModel).update_password(
        db=db, request=request, obj_in=user_in
    )
