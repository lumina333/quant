import os
import mysql.connector
import time
import socket
from mysql.connector import Error

def get_mysql_connection():
    """读取环境变量并连接 MySQL 数据库"""
    try:
        host = os.getenv("MYSQL_HOST", "quant_mysql")  
        port = int(os.getenv("MYSQL_PORT", 3306))    
        user = os.getenv("MYSQL_USER", "root")
        password = os.getenv("MYSQL_PASSWORD", "root")
        database = os.getenv("MYSQL_DB", None)       # 查看所有数据库时无需指定数据库
     
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

        if connection.is_connected():
            print("成功连接到 MySQL 服务！")
            return connection

    except Error as e:
        print(f"连接 MySQL 失败: {e}")
        return None

def list_all_databases(connection):
    """执行 SHOW DATABASES 命令并打印结果"""
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES;")
        databases = cursor.fetchall()

        print("\n所有数据库列表：")
        for db in databases:
            print(f"- {db[0]}")  # 结果是元组，取第一个元素（数据库名）

    except Error as e:
        print(f"查询数据库失败: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()

if __name__ == "__main__":
    # 等mysql起来
    time.sleep(20)
    mysql_conn = get_mysql_connection()
    
    if mysql_conn:
        # 列出所有数据库
        list_all_databases(mysql_conn)
        
        # 关闭连接
        if mysql_conn.is_connected():
            mysql_conn.close()
            print("\n数据库连接已关闭。")