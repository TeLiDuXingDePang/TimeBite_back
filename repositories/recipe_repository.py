import pandas as pd
from datetime import datetime
from models.recipe import Recipe

class RecipeRepository:
    """菜谱数据访问类"""
    
    def __init__(self, excel_db):
        self.excel_db = excel_db
    
    def find_all(self):
        """获取所有菜谱"""
        recipes_df = self.excel_db.read_table('recipes')
        if recipes_df.empty:
            return []
        
        return [Recipe.from_dict(recipe) for recipe in recipes_df.to_dict('records')]
    
    def find_by_id(self, recipe_id):
        """根据ID获取菜谱"""
        recipes_df = self.excel_db.read_table('recipes')
        if recipes_df.empty:
            return None
        
        recipe = recipes_df[recipes_df['id'] == recipe_id]
        if recipe.empty:
            return None
        
        return Recipe.from_dict(recipe.iloc[0].to_dict())
    
    def create(self, recipe):
        """创建新菜谱"""
        recipes_df = self.excel_db.read_table('recipes')
        
        # 准备菜谱数据
        recipe_dict = recipe.to_dict()
        
        # 生成ID
        if recipes_df.empty:
            new_id = 1
        else:
            new_id = recipes_df['id'].max() + 1
        
        recipe_dict['id'] = new_id
        
        # 添加时间戳
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not recipe_dict.get('created_at'):
            recipe_dict['created_at'] = now
        if not recipe_dict.get('updated_at'):
            recipe_dict['updated_at'] = now
        
        # 添加到DataFrame
        new_row = pd.DataFrame([recipe_dict])
        recipes_df = pd.concat([recipes_df, new_row], ignore_index=True)
        
        # 保存到Excel
        self.excel_db.write_table('recipes', recipes_df)
        
        return Recipe.from_dict(recipe_dict)
    
    def update(self, recipe_id, update_data):
        """更新菜谱信息"""
        recipes_df = self.excel_db.read_table('recipes')
        if recipes_df.empty:
            return None
        
        # 查找菜谱
        recipe_idx = recipes_df[recipes_df['id'] == recipe_id].index
        if len(recipe_idx) == 0:
            return None
        
        # 更新时间戳
        update_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新菜谱数据
        for key, value in update_data.items():
            recipes_df.loc[recipe_idx[0], key] = value
        
        # 保存到Excel
        self.excel_db.write_table('recipes', recipes_df)
        
        # 返回更新后的菜谱信息
        return Recipe.from_dict(recipes_df.loc[recipe_idx[0]].to_dict())
    
    def delete(self, recipe_id):
        """删除菜谱"""
        recipes_df = self.excel_db.read_table('recipes')
        if recipes_df.empty:
            return False
        
        # 查找菜谱
        recipe_idx = recipes_df[recipes_df['id'] == recipe_id].index
        if len(recipe_idx) == 0:
            return False
        
        # 删除菜谱
        recipes_df = recipes_df.drop(recipe_idx)
        
        # 保存到Excel
        self.excel_db.write_table('recipes', recipes_df)
        
        return True 