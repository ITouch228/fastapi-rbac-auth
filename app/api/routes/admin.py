from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.access_rule import AccessRuleResponse, AccessRuleUpdateRequest
from app.schemas.common import APIMessage
from app.schemas.role import AssignRoleRequest, RoleResponse
from app.services.access_service import AccessService, Action
from app.services.admin_service import AdminService
from app.repositories.access_rules import AccessRuleRepository
from app.repositories.roles import RoleRepository

router = APIRouter(prefix='/admin', tags=['admin'])


async def require_admin(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> User:
    access_service = AccessService(RoleRepository(session), AccessRuleRepository(session))
    await access_service.check_access(user=current_user, element_name='rules', action=Action.READ)
    return current_user


@router.get('/rules', response_model=list[AccessRuleResponse], dependencies=[Depends(require_admin)])
async def list_rules(session: AsyncSession = Depends(get_db)):
    return await AdminService(session).list_rules()


@router.patch('/rules/{rule_id}', response_model=AccessRuleResponse, dependencies=[Depends(require_admin)])
async def update_rule(rule_id: int, payload: AccessRuleUpdateRequest, session: AsyncSession = Depends(get_db)):
    return await AdminService(session).update_rule(rule_id, payload)


@router.post('/users/{user_id}/roles', response_model=RoleResponse, dependencies=[Depends(require_admin)])
async def assign_role(user_id: int, payload: AssignRoleRequest, session: AsyncSession = Depends(get_db)):
    return await AdminService(session).assign_role(user_id, payload.role_name)


@router.get('/users/{user_id}/roles', response_model=list[RoleResponse], dependencies=[Depends(require_admin)])
async def get_user_roles(user_id: int, session: AsyncSession = Depends(get_db)):
    return await AdminService(session).get_user_roles(user_id)
