from flask import Blueprint
from controllers.recipe_controller import RecipeController
from controllers.recipe_matching_controller import RecipeMatchingController

def create_recipe_blueprint(excel_db):
    """
    创建菜谱蓝图
    
    Args:
        excel_db: Excel数据库实例
        
    Returns:
        Blueprint: Flask蓝图对象
    """
    recipe_bp = Blueprint('recipe', __name__)
    
    # 初始化菜谱控制器
    recipe_controller = RecipeController(excel_db)
    recipe_controller.init_routes(recipe_bp)
    
    # 初始化菜谱匹配控制器
    recipe_matching_controller = RecipeMatchingController(excel_db)
    recipe_matching_controller.init_routes(recipe_bp)
    
    return recipe_bp 