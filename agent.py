import ollama
import prompt
import message_history_txt

def chat_with_llama():

    
    messages = []  # 用來儲存對話歷史，以便維持上下文
    
    messages.append({"role": "user", "content": prompt.tutor_guideline})
    messages.append({"role": "user", "content": prompt.teaching_quiz})
    messages.append({"role": "user", "content": prompt.Progress})
    messages.append({"role": "user", "content": message_history_txt.message_history})


    while True:
        try:
            user_input = input("👤 你: ")  # 接收使用者輸入
            
            if user_input.lower() == "exit":  # 若使用者輸入 'exit'，則結束對話
                print("🔴 結束對話...\n")
                break
            
            messages.append({"role": "user", "content": user_input})  # 儲存使用者輸入
            
            response = ollama.chat(model='llama3.1', messages=messages)  # 向 Llama 3.1  發送請求
            
            bot_reply = response.get('message', {}).get('content', '⚠️ 無法獲取回應')  # 取得回應內容，並處理可能的錯誤
            
            messages.append({"role": "assistant", "content": bot_reply})  # 儲存 AI 的回應
            
            
            print("🤖 Llama: "+bot_reply)  # 顯示 AI 的回應

        
        except Exception as e:
            print(f"⚠️ 發生錯誤: {e}\n")  # 捕捉並顯示錯誤訊息

if __name__ == "__main__":
    chat_with_llama()  # 執行對話函式
