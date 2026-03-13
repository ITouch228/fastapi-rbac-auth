"""
Модели Pydantic для стандартных сообщений и базовой конфигурации ORM.
"""

from pydantic import BaseModel, ConfigDict


class APIMessage(BaseModel):
    """Универсальная модель для сообщений API"""

    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


class ORMBase(BaseModel):
    """Базовая модель Pydantic с поддержкой from_attributes"""

    model_config = ConfigDict(from_attributes=True)
