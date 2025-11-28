from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class Chunk:
    """
    代表從較大文件中分割出來的一段文字。
    這是檢索的核心單位。
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

@dataclass
class SearchResult:
    """
    代表檢索到的 Chunk 及其相關性分數。
    """
    chunk: Chunk
    score: float
