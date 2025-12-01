import asyncio
import logging
import sys
from src.rag.adapters.chroma_repository import ChromaRepository
from src.config import settings

# 設定 Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("=== RAG Diagnostic Tool ===")
    
    # 1. 初始化 Repository
    repo = ChromaRepository(
        persist_directory=settings.rag.db_path,
        embedding_model=settings.rag.embed_model
    )
    
    query = "吳東凌"
    print(f"\nSearching for: '{query}'")
    
    # 2. 執行搜尋
    results = await repo.search(query, k=5)
    
    if not results:
        print("No results found in Vector DB.")
    else:
        print(f"Found {len(results)} chunks:\n")
        for i, res in enumerate(results):
            print(f"--- Result {i+1} (Score: {res.score:.4f}) ---")
            print(f"Source: {res.chunk.metadata.get('source', 'Unknown')}")
            
            # Safely print content handling encoding issues
            try:
                content_preview = res.chunk.content[:200]
                # Encode to the stdout encoding (likely cp950 on Windows) replacing errors
                encoding = sys.stdout.encoding or 'utf-8'
                safe_content = content_preview.encode(encoding, errors='replace').decode(encoding)
                print(f"Content Preview: {safe_content}...")
            except Exception as e:
                print(f"Content Preview: [Error displaying content: {e}]")
                
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
