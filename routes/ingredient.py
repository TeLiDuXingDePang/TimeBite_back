from flask import Blueprint
from controllers.ingredient_controller import IngredientController

def create_ingredient_blueprint(excel_db):
    """创建食材蓝图并传入excel_db实例"""
    ingredient_bp = Blueprint('ingredient', __name__)
    
    # 初始化食材控制器
    ingredient_controller = IngredientController(excel_db)
    
    # 注册路由
    ingredient_controller.init_routes(ingredient_bp)
    
    return ingredient_bp 