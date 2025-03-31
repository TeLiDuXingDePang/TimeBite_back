import uuid
import pandas as pd
from datetime import datetime
from models.user import User
from utils.wechat_api import get_openid_and_session_key
from utils.image_utils import save_base64_image, process_avatar_file

class UserService:
    """用户服务类"""
    
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def login(self, nickname, avatar_data, code, login_time, is_base64=True):
        """
        用户登录/注册
        
        Args:
            nickname: 用户昵称
            avatar_data: 头像数据（Base64字符串或文件对象）
            code: 微信登录临时授权码
            login_time: 登录时间戳（毫秒）
            is_base64: 是否为Base64头像
            
        Returns:
            tuple: (user, token, is_new_user)
        """
        # 处理头像
        if is_base64:
            avatar_url = save_base64_image(avatar_data)
        else:
            avatar_url = process_avatar_file(avatar_data)
        
        # 获取openid和session_key
        openid, session_key = get_openid_and_session_key(code)
        if not openid:
            raise ValueError("微信授权码无效或已过期")
        
        # 查找用户
        user = self.user_repository.find_by_openid(openid)
        is_new_user = False
        
        if user:
            # 更新现有用户
            login_datetime = datetime.fromtimestamp(int(login_time)/1000).strftime('%Y-%m-%d %H:%M:%S')
            user = self.user_repository.update(openid, {
                'nickname': nickname,
                'avatar_url': avatar_url,
                'last_login_time': login_datetime
            })
        else:
            # 创建新用户
            is_new_user = True
            user = User(
                user_id=f"u_{uuid.uuid4().hex[:8]}",
                openid=openid,
                session_key=session_key,
                nickname=nickname,
                avatar_url=avatar_url,
                member_level='普通用户',
                health_goal='',
                last_login_time=datetime.fromtimestamp(int(login_time)/1000).strftime('%Y-%m-%d %H:%M:%S')
            )
            user = self.user_repository.create(user)
        
        return user, is_new_user
    
    def update_user_info(self, user_id, nickname=None, health_goal=None, avatar_data=None, is_base64=True):
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            nickname: 新昵称（可选）
            health_goal: 新健康目标（可选）
            avatar_data: 新头像数据（可选，Base64字符串或文件对象）
            is_base64: 是否为Base64头像
            
        Returns:
            User: 更新后的用户对象
        """
        # 查找用户
        user = self.user_repository.find_by_user_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 准备更新数据
        update_data = {}
        
        if nickname:
            update_data['nickname'] = nickname
        
        if health_goal is not None:  # 允许设置为空字符串
            update_data['health_goal'] = health_goal
        
        if avatar_data:
            if is_base64:
                avatar_url = save_base64_image(avatar_data)
            else:
                avatar_url = process_avatar_file(avatar_data)
            update_data['avatar_url'] = avatar_url
        
        # 如果没有要更新的数据
        if not update_data:
            raise ValueError("没有提供要更新的数据")
        
        # 更新用户
        updated_user = self.user_repository.update(user.openid, update_data)
        if not updated_user:
            raise ValueError("更新用户信息失败")
        
        return updated_user
    
    def get_user_info(self, user_id):
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            User: 用户对象
        """
        user = self.user_repository.find_by_user_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        return user 