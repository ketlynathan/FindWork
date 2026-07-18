"""
Job Hunter AI - Repositório Base Genérico
Define o contrato de CRUD e operações assíncronas padrão para todas as entidades.
"""

import uuid
from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base_class import Base

# Variável de tipo (Type Variable) vinculada à nossa classe base do ORM
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Classe base para gerenciamento de persistência de dados utilizando Repository Pattern.
    Abstrai as consultas fundamentais do SQLAlchemy de forma assíncrona.
    """

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        """
        Inicializa o repositório vinculando o modelo e a sessão correspondente.
        
        Args:
            model: A classe do modelo SQLAlchemy (ex: User, Job).
            db_session: Instância de uma AsyncSession ativa do banco de dados.
        """
        self.model = model
        self.db_session = db_session

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        """Recupera um registro único com base em seu ID de UUID."""
        query = select(self.model).where(self.model.id == id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retorna uma lista paginada de registros."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in_data: dict) -> ModelType:
        """Cria e persiste um novo registro a partir de um dicionário de dados."""
        db_obj = self.model(**obj_in_data)
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in_data: dict) -> ModelType:
        """
        Atualiza campos específicos de um objeto existente na sessão.
        
        Args:
            db_obj: O objeto gerenciado originalmente recuperado do banco.
            obj_in_data: Dicionário contendo os novos campos a atualizar.
        """
        for field in obj_in_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in_data[field])
                
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        return db_obj

    async def delete(self, id: uuid.UUID) -> bool:
        """Remove fisicamente um registro do banco pelo ID."""
        query = delete(self.model).where(self.model.id == id)
        result = await self.db_session.execute(query)
        await self.db_session.commit()
        return result.rowcount > 0