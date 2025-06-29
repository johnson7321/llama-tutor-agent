from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 模擬字幕 srt_content
srt_content = """
1
00:00:00,000 --> 00:00:03,000
太陽是一顆恆星，它提供地球光和熱。

2
00:00:03,001 --> 00:00:06,000
地球自轉導致白天和黑夜的交替。

3
00:00:06,001 --> 00:00:09,000
月亮圍繞地球運行，造成潮汐現象。
"""

# 建立 retriever
def build_db(srt_content):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
    docs = text_splitter.create_documents([srt_content])

    # 為每段加上 source metadata
    for i, doc in enumerate(docs):
        doc.metadata = {"source": "YouTube", "chunk": i}

    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    vectordb = FAISS.from_documents(docs, embedding_model)

    return vectordb.as_retriever()

# RAG 函數
def rag(user_input, messages, srt_content):
    retriever = build_db(srt_content)
    related_docs = retriever.invoke(user_input)[:3]

    context_chunks = [
        f"[來自：{doc.metadata.get('source', '未知')}]\n{doc.page_content}"
        for doc in related_docs
    ]

    context_text = "\n---\n".join(context_chunks)
    rag_prompt = f"""以下是影片字幕內容摘要，請根據這些內容來回答問題：\n\n{context_text}\n\n使用者問題：{user_input}\n請用繁體中文詳細解釋，並舉例子說明。"""
    messages.append({"role": "user", "content": rag_prompt})

    print(rag_prompt)

# 測試
messages = []
rag("為什麼會有白天和黑夜？", messages, srt_content)
