from typing import List, Protocol
from src.rag.domain.models import Chunk, SearchResult

class VectorStoreRepository(Protocol):
    """
    Port definition for Vector Store operations.
    Decouples the business logic from specific DB implementations (Chroma, Pinecone, etc.).
    """
    
    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Persist chunks into the vector store."""
        ...

    async def search(self, query: str, k: int = 4) -> List[SearchResult]:
        """Retrieve relevant chunks for a given query asynchronously."""
        ...
