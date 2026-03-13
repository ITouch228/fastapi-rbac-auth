from pydantic import BaseModel, ConfigDict

from app.schemas.common import ORMBase


class RoleResponse(ORMBase):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "name": "manager",
                "description": None
            }
        },
    )


class AssignRoleRequest(BaseModel):
    role_name: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role_name": "manager"
            }
        }
    )
