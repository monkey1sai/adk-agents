from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class Chunk:
    """
    Represents a piece of text that has been split from a larger document.
    This is the core unit of retrieval.
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class SearchResult:
    """
    Represents a retrieved chunk with its relevance score.
    """
    chunk: Chunk
    score: float
