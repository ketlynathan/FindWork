"""
Job Hunter AI - Serviço de Usuários
Orquestra as regras de negócio para registro, autenticação e gerenciamento de perfis.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """
    Classe de serviço para gerenciamento do ciclo de vida dos usuários.
    Garante a integridade das regras de negócio antes de acionar a persistência.
    """

    def __init__(self, db_session: AsyncSession):
        """Inicializa o serviço injetando a sessão de banco no repositório de usuários."""
        self.user_repo = UserRepository(db_session=db_session)
        self.auth_service = AuthService()

    async def register_user(self, user_data: Dict[str, Any]) -> User:
        """
        Registra um novo usuário no sistema se o e-mail for inédito.
        
        Args:
            user_data: Dicionário contendo 'name', 'email' e 'password' em texto plano.
            
        Returns:
            Instância do modelo User criado e persistido.
            
        Raises:
            ValueError: Se o e-mail já estiver cadastrado no sistema.
        """
        email = user_data.get("email", "").strip().lower()
        
        # Verifica duplicidade de e-mail antes de processar o registro
        existing_user = await self.user_repo.get_by_email(email=email)
        if existing_user:
            logger.warning(f"Registration rejected: Email '{email}' already exists")
            raise ValueError("Este e-mail já está cadastrado no sistema.")

        # Prepara os dados purificando o e-mail e aplicando hash na senha
        cleaned_data = {
            "name": user_data.get("name", "").strip(),
            "email": email,
            "hashed_password": self.auth_service.hash_password(user_data["password"]),
            "is_active": True
        }

        logger.info(f"Registering new user profile for email: {email}")
        return await self.user_repo.create(obj_in_data=cleaned_data)

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Valida as credenciais do usuário e emite um token de acesso em caso de sucesso.
        
        Args:
            email: E-mail informado na tentativa de login.
            password: Senha em texto plano.
            
        Returns:
            Dicionário contendo os dados do usuário e o token JWT, ou None se inválido.
        """
        cleaned_email = email.strip().lower()
        user = await self.user_repo.get_by_email(email=cleaned_email)
        
        if not user or not user.is_active:
            logger.warning(f"Authentication failed: User not found or inactive for email '{cleaned_email}'")
            return None

        # Valida a integridade da senha com o hash do banco
        if not self.auth_service.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid credentials for email '{cleaned_email}'")
            return None

        logger.info(f"User authenticated successfully: {user.id}")
        
        # Cria o payload e assina o token de acesso
        token_payload = {"sub": str(user.id), "email": user.email}
        access_token = self.auth_service.create_access_token(data=token_payload)

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            "access_token": access_token
        }