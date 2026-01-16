from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseSkill(ABC):
    """
    Standard Interface for Yunshu System Skills.
    All skills must inherit from this class and implement the abstract methods.
    """
    
    def __init__(self, metadata: Dict[str, Any]):
        self.metadata = metadata
        self.context = {}

    @abstractmethod
    def init(self) -> bool:
        """
        Initialize the skill (e.g., load models, connect DB).
        Returns:
            bool: True if initialization is successful.
        """
        pass

    @abstractmethod
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill logic.
        Args:
            params: Input parameters defined in skill.yaml.
        Returns:
            Dict: Output data matching the output spec.
                  Standard keys:
                  - 'content': The main result (markdown/text)
                  - 'files': List of generated file paths
                  - 'meta': Additional metadata
        """
        pass

    @abstractmethod
    def destroy(self):
        """
        Cleanup resources.
        """
        pass

    def validate_input(self, params: Dict[str, Any]) -> bool:
        """
        Validate input parameters against metadata.
        (Implemented by the SDK, can be overridden)
        """
        # TODO: Implement validation logic based on self.metadata['input']
        return True
