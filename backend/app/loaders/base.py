from abc import ABC, abstractmethod
from typing import Union, Dict, Any
from pathlib import Path
from app.models.internal import Document


class BaseLoader(ABC):
    """Abstract base class for all document loaders."""

    @abstractmethod
    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        """
        Loads the document from the given source path or URI.
        Returns a common internal Document object.
        """
        pass
