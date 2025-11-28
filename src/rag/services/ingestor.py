import os
import logging
import hashlib
import json
from typing import List, Dict, Set
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.domain.models import Chunk
from src.rag.ports.repository import VectorStoreRepository

logger = logging.getLogger(__name__)

class IngestionService:
    """
    處理 ETL 流程：擷取 (Load)、轉換 (Split)、載入 (Store)。
    支援增量更新 (Incremental Update)，避免重複 Embedding。
    """
    def __init__(self, repo: VectorStoreRepository, state_file: str = "ingestion_state.json"):
        self.repo = repo
        self.state_file = state_file
        self.processed_files: Dict[str, str] = self._load_state()

    def _load_state(self) -> Dict[str, str]:
        """載入已處理檔案的狀態 (FilePath -> Hash)。"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load ingestion state: {e}")
        return {}

    def _save_state(self):
        """儲存目前的處理狀態。"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save ingestion state: {e}")

    def _calculate_file_hash(self, filepath: str) -> str:
        """計算檔案的 MD5 Hash。"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def load_docs(self, folder: str) -> List[Chunk]:
        """
        從資料夾載入文件並轉換為 Chunks (支援遞迴搜尋與增量更新)。
        """
        # [Fix] 即使資料夾不存在，也應該檢查是否有需要刪除的檔案 (因為資料夾可能被整個刪除了)
        # if not os.path.exists(folder):
        #     logger.warning(f"Document folder {folder} does not exist.")
        #     return []

        # 1. 掃描所有檔案並過濾出變更的檔案
        changed_files = []
        current_files_state = {}
        
        # 支援的副檔名
        supported_exts = {".pdf", ".txt", ".md"}
        
        if os.path.exists(folder):
            logger.info(f"Scanning {folder} for changes...")
            for root, _, files in os.walk(folder):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_exts:
                        full_path = os.path.join(root, file)
                        # 正規化路徑以作為 Key
                        norm_path = os.path.normpath(full_path)
                        
                        file_hash = self._calculate_file_hash(full_path)
                        current_files_state[norm_path] = file_hash
                        
                        # 檢查是否為新檔案或內容已變更
                        if norm_path not in self.processed_files or self.processed_files[norm_path] != file_hash:
                            changed_files.append(full_path)
        else:
            logger.warning(f"Document folder {folder} does not exist. Assuming all files deleted.")
            # current_files_state 保持為空，這將觸發所有已知檔案的刪除邏輯

        if not changed_files:
            # 檢查是否有被刪除的檔案
            # 找出在 state 中但不在目前檔案列表中的檔案
            current_files_set = set(current_files_state.keys())
            known_files_set = set(self.processed_files.keys())
            deleted_files = list(known_files_set - current_files_set)
            
            if deleted_files:
                logger.info(f"Found {len(deleted_files)} deleted files. Cleaning up database...")
                for deleted_file in deleted_files:
                    # 從 DB 移除
                    self.repo.delete_chunks_by_source(deleted_file)
                    
                    # 從狀態移除
                    del self.processed_files[deleted_file]
                
                self._save_state()
                logger.info("Cleanup complete.")
            else:
                logger.info("No new, modified, or deleted files found. Skipping ingestion.")
            
            return []

        logger.info(f"Found {len(changed_files)} new or modified files to ingest.")

        # 2. 針對變更的檔案進行載入
        raw_docs = []
        for file_path in changed_files:
            try:
                ext = os.path.splitext(file_path)[1].lower()
                loader = None
                
                if ext == ".pdf":
                    loader = PyPDFLoader(file_path)
                elif ext in [".txt", ".md"]:
                    loader = TextLoader(file_path, encoding="utf-8")
                
                if loader:
                    docs = loader.load()
                    # [Fix] 正規化 metadata 中的 source 路徑，確保與 ingestion_state.json 一致
                    # LangChain Loader 通常會將 source 設為絕對路徑或相對路徑，視輸入而定。
                    # 為了確保刪除時能匹配，我們統一強制將 metadata['source'] 設為 os.normpath(file_path)
                    norm_path = os.path.normpath(file_path)
                    
                    # [Fix] 針對修改的檔案，先清除舊的 Chunks，避免重複或過時資料
                    logger.info(f"Clearing old chunks for modified file: {norm_path}")
                    self.repo.delete_chunks_by_source(norm_path)

                    for doc in docs:
                        doc.metadata['source'] = norm_path
                        
                    raw_docs.extend(docs)
                    # 更新狀態 (暫存)
                    self.processed_files[norm_path] = self._calculate_file_hash(file_path)
                    
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        if not raw_docs:
            return []

        logger.info(f"Loaded {len(raw_docs)} raw documents from changed files.")
        
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
            # 只有在成功寫入 DB 後才儲存狀態
            self._save_state()
            logger.info("Ingestion state saved.")
