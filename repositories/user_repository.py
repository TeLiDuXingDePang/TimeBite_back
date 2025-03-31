import uuid
import pandas as pd
from datetime import datetime
from models.user import User

class UserRepository:
    """用户数据访问类"""
    
    def __init__(self, excel_db):
        self.excel_db = excel_db
    
    def find_by_openid(self, openid):
        """根据openid查找用户"""
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            return None
            
        user = users_df[users_df['openid'] == openid]
        if user.empty:
            return None
            
        return User.from_dict(user.iloc[0].to_dict())
    
    def find_by_user_id(self, user_id):
        """根据user_id查找用户"""
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            return None
        
        user_row = users_df[users_df['user_id'] == user_id]
        if user_row.empty:
            return None
        
        return User.from_dict(user_row.iloc[0].to_dict())
    
    def create(self, user):
        """创建新用户"""
        users_df = self.excel_db.read_table('users')
        
        # 准备用户数据
        user_dict = user.to_dict()
        
        # 生成ID
        if users_df.empty:
            new_id = 1
        else:
            new_id = users_df['id'].max() + 1
        
        user_dict['id'] = new_id
        
        # 添加时间戳
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not user_dict.get('created_at'):
            user_dict['created_at'] = now
        if not user_dict.get('updated_at'):
            user_dict['updated_at'] = now
        
        # 添加到DataFrame
        new_row = pd.DataFrame([user_dict])
        users_df = pd.concat([users_df, new_row], ignore_index=True)
        
        # 保存到Excel
        self.excel_db.write_table('users', users_df)
        
        return User.from_dict(user_dict)
    
    def update(self, openid, update_data):
        """更新用户信息"""
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            return None
        
        # 查找用户
        user_idx = users_df[users_df['openid'] == openid].index
        if len(user_idx) == 0:
            return None
        
        # 更新时间戳
        update_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新用户数据
        for key, value in update_data.items():
            users_df.loc[user_idx[0], key] = value
        
        # 保存到Excel
        self.excel_db.write_table('users', users_df)
        
        # 返回更新后的用户信息
        return User.from_dict(users_df.loc[user_idx[0]].to_dict()) 