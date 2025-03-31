from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.recipe_service import RecipeService
from repositories.recipe_repository import RecipeRepository
from services.recipe_detail_service import RecipeDetailService

class RecipeController:
    """菜谱控制器类"""
    
    def __init__(self, excel_db):
        """
        初始化菜谱控制器
        
        Args:
            excel_db: Excel数据库实例
        """
        # 初始化依赖组件
        recipe_repository = RecipeRepository(excel_db)
        self.recipe_service = RecipeService(recipe_repository)
        self.recipe_detail_service = RecipeDetailService(excel_db)
    
    def init_routes(self, blueprint):
        """
        初始化路由
        
        Args:
            blueprint: Flask蓝图实例
        """
        # 注册路由
        blueprint.route('', methods=['GET'])(self.get_all_recipes)
        blueprint.route('/<int:recipe_id>', methods=['GET'])(self.get_recipe_detail)
        blueprint.route('/<int:recipe_id>/detail', methods=['GET'])(self.get_recipe_detail_v2)
        blueprint.route('/<int:recipe_id>/detail/public', methods=['GET'])(self.get_recipe_detail_public)
    
    def get_all_recipes(self):
        """获取所有菜谱"""
        try:
            recipes = self.recipe_service.get_all_recipes()
            
            # 转换为响应格式
            recipe_list = [recipe.to_response_dict() for recipe in recipes]
            
            response = {
                'code': 0,
                'message': 'success',
                'data': {
                    'recipes': recipe_list
                }
            }
            
            return jsonify(response)
        except Exception as e:
            current_app.logger.error(f"获取菜谱列表异常: {str(e)}")
            return jsonify({
                'code': 2001,
                'message': '服务器内部错误',
                'data': None
            }), 500
    
    def get_recipe_detail(self, recipe_id):
        """获取菜谱基本详情"""
        try:
            recipe = self.recipe_service.get_recipe_by_id(recipe_id)
            
            response = {
                'code': 0,
                'message': 'success',
                'data': {
                    'recipe': recipe.to_response_dict()
                }
            }
            
            return jsonify(response)
        except ValueError as e:
            return jsonify({
                'code': 1004,
                'message': str(e),
                'data': None
            }), 404
        except Exception as e:
            current_app.logger.error(f"获取菜谱详情异常: {str(e)}")
            return jsonify({
                'code': 2001,
                'message': '服务器内部错误',
                'data': None
            }), 500
            
    @jwt_required()
    def get_recipe_detail_v2(self, recipe_id):
        """获取菜谱完整详情，包含食材、工具、步骤等信息（包含用户食材库存状态）"""
        try:
            current_app.logger.info(f"请求菜谱ID: {recipe_id} 的详情(带用户库存)")
            
            # 从JWT中获取用户身份标识
            jwt_user_id = get_jwt_identity()
            if jwt_user_id:
                current_app.logger.info(f"当前用户JWT标识: {jwt_user_id}，将检查食材库存状态")
            else:
                current_app.logger.warning("未获取到有效的用户JWT标识，不检查库存状态")
            
            # 获取菜谱详情，传入JWT用户ID
            recipe = self.recipe_detail_service.get_recipe_detail(recipe_id, jwt_user_id)
            
            if recipe is None:
                current_app.logger.warning(f"未找到ID为 {recipe_id} 的菜谱")
                return jsonify({
                    'code': 404,
                    'message': f"未找到ID为 {recipe_id} 的菜谱",
                    'data': None
                }), 404
            
            current_app.logger.info(f"成功获取菜谱 '{recipe.name}' 的详情")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取菜谱详情成功',
                'data': recipe.to_response_dict()
            })
            
        except Exception as e:
            current_app.logger.error(f"获取菜谱详情失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取菜谱详情失败: {str(e)}",
                'data': None
            }), 500
            
    def get_recipe_detail_public(self, recipe_id):
        """获取菜谱完整详情，不包含用户食材库存状态（无需JWT认证）"""
        try:
            current_app.logger.info(f"公开请求菜谱ID: {recipe_id} 的详情")
            
            # 获取菜谱详情，不传入JWT用户ID
            recipe = self.recipe_detail_service.get_recipe_detail(recipe_id)
            
            if recipe is None:
                current_app.logger.warning(f"未找到ID为 {recipe_id} 的菜谱")
                return jsonify({
                    'code': 404,
                    'message': f"未找到ID为 {recipe_id} 的菜谱",
                    'data': None
                }), 404
            
            current_app.logger.info(f"成功获取菜谱 '{recipe.name}' 的公开详情")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取菜谱详情成功',
                'data': recipe.to_response_dict()
            })
            
        except Exception as e:
            current_app.logger.error(f"获取菜谱详情失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取菜谱详情失败: {str(e)}",
                'data': None
            }), 500 