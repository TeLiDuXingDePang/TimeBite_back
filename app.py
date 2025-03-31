from flask import Flask, send_from_directory
from config import config
from extensions import jwt
from utils.excel_db import ExcelDatabase
import os

# 创建全局excel_db对象
excel_db = None


def create_app(config_name='development'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 验证关键配置
    if not app.config.get('WECHAT_APPID') or not app.config.get('WECHAT_SECRET'):
        app.logger.warning('微信小程序配置缺失，可能导致登录功能无法正常使用')

    # 初始化配置
    config[config_name].init_app(app)

    # 初始化扩展
    jwt.init_app(app)

    # 初始化Excel数据库
    global excel_db
    excel_db = ExcelDatabase(app.config['EXCEL_DB_PATH'])

    # 导入路由模块并传递excel_db
    from routes import register_blueprints
    register_blueprints(app, excel_db)

    # 添加静态文件访问路由
    @app.route('/static/avatars/<filename>')
    def serve_avatar(filename):
        """提供头像文件访问"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/static/recipes/<filename>')
    def serve_recipe_image(filename):
        """提供菜谱图片访问"""
        return send_from_directory(app.config['RECIPES_FOLDER'], filename)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
