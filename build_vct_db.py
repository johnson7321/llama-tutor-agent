import os
from langchain.docstore.document import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DB_DIR = os.path.join(SCRIPT_DIR, "yt_db")

def build_db(full_text):
    # ------------------ 建立向量資料庫 ------------------
    yt_doc = Document(page_content=full_text,metadata={"source": "YouTube"})
    documents = [yt_doc]

    # 建立向量資料庫
    os.makedirs(DB_DIR, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(documents)
    embedding = OllamaEmbeddings(model="nomic-embed-text")
    vectordb = Chroma.from_documents(docs, embedding, persist_directory=DB_DIR)
    retriever = vectordb.as_retriever()
    return retriever
def rag(user_input,messages,srt_content):
    retriever = build_db(srt_content)

    related_docs = retriever.invoke(user_input)[:3]
    context_chunks = [
        f"[來自：{doc.metadata.get('source', '未知')}]\n{doc.page_content}"
        for doc in related_docs
    ]
    context_text = "\n---\n".join(context_chunks)

    rag_prompt = f"""以下是影片字幕內容摘要，請根據這些內容來回答問題：\n\n{context_text}\n\n使用者問題：{user_input}\n請用繁體中文詳細解釋，並舉例子說明。"""

    messages.append({"role": "user", "content": rag_prompt})