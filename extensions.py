from flask_jwt_extended import JWTManager
from utils.excel_db import ExcelDatabase

# 初始化扩展
jwt = JWTManager()
excel_db = None  # 将在应用初始化时设置

def init_excel_db(app):
    """初始化Excel数据库"""
    global excel_db
    excel_db = ExcelDatabase(app.config['EXCEL_DB_PATH'])
    return excel_db 