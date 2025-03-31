import random
import pandas as pd
from flask import current_app
from models.recipe import Recipe

class RecommendationService:
    """菜谱推荐服务类"""
    
    def __init__(self, excel_db):
        self.excel_db = excel_db
    
    def recommend_recipes(self, jwt_user_id, limit=10):
        """
        根据用户食材库为用户推荐菜谱
        
        Args:
            jwt_user_id: JWT中的用户标识，对应users表中的user_id列
            limit: 返回的菜谱数量上限
            
        Returns:
            list: 推荐的菜谱列表，每个菜谱包含匹配度信息
        """
        print(f"\n===== 开始为用户(JWT标识) {jwt_user_id} 推荐菜谱 =====")
        
        # 0. 根据JWT中获取的user_id找到users表中对应的id
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            print("用户表为空，无法获取用户信息")
            return self._get_random_recipes(limit)
        
        print(f"用户表列名: {users_df.columns.tolist()}")
        
        # 确认users表中是否存在user_id列
        if 'user_id' not in users_df.columns:
            print(f"警告: users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
            return self._get_random_recipes(limit)
        
        # 根据JWT中的user_id查找用户记录
        user_record = users_df[users_df['user_id'] == jwt_user_id]
        
        if user_record.empty:
            print(f"在users表中未找到user_id={jwt_user_id}的记录")
            # 尝试其他可能的格式转换
            if isinstance(jwt_user_id, str) and jwt_user_id.startswith('u_'):
                # 尝试去掉前缀
                user_id_without_prefix = jwt_user_id[2:]
                user_record = users_df[users_df['user_id'] == user_id_without_prefix]
                if not user_record.empty:
                    print(f"通过去掉'u_'前缀找到用户记录")
            
            # 如果仍未找到记录，返回随机推荐
            if user_record.empty:
                print(f"在users表中未找到与JWT标识匹配的用户记录，返回随机推荐")
                return self._get_random_recipes(limit)
        
        # 获取用户在数据库中的id (主键)
        db_user_id = user_record.iloc[0]['id']
        print(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
        
        # 1. 获取用户食材库
        user_ingredients_df = self.excel_db.read_table('user_ingredients')
        if user_ingredients_df.empty:
            print("用户食材库表为空，返回随机推荐")
            return self._get_random_recipes(limit)
        
        # 使用数据库id(主键)筛选当前用户的食材
        user_ingredients_df = user_ingredients_df[user_ingredients_df['user_id'] == db_user_id]
        if user_ingredients_df.empty:
            print(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})没有食材，返回随机推荐")
            return self._get_random_recipes(limit)
        
        print(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})拥有 {len(user_ingredients_df)} 种食材")
        
        # 用户拥有的食材ID和数量字典
        user_ingredients = {}
        for _, row in user_ingredients_df.iterrows():
            ingredient_id = row['ingredient_id']
            quantity = row['quantity'] if 'quantity' in row else 0
            user_ingredients[ingredient_id] = quantity
            
        print(f"用户食材库: {user_ingredients}")
        
        # 2. 获取所有菜谱
        recipes_df = self.excel_db.read_table('recipes')
        if recipes_df.empty:
            print("菜谱表为空，无法推荐")
            return []
        
        print(f"系统中共有 {len(recipes_df)} 个菜谱")
        
        # 3. 获取菜谱食材关联表
        recipe_ingredients_df = self.excel_db.read_table('recipe_ingredients')
        if recipe_ingredients_df.empty:
            print("菜谱食材关联表为空，返回随机推荐")
            return self._get_random_recipes(limit)
        
        print(f"菜谱食材关联表中共有 {len(recipe_ingredients_df)} 条记录")
        
        # 4. 计算每个菜谱的匹配度
        recipe_matches = {}
        recipe_names = {}  # 用于日志输出
        
        # 为每个菜谱创建一个字典，存储该菜谱需要的所有食材及其数量
        recipe_required_ingredients = {}
        
        # 获取每个菜谱的名称（用于日志）
        for _, recipe in recipes_df.iterrows():
            recipe_id = recipe['id']
            recipe_names[recipe_id] = recipe['name']
            recipe_required_ingredients[recipe_id] = {}
        
        # 收集每个菜谱需要的所有食材及其数量
        for _, row in recipe_ingredients_df.iterrows():
            recipe_id = row['recipe_id']
            ingredient_id = row['ingredient_id']
            quantity = row['quantity'] if 'quantity' in row else 0
            
            if recipe_id in recipe_required_ingredients:
                recipe_required_ingredients[recipe_id][ingredient_id] = quantity
        
        print("\n===== 开始计算菜谱匹配度 =====")
        
        # 计算菜谱匹配度
        for recipe_id, required_ingredients in recipe_required_ingredients.items():
            if recipe_id not in recipe_names:
                continue
                
            recipe_name = recipe_names[recipe_id]
            print(f"\n检查菜谱 {recipe_id}: {recipe_name}")
            print(f"该菜谱需要的食材: {required_ingredients}")
            
            if not required_ingredients:  # 如果菜谱没有关联食材
                print(f"菜谱 {recipe_name} 没有关联食材，跳过")
                continue
            
            # 统计匹配的食材数量
            matching_ingredients = 0
            total_ingredients = len(required_ingredients)
            
            # 检查用户拥有哪些食材是菜谱所需的
            for ingredient_id, required_quantity in required_ingredients.items():
                if ingredient_id in user_ingredients:
                    user_quantity = user_ingredients[ingredient_id]
                    print(f"食材 {ingredient_id}: 需要 {required_quantity}, 用户拥有 {user_quantity}")
                    
                    # 如果用户拥有该食材，且数量足够，则算作匹配
                    if user_quantity >= required_quantity:
                        matching_ingredients += 1
                        print(f"食材 {ingredient_id} 匹配成功")
                    else:
                        print(f"食材 {ingredient_id} 数量不足")
                else:
                    print(f"食材 {ingredient_id} 用户未拥有")
            
            # 计算匹配度百分比
            if total_ingredients > 0:
                match_rate = (matching_ingredients / total_ingredients) * 100
            else:
                match_rate = 0
                
            print(f"菜谱 {recipe_name} 匹配度: {match_rate:.1f}% ({matching_ingredients}/{total_ingredients})")
            
            recipe_matches[recipe_id] = {
                'matching_ingredients': matching_ingredients,
                'total_ingredients': total_ingredients,
                'match_rate': match_rate
            }
        
        # 5. 如果没有任何匹配，返回随机菜谱
        if not recipe_matches or all(match['match_rate'] == 0 for match in recipe_matches.values()):
            print("没有找到匹配的菜谱，返回随机推荐")
            return self._get_random_recipes(limit)
        
        # 6. 按匹配度排序
        sorted_recipes = sorted(recipe_matches.items(), key=lambda x: x[1]['match_rate'], reverse=True)
        
        print("\n===== 按匹配度排序的菜谱 =====")
        for recipe_id, match_info in sorted_recipes[:10]:  # 只打印前10个，避免日志过长
            recipe_name = recipe_names.get(recipe_id, f"未知菜谱({recipe_id})")
            print(f"菜谱 {recipe_name}: 匹配度 {match_info['match_rate']:.1f}% ({match_info['matching_ingredients']}/{match_info['total_ingredients']})")
        
        # 7. 获取前N个菜谱详情
        result = []
        for recipe_id, match_info in sorted_recipes[:limit]:
            recipe_data = recipes_df[recipes_df['id'] == recipe_id].iloc[0].to_dict()
            
            # 创建Recipe对象
            recipe = Recipe.from_dict(recipe_data)
            
            # 添加匹配度信息
            recipe_dict = recipe.to_response_dict()
            recipe_dict['match_rate'] = round(match_info['match_rate'], 1)  # 保留一位小数
            recipe_dict['matching_ingredients'] = match_info['matching_ingredients']
            recipe_dict['total_ingredients'] = match_info['total_ingredients']

            # 确保cook_time是纯数字，不包含单位
            if 'cook_time' in recipe_dict and recipe_dict['cook_time'] is not None:
                recipe_dict['cook_time'] = int(recipe_dict['cook_time'])
            
            result.append(recipe_dict)
        
        print(f"\n===== 为用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})推荐了 {len(result)} 个菜谱 =====")
        return result
    
    def _get_random_recipes(self, limit=10):
        """获取随机菜谱，当用户没有食材或匹配度为0时使用"""
        print("\n===== 获取随机菜谱推荐 =====")
        
        recipes_df = self.excel_db.read_table('recipes')
        if recipes_df.empty:
            print("菜谱表为空，无法提供随机推荐")
            return []
        
        # 获取所有菜谱ID
        all_recipe_ids = recipes_df['id'].tolist()
        
        # 随机选择菜谱ID
        sample_size = min(limit, len(all_recipe_ids))
        if sample_size == 0:
            print("没有可用的菜谱进行随机推荐")
            return []
            
        selected_ids = random.sample(all_recipe_ids, sample_size)
        print(f"随机选择了 {sample_size} 个菜谱: {selected_ids}")
        
        # 获取选中的菜谱详情
        result = []
        for recipe_id in selected_ids:
            recipe_data = recipes_df[recipes_df['id'] == recipe_id].iloc[0].to_dict()
            
            # 创建Recipe对象
            recipe = Recipe.from_dict(recipe_data)
            recipe_name = recipe_data.get('name', f"未知菜谱({recipe_id})")
            print(f"添加随机菜谱: {recipe_name}")
            
            # 添加匹配度信息（随机推荐的匹配度为0）
            recipe_dict = recipe.to_response_dict()
            recipe_dict['match_rate'] = 0.0
            recipe_dict['matching_ingredients'] = 0
            recipe_dict['total_ingredients'] = 0
            
            # 确保cook_time是纯数字，不包含单位
            if 'cook_time' in recipe_dict and recipe_dict['cook_time'] is not None:
                recipe_dict['cook_time'] = int(recipe_dict['cook_time'])
            
            result.append(recipe_dict)
        
        print(f"随机推荐了 {len(result)} 个菜谱")
        return result 