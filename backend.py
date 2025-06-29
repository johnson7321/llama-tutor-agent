from flask import Flask, jsonify, send_from_directory, request

app = Flask(__name__, static_folder='static')

@app.route('/api/data')
def get_data():
    return jsonify({"message": "Hello from backend"})

# ✅ 新增輸入輸出 API
@app.route('/api/echo', methods=['POST'])
def echo_input():
    data = request.json
    user_input = data.get("input", "")
    # 這裡可以加上你自己的處理邏輯，比如計算、查資料庫等
    output = f"You said: {user_input}"
    return jsonify({"output": output})

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
