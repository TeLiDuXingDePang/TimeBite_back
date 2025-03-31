from flask import current_app
from flask_jwt_extended import decode_token

def get_user_id_from_token(token):
    """
    从JWT令牌中提取用户ID
    
    Args:
        token: JWT令牌字符串，可能是带有Bearer前缀的形式
        
    Returns:
        str: 用户ID或None（如果提取失败）
    """
    try:
        # 如果令牌有Bearer前缀，去掉前缀
        if token.startswith('Bearer '):
            token = token[7:]
            
        # 解码令牌
        decoded_token = decode_token(token)
        
        # 从令牌中获取身份信息（用户ID）
        user_id = decoded_token.get('sub')
        
        current_app.logger.debug(f"从令牌中提取的用户ID: {user_id}")
        return user_id
        
    except Exception as e:
        current_app.logger.error(f"从令牌中提取用户ID失败: {str(e)}")
        return None 