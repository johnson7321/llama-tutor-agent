import ollama
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings 
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ------------------ 載入 PDF 教材並建立向量資料庫 ------------------

PDF_PATH = "Abraham Silberschatz Operating System Concepts.pdf"  # ← 放你的教材
DB_DIR = "./db"

if not os.path.exists(DB_DIR):
    print("🧠 第一次執行：載入 PDF 並建立向量資料庫...")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(documents)

    embedding = OllamaEmbeddings(model="nomic-embed-text")  # 記得先 ollama pull nomic-embed-text
    vectordb = Chroma.from_documents(docs, embedding, persist_directory=DB_DIR)
    # ❌ 不需要 vectordb.persist()，新版會自動儲存
else:
    print("✅ 已載入本地資料庫")
    embedding = OllamaEmbeddings(model="nomic-embed-text")
    vectordb = Chroma(persist_directory=DB_DIR, embedding_function=embedding)

retriever = vectordb.as_retriever()

# ------------------ LLM 訊息處理 ------------------

messages = [{"role": "system", "content": "你是一位用繁體中文回答的家教老師，請用簡單方式講解問題。"}]
MODEL_NAME = 'llama3'

def chat_with_ollama(prompt):
    # 🔍 檢索相關內容（RAG）
    related_docs = retriever.invoke(prompt)
    context_text = "\n---\n".join([doc.page_content for doc in related_docs[:3]])  # 取前3筆資料

    # 包裝 prompt 加入上下文
    rag_prompt = f"""以下是教材內容摘要，請根據這些內容來回答問題：

    {context_text}

    使用者問題：{prompt}
    請用繁體中文詳細解釋，並舉例子說明。"""

    messages.append({"role": "user", "content": rag_prompt})

    try:
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        reply = response['message']['content']
        messages.append({"role": "assistant", "content": reply})

        # 控制訊息堆積（簡易記憶）
        if len(messages) > 20:
            messages.pop(1)

        return reply
    except Exception as e:
        return f"❌ 發生錯誤：{e}"

# ------------------ 主程式 ------------------

if __name__ == "__main__":
    print("📘 RAG 家教系統已啟動，輸入 quit 離開")

    while True:
        user_input = input("你：").strip()
        
        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "bye"]:
            print("👋 再見，祝學習愉快！")
            break

        response = chat_with_ollama(user_input)
        print("家教老師：", response)
