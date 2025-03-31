import pandas as pd
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

class UserController:
    """用户控制器类"""
    
    def __init__(self, user_service):
        self.user_service = user_service
    
    def login(self):
        """用户登录/注册接口"""
        try:
            # 判断请求类型
            if request.content_type and 'multipart/form-data' in request.content_type:
                # FormData方式
                nickname = request.form.get('nickname')
                code = request.form.get('code')
                login_time = request.form.get('loginTime')
                avatar_file = request.files.get('avatarFile')
                
                if not all([nickname, code, login_time, avatar_file]):
                    return jsonify({
                        'code': 1003,
                        'message': '缺少必要参数',
                        'data': None
                    }), 400
                
                # 调用服务层处理登录
                try:
                    user, is_new_user = self.user_service.login(
                        nickname=nickname,
                        avatar_data=avatar_file,
                        code=code,
                        login_time=login_time,
                        is_base64=False
                    )
                except ValueError as e:
                    return jsonify({
                        'code': 1001,
                        'message': str(e),
                        'data': None
                    }), 400
                except Exception as e:
                    current_app.logger.error(f"登录处理失败: {str(e)}")
                    return jsonify({
                        'code': 1002,
                        'message': '用户信息处理失败',
                        'data': None
                    }), 500
                
            else:
                # JSON方式
                data = request.get_json()
                if not data:
                    return jsonify({
                        'code': 1003,
                        'message': '无效的请求数据',
                        'data': None
                    }), 400
                
                nickname = data.get('nickname')
                avatar_url_base64 = data.get('avatarUrl')
                code = data.get('code')
                login_time = data.get('loginTime')
                
                if not all([nickname, avatar_url_base64, code, login_time]):
                    return jsonify({
                        'code': 1003,
                        'message': '缺少必要参数',
                        'data': None
                    }), 400
                
                # 调用服务层处理登录
                try:
                    user, is_new_user = self.user_service.login(
                        nickname=nickname,
                        avatar_data=avatar_url_base64,
                        code=code,
                        login_time=login_time,
                        is_base64=True
                    )
                except ValueError as e:
                    return jsonify({
                        'code': 1001,
                        'message': str(e),
                        'data': None
                    }), 400
                except Exception as e:
                    current_app.logger.error(f"登录处理失败: {str(e)}")
                    return jsonify({
                        'code': 1002,
                        'message': '用户信息处理失败',
                        'data': None
                    }), 500
            
            # 生成JWT令牌
            token = create_access_token(identity=user.user_id)
            
            # 构建响应数据
            response_data = {
                'userId': user.user_id,
                'token': token,
                'expiresIn': 30 * 24 * 60 * 60,  # 30天有效期（秒）
                'userInfo': {
                    'nickname': user.nickname,
                    'avatarUrl': user.avatar_url,
                    'isNewUser': is_new_user,
                    'memberLevel': user.member_level or '普通用户',
                    'healthGoal': user.health_goal if pd.notna(user.health_goal) else ''
                }
            }
            
            response = {
                'code': 0,
                'message': 'success',
                'data': response_data
            }
            current_app.logger.debug(f"发送响应: {response}")
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"登录接口异常: {str(e)}")
            return jsonify({
                'code': 2001,
                'message': '服务器内部错误',
                'data': None
            }), 500
    
    @jwt_required()
    def update_user_info(self):
        """用户信息更新接口"""
        try:
            # 获取当前用户ID
            current_user_id = get_jwt_identity()
            
            # 判断请求类型
            if request.content_type and 'multipart/form-data' in request.content_type:
                # FormData方式
                nickname = request.form.get('nickname')
                health_goal = request.form.get('healthGoal')
                avatar_file = request.files.get('avatarFile')
                
                # 调用服务层更新用户信息
                try:
                    updated_user = self.user_service.update_user_info(
                        user_id=current_user_id,
                        nickname=nickname,
                        health_goal=health_goal,
                        avatar_data=avatar_file if avatar_file else None,
                        is_base64=False
                    )
                except ValueError as e:
                    return jsonify({
                        'code': 1003,
                        'message': str(e),
                        'data': None
                    }), 400
                except Exception as e:
                    current_app.logger.error(f"更新用户信息失败: {str(e)}")
                    return jsonify({
                        'code': 2002,
                        'message': '更新用户信息失败',
                        'data': None
                    }), 500
                
            else:
                # JSON方式
                data = request.get_json()
                if not data:
                    return jsonify({
                        'code': 1003,
                        'message': '无效的请求数据',
                        'data': None
                    }), 400
                
                nickname = data.get('nickname')
                health_goal = data.get('healthGoal')
                avatar_url_base64 = data.get('avatarUrl')
                
                # 调用服务层更新用户信息
                try:
                    updated_user = self.user_service.update_user_info(
                        user_id=current_user_id,
                        nickname=nickname,
                        health_goal=health_goal,
                        avatar_data=avatar_url_base64 if avatar_url_base64 and avatar_url_base64.startswith('data:image') else None,
                        is_base64=True
                    )
                except ValueError as e:
                    return jsonify({
                        'code': 1003,
                        'message': str(e),
                        'data': None
                    }), 400
                except Exception as e:
                    current_app.logger.error(f"更新用户信息失败: {str(e)}")
                    return jsonify({
                        'code': 2002,
                        'message': '更新用户信息失败',
                        'data': None
                    }), 500
            
            # 构建响应数据
            response_data = {
                'userInfo': updated_user.to_response_dict()
            }
            
            response = {
                'code': 0,
                'message': 'success',
                'data': response_data
            }
            current_app.logger.debug(f"发送响应: {response}")
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"更新用户信息接口异常: {str(e)}")
            return jsonify({
                'code': 2001,
                'message': '服务器内部错误',
                'data': None
            }), 500
    
    @jwt_required()
    def get_user_info(self):
        """获取用户信息接口"""
        try:
            # 获取当前用户ID
            current_user_id = get_jwt_identity()
            
            # 调用服务层获取用户信息
            try:
                user = self.user_service.get_user_info(current_user_id)
            except ValueError as e:
                return jsonify({
                    'code': 1002,
                    'message': str(e),
                    'data': None
                }), 404
            except Exception as e:
                current_app.logger.error(f"获取用户信息失败: {str(e)}")
                return jsonify({
                    'code': 2002,
                    'message': '获取用户信息失败',
                    'data': None
                }), 500
            
            # 构建响应数据
            response_data = {
                'userInfo': user.to_response_dict()
            }
            
            response = {
                'code': 0,
                'message': 'success',
                'data': response_data
            }
            current_app.logger.debug(f"发送响应: {response}")
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"获取用户信息接口异常: {str(e)}")
            return jsonify({
                'code': 2001,
                'message': '服务器内部错误',
                'data': None
            }), 500 