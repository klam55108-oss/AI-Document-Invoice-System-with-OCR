"""Abstract base class for dataset adapters."""

from abc import ABC, abstractmethod
from typing import List
from brain.schemas import CanonicalInvoiceSchema

class BaseDatasetAdapter(ABC):
    """Base class for all HuggingFace dataset adapters."""

    @abstractmethod
    async def load(self, limit: int = 10) -> List[CanonicalInvoiceSchema]:
        """Load and normalize records from the dataset."""
        pass
