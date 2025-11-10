from abc import ABC, abstractmethod
from typing import Optional, Any

from core.logging import logger


class Connection(ABC):
    """
    Abstract Singleton Connection Base Class
    """
    _instance = None
    _client = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation"""
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @abstractmethod
    async def connect(self) -> None:
        """Connection yaratish - subclass-da implement qilish kerak"""
        raise NotImplementedError

    async def disconnect(self) -> None:
        """
        Connection-ni o'chirish
        Async yoki sync close() -ni handle qiladi
        """
        try:
            if self._client:
                try:
                    await self._client.close()
                except TypeError:
                    self._client.close()
            
            self._client = None
            self._instance = None
            logger.info(f"Disconnected from {self.__class__.__name__} server")
        
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
            raise

    async def is_connected(self) -> bool:
        """Connection status tekshirish"""
        return self._client is not None

    def get_client(self) -> Optional[Any]:
        """Client-ni olish"""
        return self._client
