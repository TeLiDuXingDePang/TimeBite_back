from models.recipe import Recipe

class RecipeService:
    """菜谱服务类"""
    
    def __init__(self, recipe_repository):
        self.recipe_repository = recipe_repository
    
    def get_all_recipes(self):
        """获取所有菜谱"""
        return self.recipe_repository.find_all()
    
    def get_recipe_by_id(self, recipe_id):
        """根据ID获取菜谱"""
        recipe = self.recipe_repository.find_by_id(recipe_id)
        if not recipe:
            raise ValueError("菜谱不存在")
        return recipe 