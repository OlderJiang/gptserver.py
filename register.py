import pymysql

def check_existing_user(username):
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='sys',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM userinfo WHERE Username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            if result:
                return True  # 用户名已存在
            else:
                return False  # 用户名不存在
    finally:
        connection.close()

def register_user(username, password):
    if check_existing_user(username):
        return 'duplicate'  # 返回重复用户信息

    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='sys',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO userinfo (Username, Password) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
            connection.commit()
    finally:
        connection.close()
