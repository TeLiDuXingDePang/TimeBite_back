from flask import jsonify, request, Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.recommendation_service import RecommendationService

class RecommendationController:
    """菜谱推荐控制器"""
    
    def __init__(self, excel_db):
        self.recommendation_service = RecommendationService(excel_db)
        
    def init_routes(self, blueprint):
        """初始化路由"""
        blueprint.route('/recommendations', methods=['GET'])(self.get_recipe_recommendations)
        
    @jwt_required()
    def get_recipe_recommendations(self):
        """获取菜谱推荐"""
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求菜谱推荐")
            
            # 获取推荐数量参数，默认为10
            limit = request.args.get('limit', 10, type=int)
            current_app.logger.info(f"推荐数量设置为: {limit}")
            
            # 获取推荐菜谱，将JWT身份标识传递给服务层处理
            recommendations = self.recommendation_service.recommend_recipes(jwt_identity, limit)
            
            # 日志输出推荐结果
            if recommendations:
                current_app.logger.info(f"成功为用户 {jwt_identity} 推荐了 {len(recommendations)} 个菜谱")
                # 输出前3个推荐菜谱的名称和匹配度
                for i, recipe in enumerate(recommendations[:3], 1):
                    match_info = f"匹配度: {recipe.get('match_rate')}% ({recipe.get('matching_ingredients')}/{recipe.get('total_ingredients')})"
                    current_app.logger.info(f"Top {i}: {recipe.get('name')} - {match_info}")
            else:
                current_app.logger.warning(f"未能为用户 {jwt_identity} 推荐任何菜谱")
            
            # 返回结果
            return jsonify({
                'code': 200,
                'message': '获取菜谱推荐成功',
                'data': {
                    'recommendations': recommendations,
                    'total': len(recommendations)
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取菜谱推荐失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"获取菜谱推荐失败: {str(e)}",
                'data': None
            }), 500 