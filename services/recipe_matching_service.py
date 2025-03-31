from flask import current_app
from services.ingredient_service import IngredientService
from services.recipe_service import RecipeService
from repositories.recipe_repository import RecipeRepository
from utils.jwt_utils import get_user_id_from_token
import pandas as pd
import numpy as np

class RecipeMatchingService:
    """基于用户食材匹配菜谱的服务类"""
    
    def __init__(self, excel_db):
        """
        初始化服务
        
        Args:
            excel_db: Excel数据库实例
        """
        self.excel_db = excel_db
        self.ingredient_service = IngredientService(excel_db)
        # 创建RecipeRepository实例并传递给RecipeService
        recipe_repository = RecipeRepository(excel_db)
        self.recipe_service = RecipeService(recipe_repository)
    
    def match_recipes_by_expiring_ingredients(self, token, top_n=5, recipe_count=3):
        """
        基于用户最快过期的食材匹配菜谱
        
        Args:
            token: JWT令牌
            top_n: 考虑的最快过期食材数量，默认为5
            recipe_count: 返回的菜谱数量，默认为3
            
        Returns:
            list: 匹配的菜谱列表，每个菜谱包含id, name, matching_ingredients, matching_score等信息
        """
        try:
            # 获取用户ID
            user_id = get_user_id_from_token(token)
            if not user_id:
                current_app.logger.error("无法从令牌中获取用户ID")
                return []
                
            # 获取用户最快过期的食材
            expiring_ingredients = self.ingredient_service.get_top_expiring_ingredients(token, limit=top_n)
            if not expiring_ingredients:
                current_app.logger.info(f"用户 {user_id} 没有设置过期日期的食材")
                return []
                
            # 提取食材名称列表
            ingredient_names = [ing['name'] for ing in expiring_ingredients]
            current_app.logger.info(f"用户 {user_id} 最快过期的 {len(ingredient_names)} 种食材: {', '.join(ingredient_names)}")
            
            # 获取所有菜谱
            recipes = self.recipe_service.get_all_recipes()
            if not recipes:
                current_app.logger.warning("没有找到任何菜谱")
                return []
            
            # 将Recipe对象转换为字典
            all_recipes = [recipe.to_dict() for recipe in recipes]
            current_app.logger.info(f"找到 {len(all_recipes)} 个菜谱")
            
            # 计算每个菜谱的匹配分数
            matched_recipes = []
            for recipe in all_recipes:
                # 获取菜谱所需食材
                recipe_ingredients = self._get_recipe_ingredients(recipe['id'])
                if not recipe_ingredients:
                    continue
                    
                # 提取食材名称
                recipe_ingredient_names = [ri['name'] for ri in recipe_ingredients]
                
                # 计算匹配的食材
                matching_ingredients = []
                for name in ingredient_names:
                    if name in recipe_ingredient_names:
                        # 找到对应的食材详细信息
                        for ing in expiring_ingredients:
                            if ing['name'] == name:
                                matching_ingredients.append({
                                    'name': name,
                                    'days_until_expiry': ing['days_until_expiry']
                                })
                                break
                
                # 计算匹配分数（仅基于匹配食材数量）
                if matching_ingredients:
                    # 收集食材紧迫性信息（仅用于日志记录）
                    urgency_info = []
                    for ing in matching_ingredients:
                        days = ing['days_until_expiry']
                        urgency_info.append(f"{ing['name']}({days}天)")
                    
                    # 按照菜谱推荐服务的算法，计算匹配度为匹配食材数量与菜谱总食材数量的比例
                    match_rate = (len(matching_ingredients) / len(recipe_ingredient_names)) * 100
                    
                    current_app.logger.debug(f"菜谱 {recipe['name']} 匹配度: {match_rate:.1f}%, 匹配食材: {', '.join(urgency_info)}")
                    
                    # 提取关键菜谱信息
                    recipe_info = {
                        'id': recipe['id'],
                        'name': recipe['name'],
                        'matching_ingredients': [{'name': ing['name']} for ing in matching_ingredients],
                        'matching_score': round(match_rate),  # 使用推荐服务相同的匹配度计算方式
                        'total_ingredients': len(recipe_ingredient_names),
                        'tags': self._generate_tags(recipe)
                    }
                    
                    # 添加额外菜谱信息
                    for field in ['cook_time', 'calories', 'difficulty', 'image', 'description']:
                        if field in recipe and recipe[field] is not None:
                            recipe_info[field] = recipe[field]
                    
                    # 确保烹饪时间是整数格式
                    if 'cook_time' in recipe_info and recipe_info['cook_time'] is not None:
                        try:
                            recipe_info['cook_time'] = int(recipe_info['cook_time'])
                        except (ValueError, TypeError):
                            current_app.logger.warning(f"菜谱ID={recipe['id']}的烹饪时间格式错误: {recipe_info['cook_time']}")
                    
                    matched_recipes.append(recipe_info)
                    current_app.logger.debug(f"匹配菜谱: {recipe['name']}(ID={recipe['id']}), 匹配分数: {recipe_info['matching_score']}, 烹饪时间: {recipe_info.get('cook_time')}")
            
            # 按匹配分数排序并限制返回数量
            matched_recipes.sort(key=lambda x: x['matching_score'], reverse=True)
            return matched_recipes[:recipe_count]
            
        except Exception as e:
            current_app.logger.error(f"匹配菜谱时出错: {str(e)}")
            return []
    
    def _get_recipe_ingredients(self, recipe_id):
        """获取菜谱所需的食材列表"""
        try:
            current_app.logger.debug(f"获取菜谱ID={recipe_id}的食材列表")
            recipe_ingredients_df = self.excel_db.read_table('recipe_ingredients')
            ingredients_df = self.excel_db.read_table('ingredients')
            
            # 筛选指定菜谱的食材
            recipe_ingredients = recipe_ingredients_df[recipe_ingredients_df['recipe_id'] == recipe_id]
            
            if recipe_ingredients.empty:
                current_app.logger.warning(f"菜谱ID={recipe_id}没有关联的食材")
                return []
            
            # 合并食材信息
            result = []
            for _, row in recipe_ingredients.iterrows():
                ingredient_id = row['ingredient_id']
                ingredient = ingredients_df[ingredients_df['id'] == ingredient_id]
                if not ingredient.empty:
                    result.append({
                        'id': ingredient_id,
                        'name': ingredient.iloc[0]['name'],
                        'quantity': row['quantity'],
                        'unit': row['unit'] if 'unit' in row else ''
                    })
                else:
                    current_app.logger.warning(f"未找到ID={ingredient_id}的食材信息")
            
            current_app.logger.debug(f"菜谱ID={recipe_id}共有{len(result)}种食材")
            return result
        except Exception as e:
            current_app.logger.error(f"获取菜谱食材时出错: {str(e)}")
            return []
    
    def _generate_tags(self, recipe):
        """根据菜谱信息生成标签"""
        tags = []
        
        # 基于卡路里生成标签
        if 'calories' in recipe and recipe['calories'] is not None:
            calories = recipe['calories']
            if calories < 300:
                tags.append("低卡")
            elif calories < 600:
                tags.append("中卡")
            else:
                tags.append("高卡")
        
        # 基于烹饪时间生成标签
        if 'cook_time' in recipe and recipe['cook_time'] is not None:
            cook_time = recipe['cook_time']
            if cook_time <= 15:
                tags.append("快速")
            elif cook_time <= 30:
                tags.append("中速")
            else:
                tags.append("慢食")
        
        return tags 