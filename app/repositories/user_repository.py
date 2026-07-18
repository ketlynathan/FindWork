"""
Job Hunter AI - Repositório de Usuários
Implementação concreta do padrão Repository para operações na tabela 'user'.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repositório especializado para gerenciamento de dados de usuários.
    Abstrai consultas complexas e regras de persistência da entidade User.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o repositório vinculando explicitamente o modelo User."""
        super().__init__(model=User, db_session=db_session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Busca um usuário no banco de dados através do e-mail informado.
        Utilizado amplamente no fluxo de login e validação de novos cadastros.
        
        Args:
            email: String contendo o e-mail exato do usuário.
            
        Returns:
            Instância de User se encontrado, ou None caso contrário.
        """
        query = select(self.model).where(self.model.email == email)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()