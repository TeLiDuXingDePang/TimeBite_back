import os
import time
import base64
import uuid
import re
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from utils.wechat_api import get_openid_and_session_key
from utils.image_utils import save_base64_image, process_avatar_file
from controllers.user_controller import UserController
from services.user_service import UserService
from repositories.user_repository import UserRepository

def create_user_blueprint(excel_db):
    """创建用户蓝图并传入excel_db实例"""
    user_bp = Blueprint('user', __name__)
    
    # 初始化依赖
    user_repository = UserRepository(excel_db)
    user_service = UserService(user_repository)
    user_controller = UserController(user_service)
    
    # 注册路由
    user_bp.route('/login', methods=['POST'])(user_controller.login)
    user_bp.route('/update', methods=['POST'])(user_controller.update_user_info)
    user_bp.route('/info', methods=['GET'])(user_controller.get_user_info)
    
    return user_bp 