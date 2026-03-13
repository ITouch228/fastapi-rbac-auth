"""
Модуль работы с сессией базы данных.

Содержит:
- Создание async engine
- Фабрику асинхронных сессий
- FastAPI dependency для получения сессии БД

Используется для:
- Подключения к базе данных
- Получения AsyncSession в сервисах и роутерах
- Управления жизненным циклом сессии в запросах
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    future=True,
    echo=settings.debug
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# =========================================================================
# ЗАВИСИМОСТИ БАЗЫ ДАННЫХ
# =========================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии базы данных.

    Создаёт асинхронную сессию на время обработки запроса
    и закрывает её после завершения работы.

    **Возвращает:**
        AsyncGenerator[AsyncSession, None]: Асинхронная сессия базы данных
    """
    async with AsyncSessionLocal() as session:
        yield session
