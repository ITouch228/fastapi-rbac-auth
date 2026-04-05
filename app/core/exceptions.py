"""
Модуль HTTP исключений.

Содержит вспомогательные функции для создания
типовых HTTPException с часто используемыми
статус-кодами приложения.

Используется для:
- Ошибок аутентификации
- Ошибок авторизации
- Ошибок валидации запроса
- Ошибок поиска сущностей
"""

from fastapi import HTTPException, status

# =========================================================================
# ВСПОМОГАТЕЛЬНЫЕ HTTP ИСКЛЮЧЕНИЯ
# =========================================================================

def unauthorized(detail: str = 'Not authenticated') -> HTTPException:
    """
    Ошибка неавторизованного доступа.

    **Параметры:**
        - **detail** (str): Текст ошибки

    **Возвращает:**
        HTTPException: Исключение со статусом 401
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail
    )


def forbidden(detail: str = 'Forbidden') -> HTTPException:
    """
    Ошибка запрета доступа.

    **Параметры:**
        - **detail** (str): Текст ошибки

    **Возвращает:**
        HTTPException: Исключение со статусом 403
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )


def bad_request(detail: str) -> HTTPException:
    """
    Ошибка некорректного запроса.

    **Параметры:**
        - **detail** (str): Текст ошибки

    **Возвращает:**
        HTTPException: Исключение со статусом 400
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )


def not_found(detail: str) -> HTTPException:
    """
    Ошибка отсутствия сущности.

    **Параметры:**
        - **detail** (str): Текст ошибки

    **Возвращает:**
        HTTPException: Исключение со статусом 404
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )
