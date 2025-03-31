from flask import jsonify, Blueprint, current_app
from flask_jwt_extended import jwt_required
from services.recipe_detail_service import RecipeDetailService

class RecipeDetailController:
    """菜谱详情控制器"""
    
    def __init__(self, excel_db):
        self.recipe_detail_service = RecipeDetailService(excel_db)
        
    def init_routes(self, blueprint):
        """初始化路由"""
        blueprint.route('/<int:recipe_id>/detail', methods=['GET'])(self.get_recipe_detail)
        
    @jwt_required()
    def get_recipe_detail(self, recipe_id):
        """获取菜谱详情"""
        try:
            current_app.logger.info(f"请求菜谱ID: {recipe_id} 的详情")
            
            # 获取菜谱详情
            recipe = self.recipe_detail_service.get_recipe_detail(recipe_id)
            
            if recipe is None:
                current_app.logger.warning(f"未找到ID为 {recipe_id} 的菜谱")
                return jsonify({
                    'code': 404,
                    'message': f"未找到ID为 {recipe_id} 的菜谱",
                    'data': None
                }), 404
            
            # 记录详细信息到日志
            current_app.logger.info(f"成功获取菜谱 '{recipe.name}' 的详情")
            current_app.logger.info(f"菜谱包含 {len(recipe.ingredients)} 种食材")
            current_app.logger.info(f"菜谱包含 {len(recipe.tools)} 种工具")
            current_app.logger.info(f"菜谱包含 {len(recipe.prep_steps)} 个预处理步骤")
            current_app.logger.info(f"菜谱包含 {len(recipe.steps)} 个烹饪步骤")
            current_app.logger.info(f"菜谱{'包含' if recipe.tips else '不包含'}小贴士")
            current_app.logger.info(f"菜谱标签: {recipe.tags}")
            
            # 获取响应数据
            response_data = recipe.to_response_dict()
            
            # 确保返回数据包含所有必要字段
            required_fields = ['tools', 'prep_steps', 'tips']
            for field in required_fields:
                if field not in response_data:
                    current_app.logger.warning(f"响应数据中缺少 {field} 字段")
                else:
                    current_app.logger.info(f"响应数据包含 {field} 字段")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取菜谱详情成功',
                'data': response_data
            })
            
        except Exception as e:
            current_app.logger.error(f"获取菜谱详情失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取菜谱详情失败: {str(e)}",
                'data': None
            }), 500 