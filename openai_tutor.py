import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()  # 加載 .env 檔案
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 配置 OpenAI API
openai.api_key = OPENAI_API_KEY

# 初始化對話歷史
conversation_history = [
    {"role": "system", "content": "你是一位智慧型家教，專門為國高中生提供學科輔導。"}
]

# 計算 token 數量的函式
def num_tokens_from_messages(messages):
    return sum(len(msg["content"]) for msg in messages)

# 總結對話歷史的函式
def summarize_history():
    try:
        summary_prompt = "請總結以下對話，保留主要信息：" + json.dumps(conversation_history[:-5], ensure_ascii=False)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        summary = response["choices"][0]["message"]["content"]
        return [{"role": "system", "content": "總結對話：" + summary}]
    except Exception:
        return conversation_history[:1]  # 若總結失敗，保留 system 訊息

def ask_tutor(question):
    """ 發送問題給 OpenAI 並獲取回答，並記憶對話內容 """
    try:
        # 新增使用者的輸入到對話歷史
        conversation_history.append({"role": "user", "content": question})

        # 限制 token 總量（假設最大 token 限制為 4000）
        while num_tokens_from_messages(conversation_history) > 3500:
            conversation_history[:] = summarize_history() + conversation_history[-5:]

        # 呼叫 OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        )

        # 取得 AI 回應
        answer = response["choices"][0]["message"]["content"]

        # 將 AI 回應加入對話歷史
        conversation_history.append({"role": "assistant", "content": answer})

        return answer
    except Exception as e:
        return f"發生錯誤：{e}"

def main():
    """ 主迴圈，允許使用者不斷輸入問題 """
    print("📚 智慧家教已啟動，輸入你的問題吧！（輸入 'exit' 退出）")
    while True:
        try:
            user_input = input("\n你：")
            if user_input.lower() in ["exit", "退出"]:
                print("📚 結束對話，期待下次見面！")
                break
            answer = ask_tutor(user_input)
            print(f"\n🧠 AI 家教：{answer}")
        except KeyboardInterrupt:
            print("\n📚 結束對話，期待下次見面！")
            break

if __name__ == "__main__":
    main()
