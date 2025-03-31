from flask import Blueprint
from controllers.food_vision_controller import FoodVisionController

def create_food_vision_blueprint(excel_db=None):
    """创建食物图像识别蓝图并传入excel_db实例"""
    food_vision_bp = Blueprint('food_vision', __name__)
    
    # 初始化食物图像识别控制器
    food_vision_controller = FoodVisionController(excel_db)
    
    # 注册路由
    food_vision_controller.init_routes(food_vision_bp)
    
    return food_vision_bp 