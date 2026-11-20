from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return the generated answer as plain text."""
