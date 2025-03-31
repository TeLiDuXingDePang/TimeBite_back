import requests
from flask import current_app

def get_openid_and_session_key(code):
    """
    调用微信API获取openid和session_key
    
    Args:
        code: 微信登录临时授权码
        
    Returns:
        tuple: (openid, session_key)
    """
    appid = current_app.config['WECHAT_APPID']
    secret = current_app.config['WECHAT_SECRET']
    
    if not appid or not secret:
        current_app.logger.error("微信小程序配置缺失")
        raise ValueError("微信小程序配置缺失")
    
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'errcode' in data and data['errcode'] != 0:
            current_app.logger.error(f"微信API返回错误: {data}")
            return None, None
            
        return data.get('openid'), data.get('session_key')
    except Exception as e:
        current_app.logger.error(f"调用微信API失败: {str(e)}")
        raise 