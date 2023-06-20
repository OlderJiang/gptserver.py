import random

from flask import Flask, render_template, jsonify, request, redirect, url_for
import pymysql
import openai
from register import register_user
import time
import threading

# 用户最后活动时间的字典，存储用户的最后活动时间戳
user_last_activity = {}

# 登出时限（秒）
logout_timeout = 1000

app = Flask(__name__, static_folder='static')

api_keys = ['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',
            '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',
            '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',
            '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',
            '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',
            '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',
            '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',
            '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',
            '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',
            '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',
            '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',
            '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',
            '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']

api_keys_backup = ['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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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',
                   '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']

model_name = "gpt-3.5-turbo-0613"

chat_histories = [[] for _ in range(len(api_keys))]
# 用于跟踪已分配的密钥和用户名的字典
user_key_mapping = {}


def connect_to_database():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='sys',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


def user_login(username, password):
    connection = connect_to_database()
    # 更新用户的最后活动时间
    user_last_activity[username] = time.time()

    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM userinfo WHERE Username = %s AND Password = %s"
            cursor.execute(sql, (username, password))
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False
    finally:
        connection.close()


@app.route('/')
def index():
    return app.send_static_file('rein.html')


@app.route('/register')
def register():
    return app.send_static_file('register.html')


@app.route('/register', methods=['POST'])
def handle_registration():
    data = request.form
    username = data.get('username', '')
    password = data.get('password', '')

    result = register_user(username, password)  # 调用 register.py 中的注册方法

    if result == 'duplicate':
        error_msg = "用户名已存在，请选择其他用户名"  # 设置错误消息
        return render_template('register.html', error=error_msg)  # 将错误消息传递给模板
    else:
        return app.send_static_file('rein.html')


@app.route('/index/<username>')
def user_index(username):
    # 确保只有已登录的用户能够访问该页面
    if username in user_key_mapping:
        return render_template('index.html', username=username)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data.get('username', '')
    password = data.get('password', '')

    # 更新用户的最后活动时间
    user_last_activity[username] = time.time()

    if user_login(username, password):
        # 检查用户是否已经登录
        if username in user_key_mapping:
            return "User already logged in."

        # 分配一个可用的 API 密钥给用户
        if len(api_keys) > 0:
            # 从可用的 API 密钥集合中随机选择一个
            key = random.choice(api_keys)
            # 将用户与密钥进行绑定
            user_key_mapping[username] = key
            # 从可用的 API 密钥集合中移除已分配的密钥
            api_keys.remove(key)
            print("当前api_keys集合长度：", len(api_keys))
            print("当前绑定的用户名和密钥：", username, key)

            return redirect(url_for('user_index', username=username))

        else:
            return "No available API keys."
    else:
        error_msg = "用户名或密码错误"  # 设置错误消息
        return render_template('rein.html', error=error_msg)  # 将错误消息传递给模板


@app.route('/logout', methods=['POST'])
def logout():
    username = request.form['username']
    # 删除用户的最后活动时间记录
    if username in user_last_activity:
        del user_last_activity[username]

    # 检查用户是否已登录
    if username in user_key_mapping:
        # 将用户的密钥释放回集合
        api_keys.append(user_key_mapping[username])
        # 删除用户与密钥的映射关系
        print(username, "成功登出")
        print("当前api_keys集合长度：", len(api_keys))
        del user_key_mapping[username]
        return "成功登出."
    else:
        return "User not logged in."


@app.route('/get_response', methods=['POST'])
def get_response():
    data = request.get_json()
    user_input = data.get('user_input', '')
    username = data.get('username', '')

    # 更新用户的最后活动时间
    user_last_activity[username] = time.time()

    print(username)

    # 检查用户是否已登录
    if username in user_key_mapping:
        api_key = user_key_mapping[username]
        openai.api_key = api_key
        print(openai.api_key)

        api_key_index = api_keys_backup.index(api_key)
        chat_history = chat_histories[api_key_index]
        recent_chat_history = chat_history[-5:]

        input_text = '\n'.join(recent_chat_history + [user_input])

        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system",
                 "content": "我是 ChatGPT，一款强大的语言模型助手。我可以回答你的问题、提供帮助和交流。请告诉我你需要什么帮助。"},
                {"role": "user", "content": input_text}
            ],
            temperature=0.5,
            max_tokens=2300
        )

        chat_response = response.choices[0].message.content.strip()

        chat_history.append(user_input)
        chat_history.append(chat_response)

        return jsonify({'chat_response': chat_response})
    else:
        return "User not logged in."


# 定时检查用户的最后活动时间并执行登出操作
def check_logout_timeout():
    while True:
        # 获取当前时间戳
        current_time = time.time()

        # 遍历用户的最后活动时间字典
        for username, last_activity in user_last_activity.items():
            # 计算用户的活动时间间隔
            activity_duration = current_time - last_activity

            # 如果超过登出时限，执行登出操作
            if activity_duration > logout_timeout:
                logout_user(username)

        # 检查用户是否已登录
        if user_key_mapping:
            # 每秒检查一次
            time.sleep(5)
        else:
            # 用户未登录时，延迟一段时间后再次检查
            time.sleep(20)


def logout_user(username):
    # 检查用户是否已登录
    if username in user_key_mapping:
        # 将用户的密钥释放回集合
        api_keys.append(user_key_mapping[username])
        # 删除用户与密钥的映射关系
        print(username, "用户超时，自动登出")
        print("当前api_keys集合长度：", len(api_keys))
        del user_key_mapping[username]
    else:
        pass


# 启动一个线程来执行检查登出时限的操作
logout_thread = threading.Thread(target=check_logout_timeout)
logout_thread.start()

if __name__ == '__main__':
    app.run(debug=False)
