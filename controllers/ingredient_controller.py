from flask import jsonify, Blueprint, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.ingredient_service import IngredientService
from datetime import datetime

class IngredientController:
    """食材控制器"""
    
    def __init__(self, excel_db):
        self.ingredient_service = IngredientService(excel_db)
        
    def init_routes(self, blueprint):
        """初始化路由"""
        blueprint.route('/stats', methods=['GET'])(self.get_ingredient_stats)
        blueprint.route('/most-expiring', methods=['GET'])(self.get_most_expiring_ingredient)
        blueprint.route('/top-expiring', methods=['GET'])(self.get_top_expiring_ingredients)
        blueprint.route('/all', methods=['GET'])(self.get_all_ingredients)
        blueprint.route('/<int:ingredient_id>', methods=['DELETE'])(self.delete_ingredient)
        blueprint.route('/<int:ingredient_id>', methods=['PUT'])(self.update_ingredient)
        
    @jwt_required()
    def get_ingredient_stats(self):
        """获取用户食材库存统计"""
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求食材库存统计")
            
            # 获取食材库存统计
            stats = self.ingredient_service.get_ingredient_stats(jwt_identity)
            
            # 日志输出统计结果
            current_app.logger.info(f"用户 {jwt_identity} 的食材统计: 新鲜食材 {stats['fresh_count']} 种, 临期食材 {stats['expiring_count']} 种, 过期食材 {stats['expired_count']} 种")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取食材库存统计成功',
                'data': {
                    'fresh_count': stats['fresh_count'],
                    'expiring_count': stats['expiring_count'],
                    'expired_count': stats['expired_count'],
                    'total_count': stats['fresh_count'] + stats['expiring_count'] + stats['expired_count']
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取食材库存统计失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取食材库存统计失败: {str(e)}",
                'data': None
            }), 500
            
    @jwt_required()
    def get_most_expiring_ingredient(self):
        """获取用户最快过期的食材"""
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求最快过期的食材信息")
            
            # 获取最快过期的食材
            ingredient = self.ingredient_service.get_most_expiring_ingredient(jwt_identity)
            
            # 如果没有找到食材
            if ingredient is None:
                current_app.logger.warning(f"用户 {jwt_identity} 没有设置过期日期的食材")
                return jsonify({
                    'code': 404,
                    'message': '未找到设置过期日期的食材',
                    'data': None
                }), 404
            
            # 日志输出找到的食材
            current_app.logger.info(f"用户 {jwt_identity} 最快过期的食材: {ingredient['name']}, 还有 {ingredient['days_until_expiry']} 天过期")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取最快过期食材成功',
                'data': {
                    'name': ingredient['name'],
                    'quantity': ingredient['quantity'],
                    'unit': ingredient['unit'],
                    'days_until_expiry': ingredient['days_until_expiry'],
                    'expiry_date': ingredient['expiry_date']
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取最快过期食材失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取最快过期食材失败: {str(e)}",
                'data': None
            }), 500
            
    @jwt_required()
    def get_top_expiring_ingredients(self):
        """获取用户最快过期的最多5个食材"""
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求最快过期的多个食材信息")
            
            # 获取最快过期的最多5个食材
            ingredients = self.ingredient_service.get_top_expiring_ingredients(jwt_identity)
            
            # 如果没有找到食材
            if not ingredients:
                current_app.logger.warning(f"用户 {jwt_identity} 没有设置过期日期的食材")
                return jsonify({
                    'code': 404,
                    'message': '未找到设置过期日期的食材',
                    'data': None
                }), 404
            
            # 日志输出找到的食材数量
            current_app.logger.info(f"用户 {jwt_identity} 找到 {len(ingredients)} 个最快过期的食材")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取最快过期食材列表成功',
                'data': {
                    'ingredients': ingredients,
                    'total': len(ingredients)
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取最快过期食材列表失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取最快过期食材列表失败: {str(e)}",
                'data': None
            }), 500
            
    @jwt_required()
    def get_all_ingredients(self):
        """获取用户的所有食材"""
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求所有食材信息")
            
            # 获取所有食材
            ingredients = self.ingredient_service.get_all_ingredients(jwt_identity)
            
            # 如果没有找到食材
            if not ingredients:
                current_app.logger.warning(f"用户 {jwt_identity} 没有任何食材")
                return jsonify({
                    'code': 404,
                    'message': '未找到任何食材',
                    'data': None
                }), 404
            
            # 日志输出找到的食材数量
            current_app.logger.info(f"用户 {jwt_identity} 共有 {len(ingredients)} 种食材")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取食材列表成功',
                'data': {
                    'ingredients': ingredients,
                    'total': len(ingredients)
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取食材列表失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取食材列表失败: {str(e)}",
                'data': None
            }), 500
            
    @jwt_required()
    def delete_ingredient(self, ingredient_id):
        """删除用户的指定食材"""
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求删除食材(ID: {ingredient_id})")
            
            # 删除食材
            result = self.ingredient_service.delete_ingredient(jwt_identity, ingredient_id)
            
            # 如果删除失败
            if not result:
                current_app.logger.warning(f"用户 {jwt_identity} 删除食材(ID: {ingredient_id})失败")
                return jsonify({
                    'code': 404,
                    'message': f'删除失败，未找到ID为{ingredient_id}的食材或没有权限删除',
                    'data': None
                }), 404
            
            # 删除成功
            current_app.logger.info(f"用户 {jwt_identity} 成功删除食材(ID: {ingredient_id})")
            return jsonify({
                'code': 200,
                'message': '食材删除成功',
                'data': {
                    'ingredient_id': ingredient_id
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"删除食材时出错: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"删除食材失败: {str(e)}",
                'data': None
            }), 500
            
    @jwt_required()
    def update_ingredient(self, ingredient_id):
        """更新用户的指定食材信息"""
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求更新食材(ID: {ingredient_id})信息")
            
            # 获取请求体数据
            data = request.get_json()
            if not data:
                current_app.logger.warning("请求体为空或不是有效的JSON")
                return jsonify({
                    'code': 400,
                    'message': '请求体为空或不是有效的JSON',
                    'data': None
                }), 400
            
            # 提取需要更新的字段
            quantity = data.get('quantity')
            expiry_date = data.get('expiry_date')
            
            # 检查是否至少有一个需要更新的字段
            if quantity is None and expiry_date is None:
                current_app.logger.warning("没有提供需要更新的字段")
                return jsonify({
                    'code': 400,
                    'message': '请至少提供一个需要更新的字段(quantity或expiry_date)',
                    'data': None
                }), 400
            
            # 验证数量是否合法
            if quantity is not None and not isinstance(quantity, (int, float)) or (isinstance(quantity, (int, float)) and quantity <= 0):
                current_app.logger.warning(f"提供的食材数量不合法: {quantity}")
                return jsonify({
                    'code': 400,
                    'message': '食材数量必须是正数',
                    'data': None
                }), 400
            
            # 验证日期格式是否合法
            if expiry_date is not None:
                try:
                    # 尝试解析日期格式
                    datetime.strptime(expiry_date, '%Y-%m-%d')
                except ValueError:
                    current_app.logger.warning(f"提供的日期格式不合法: {expiry_date}")
                    return jsonify({
                        'code': 400,
                        'message': '日期格式必须为YYYY-MM-DD',
                        'data': None
                    }), 400
            
            # 更新食材信息
            result = self.ingredient_service.update_ingredient(jwt_identity, ingredient_id, quantity, expiry_date)
            
            # 如果更新失败
            if result is None:
                current_app.logger.warning(f"用户 {jwt_identity} 更新食材(ID: {ingredient_id})失败")
                return jsonify({
                    'code': 404,
                    'message': f'更新失败，未找到ID为{ingredient_id}的食材或没有权限更新',
                    'data': None
                }), 404
            
            # 更新成功
            current_app.logger.info(f"用户 {jwt_identity} 成功更新食材(ID: {ingredient_id})信息")
            return jsonify({
                'code': 200,
                'message': '食材信息更新成功',
                'data': result
            })
            
        except Exception as e:
            current_app.logger.error(f"更新食材信息时出错: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"更新食材信息失败: {str(e)}",
                'data': None
            }), 500 