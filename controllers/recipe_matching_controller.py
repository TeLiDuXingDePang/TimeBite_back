from flask import request, jsonify, current_app
from services.recipe_matching_service import RecipeMatchingService

class RecipeMatchingController:
    """基于过期食材匹配菜谱的控制器"""
    
    def __init__(self, excel_db):
        """
        初始化控制器
        
        Args:
            excel_db: Excel数据库实例
        """
        self.excel_db = excel_db
        self.recipe_matching_service = RecipeMatchingService(excel_db)
    
    def init_routes(self, blueprint):
        """
        初始化路由
        
        Args:
            blueprint: Flask蓝图实例
        """
        blueprint.route('/match-expiring', methods=['GET'])(self.match_recipes_by_expiring_ingredients)
    
    def match_recipes_by_expiring_ingredients(self):
        """处理基于过期食材匹配菜谱的请求"""
        try:
            token = request.headers.get('Authorization', '')
            if not token:
                current_app.logger.warning("请求中缺少Authorization令牌")
                return jsonify({
                    "code": 401,
                    "message": "未授权的请求",
                    "data": None
                }), 401
            
            # 从查询参数获取可选配置
            top_n = request.args.get('top_n', default=5, type=int)
            recipe_count = request.args.get('count', default=3, type=int)
            
            # 验证参数范围
            if top_n < 1 or top_n > 10:
                top_n = 5  # 默认最多考虑5种食材
            if recipe_count < 1 or recipe_count > 10:
                recipe_count = 3  # 默认返回3个菜谱
            
            current_app.logger.info(f"匹配菜谱请求 - 考虑前 {top_n} 种食材，返回 {recipe_count} 个菜谱")
            
            # 调用服务进行菜谱匹配
            matched_recipes = self.recipe_matching_service.match_recipes_by_expiring_ingredients(
                token, top_n=top_n, recipe_count=recipe_count
            )
            
            if not matched_recipes:
                current_app.logger.info("未找到匹配的菜谱")
                return jsonify({
                    "code": 404,
                    "message": "未找到匹配的菜谱",
                    "data": None
                }), 404
            
            current_app.logger.info(f"找到 {len(matched_recipes)} 个匹配的菜谱")
            return jsonify({
                "code": 200,
                "message": "匹配菜谱成功",
                "data": {
                    "recipes": matched_recipes,
                    "total": len(matched_recipes)
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"匹配菜谱时出错: {str(e)}")
            return jsonify({
                "code": 500,
                "message": f"匹配菜谱失败: {str(e)}",
                "data": None
            }), 500 