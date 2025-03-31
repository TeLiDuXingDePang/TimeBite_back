from flask import Blueprint
from controllers.recommendation_controller import RecommendationController

def create_recommendation_blueprint(excel_db):
    """创建推荐蓝图并传入excel_db实例"""
    recommendation_bp = Blueprint('recommendation', __name__)
    
    # 初始化推荐控制器
    recommendation_controller = RecommendationController(excel_db)
    
    # 注册路由
    recommendation_controller.init_routes(recommendation_bp)
    
    return recommendation_bp 