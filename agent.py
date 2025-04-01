import ollama  # 載入 ollama 模組，與 Llama AI 進行互動
import prompt  # 載入 prompt 模組，用來儲存教學指引、測驗問題等內容

def chat_with_llama():
    # 用來儲存對話歷史，以便保持上下文
    messages = []  
    
    # 加入初始的對話訊息，包含指引、測驗問題、進度等
    messages.append({"role": "user", "content": prompt.tutor_guideline})
    messages.append({"role": "user", "content": prompt.teaching_quiz})
    messages.append({"role": "user", "content": prompt.Progress})
    
    # 讀取之前儲存的對話歷史，並加入到 messages 清單中
    with open("C:\Python\llama-tutor-agent\message_history.txt", "r", encoding="utf-8") as file:
        history = file.read()  # 讀取檔案內容
        
    messages.append({"role": "user", "content": "以下為我們的對話紀錄,讀取並繼續對話"+history})  # 把讀取的歷史對話加入

    while True:  # 持續進行對話，直到使用者結束
        try:
            # 接收使用者的輸入
            user_input = input("👤 你: ")

            if not (user_input):
                print("你沒有輸入任何內容")
                continue ;
            
            # 若使用者輸入 'exit'，則結束對話
            if user_input.lower() == "exit":
                print("🔴 結束對話...\n")
                break  # 跳出循環結束對話
            
            print("🤖 Llama: ")
            
            # 儲存使用者的輸入，並加入到對話歷史
            messages.append({"role": "user", "content": user_input})
            
            # 向 Llama 3.1 模型發送請求，並傳送對話歷史
            response = ollama.chat(model='llama3.1:latest', messages=messages)
            
            # 取得 AI 的回應內容，若沒有回應則顯示錯誤訊息
            bot_reply = response.get('message', {}).get('content', '⚠️ 無法獲取回應')
            
            # 把 AI 的回應加入到對話歷史中
            messages.append({"role": "assistant", "content": bot_reply})
            
            # 顯示 AI 的回應
            print(bot_reply)  

        except Exception as e:
            # 捕捉並顯示錯誤訊息
            print(f"⚠️ 發生錯誤: {e}\n")

# 主程式，執行與 Llama 的對話
if __name__ == "__main__":
    chat_with_llama()  # 呼叫對話函式
