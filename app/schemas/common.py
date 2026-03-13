from pydantic import BaseModel, ConfigDict


class APIMessage(BaseModel):
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
