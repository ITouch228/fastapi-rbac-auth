from pydantic import BaseModel, ConfigDict

from app.schemas.common import ORMBase


class AccessRuleResponse(ORMBase):
    id: int
    role_id: int
    element_id: int
    read_permission: bool
    read_all_permission: bool
    create_permission: bool
    update_permission: bool
    update_all_permission: bool
    delete_permission: bool
    delete_all_permission: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "role_id": 2,
                "element_id": 3,
                "read_permission": True,
                "read_all_permission": False,
                "create_permission": True,
                "update_permission": True,
                "update_all_permission": False,
                "delete_permission": False,
                "delete_all_permission": False,
            }
        },
    )


class AccessRuleUpdateRequest(BaseModel):
    read_permission: bool | None = None
    read_all_permission: bool | None = None
    create_permission: bool | None = None
    update_permission: bool | None = None
    update_all_permission: bool | None = None
    delete_permission: bool | None = None
    delete_all_permission: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "read_permission": True,
                "read_all_permission": True,
                "create_permission": True,
                "update_permission": True,
                "update_all_permission": True,
                "delete_permission": True,
                "delete_all_permission": False,
            }
        }
    )
