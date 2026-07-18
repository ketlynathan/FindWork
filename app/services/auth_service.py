"""
Job Hunter AI - Serviço de Autenticação e Segurança
Gerencia a criptografia de senhas (bcrypt) e a emissão/validação de tokens JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AuthService:
    """
    Abstrai as regras de segurança, hashing e tokenização da aplicação.
    Garante isolamento completo da lógica de criptografia contra camadas de interface.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera um hash seguro utilizando o algoritmo bcrypt com salting automático.
        
        Args:
            password: Senha em texto plano.
            
        Returns:
            String contendo o hash criptografado pronto para armazenamento.
        """
        # Converte a string da senha para bytes
        password_bytes = password.encode("utf-8")
        # Gera o salt e o hash correspondente
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Retorna o hash decodificado como string para salvar no varchar do banco
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Compara uma senha em texto plano com um hash guardado no banco de dados.
        
        Args:
            plain_password: Senha digitada pelo usuário no formulário de login.
            hashed_password: Hash recuperado do banco de dados.
            
        Returns:
            True se a senha for válida, False caso contrário.
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception as e:
            logger.error("Failed to verify password integrity", error=str(e))
            return False

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Gera e assina digitalmente um token JWT contendo os dados de identidade informados.
        
        Args:
            data: Dicionário contendo os claims (payload) do token (ex: {"sub": str(user_id)}).
            expires_delta: Tempo customizado de expiração (opcional).
            
        Returns:
            String do token JWT criptografado.
        """
        to_encode = data.copy()
        
        # Define o tempo de expiração do token
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        # Injeta o claim padronizado de expiração (exp) no payload
        to_encode.update({"exp": expire})
        
        # Assina o token utilizando a chave secreta global do sistema
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decodifica, valida a assinatura e verifica a expiração de um token JWT.
        
        Args:
            token: String contendo o JWT enviado pela aplicação.
            
        Returns:
            Dicionário com o payload original se o token for íntegro, ou None caso seja inválido/expirado.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT validation failed: Token signature has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("JWT validation failed: Token is structurally invalid")
            return None
        except Exception as e:
            logger.error("Unexpected error during JWT decoding", error=str(e))
            return None