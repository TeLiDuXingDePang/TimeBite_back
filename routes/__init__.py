from routes.user import create_user_blueprint
from routes.recipe import create_recipe_blueprint
from routes.recommendation import create_recommendation_blueprint
from routes.ingredient import create_ingredient_blueprint
from routes.food_vision import create_food_vision_blueprint

def register_blueprints(app, excel_db):
    """注册所有蓝图"""
    # 创建用户蓝图并传入excel_db
    user_bp = create_user_blueprint(excel_db)
    app.register_blueprint(user_bp, url_prefix='/api/v1/user')
    
    # 创建菜谱蓝图并传入excel_db
    recipe_bp = create_recipe_blueprint(excel_db)
    app.register_blueprint(recipe_bp, url_prefix='/api/v1/recipes')
    
    # 创建推荐蓝图并传入excel_db
    recommendation_bp = create_recommendation_blueprint(excel_db)
    app.register_blueprint(recommendation_bp, url_prefix='/api/v1/recipe')
    
    # 创建食材蓝图并传入excel_db
    ingredient_bp = create_ingredient_blueprint(excel_db)
    app.register_blueprint(ingredient_bp, url_prefix='/api/v1/ingredients')
    
    # 创建食物视觉识别蓝图并传入excel_db
    food_vision_bp = create_food_vision_blueprint(excel_db)
    app.register_blueprint(food_vision_bp, url_prefix='/api/v1/food-vision') 