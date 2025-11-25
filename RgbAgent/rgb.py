from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
import os

# ------------------------------
# 設定
# ------------------------------

DB_PATH = "vector_db"

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.1:8b"      # 可換 qwen2.5 、mistral 等

# ------------------------------
# 1. 載入文件
# ------------------------------

def load_docs(folder="docs"):
    docs = []
    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if file.endswith(".pdf"):
            docs.extend(PyPDFLoader(path).load())
        elif file.endswith(".txt") or file.endswith(".md"):
            docs.extend(TextLoader(path, encoding="utf-8").load())
    return docs

# ------------------------------
# 2. 分段器
# ------------------------------

def split_docs(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
    )
    return splitter.split_documents(documents)

# ------------------------------
# 3. 建立向量資料庫
# ------------------------------

def create_vector_db(chunks):
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    db = Chroma.from_documents(chunks, embeddings, persist_directory=DB_PATH)
    db.persist()
    return db

# ------------------------------
# 4. 建立 RAG Pipeline
# ------------------------------

def build_rag():
    llm = Ollama(model=LLM_MODEL)

    db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=OllamaEmbeddings(model=EMBED_MODEL)
    )

    retriever = db.as_retriever(search_kwargs={"k": 4})

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain

# ------------------------------
# 主流程
# ------------------------------

def init_rag():
    print("📄 Loading documents...")
    docs = load_docs()
    print(f"Loaded {len(docs)} documents")

    print("🔪 Splitting text...")
    chunks = split_docs(docs)
    print(f"Split into {len(chunks)} chunks")

    print("🔍 Building vector DB...")
    create_vector_db(chunks)
    print("Vector DB created!")

def ask_question(question):
    qa = build_rag()
    result = qa(question)

    print("\n====== 回答 ======")
    print(result["result"])

    print("\n====== 參考來源 ======")
    for doc in result["source_documents"]:
        print(f"- {doc.metadata}")

# ------------------------------
# 入口
# ------------------------------

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_rag()

    while True:
        q = input("\n請輸入你的問題： ")
        ask_question(q)
