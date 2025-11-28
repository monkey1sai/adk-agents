import os
import logging
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.domain.models import Chunk
from src.rag.ports.repository import VectorStoreRepository

logger = logging.getLogger(__name__)

class IngestionService:
    """
    處理 ETL 流程：擷取 (Load)、轉換 (Split)、載入 (Store)。
    """
    def __init__(self, repo: VectorStoreRepository):
        self.repo = repo

    def load_docs(self, folder: str) -> List[Chunk]:
        """
        從資料夾載入文件並轉換為 Chunks。
        """
        if not os.path.exists(folder):
            logger.warning(f"Document folder {folder} does not exist.")
            return []

        raw_docs = []
        for file in os.listdir(folder):
            path = os.path.join(folder, file)
            try:
                if file.endswith(".pdf"):
                    loader = PyPDFLoader(path)
                    raw_docs.extend(loader.load())
                elif file.endswith(".txt") or file.endswith(".md"):
                    loader = TextLoader(path, encoding="utf-8")
                    raw_docs.extend(loader.load())
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")

        logger.info(f"Loaded {len(raw_docs)} raw documents.")
        
        # Split
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
        )
        split_docs = splitter.split_documents(raw_docs)
        
        # Convert to Domain Chunks
        chunks = [
            Chunk(content=doc.page_content, metadata=doc.metadata)
            for doc in split_docs
        ]
        
        logger.info(f"Created {len(chunks)} chunks.")
        return chunks

    def run_pipeline(self, folder: str = "docs"):
        """
        執行完整的資料匯入流程。
        """
        chunks = self.load_docs(folder)
        if chunks:
            self.repo.add_chunks(chunks)
