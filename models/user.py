from datetime import datetime

class User:
    """用户模型"""
    
    def __init__(self, user_id, openid, session_key, nickname, avatar_url, 
                 member_level='普通用户', health_goal='', last_login_time=None, 
                 created_at=None, updated_at=None, id=None):
        self.id = id
        self.user_id = user_id
        self.openid = openid
        self.session_key = session_key
        self.nickname = nickname
        self.avatar_url = avatar_url
        self.member_level = member_level
        self.health_goal = health_goal
        self.last_login_time = last_login_time
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建用户对象"""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            openid=data.get('openid'),
            session_key=data.get('session_key'),
            nickname=data.get('nickname'),
            avatar_url=data.get('avatar_url'),
            member_level=data.get('member_level'),
            health_goal=data.get('health_goal'),
            last_login_time=data.get('last_login_time'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'openid': self.openid,
            'session_key': self.session_key,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'member_level': self.member_level,
            'health_goal': self.health_goal,
            'last_login_time': self.last_login_time,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def to_response_dict(self, include_sensitive=False):
        """转换为响应字典（排除敏感信息）"""
        result = {
            'userId': self.user_id,
            'nickname': self.nickname,
            'avatarUrl': self.avatar_url,
            'memberLevel': self.member_level or '普通用户',
            'healthGoal': self.health_goal or '',
            'lastLoginTime': self.last_login_time or '',
            'createdAt': self.created_at or ''
        }
        
        if include_sensitive:
            result.update({
                'openid': self.openid,
                'sessionKey': self.session_key
            })
            
        return result 