"""
Модель refresh токена.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RefreshToken(Base, TimestampMixin):
    __tablename__ = 'refresh_tokens'

    # =========================================================================
    # ПОЛЯ МОДЕЛИ
    # =========================================================================

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            'users.id',
            ondelete='CASCADE'
        ),
        nullable=False
    )
    token_jti: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # =========================================================================
    # СВЯЗИ
    # =========================================================================

    user = relationship('User', back_populates='refresh_tokens')

    # =========================================================================
    # МЕТОДЫ МОДЕЛИ
    # =========================================================================

    def __init__(self, **kwargs):
        """Инициализация с значениями по умолчанию"""
        defaults = {
            'is_revoked': False,
            'revoked_at': None,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

    def revoke(self) -> None:
        """Отозвать токен"""
        if not self.is_revoked:
            self.is_revoked = True
            self.revoked_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Проверить, истёк ли токен"""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь.

        **Возвращает:**
            dict: Словарь с данными токена
        """
        result = {}
        for column in self.__table__.columns:
            result[column.name] = getattr(self, column.name)
        return result

    def __repr__(self) -> str:
        """
        Строковое представление пользователя.

        **Возвращает:**
            str: Строка с ID, user_id, частью token_jti и is_revoked refresh токена
        """
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, token_jti='{self.token_jti[:8]}...', is_revoked={self.is_revoked})>"
