import pandas as pd
import json
from flask import current_app
from models.recipe import Recipe

class RecipeDetailService:
    """菜谱详情服务类"""
    
    def __init__(self, excel_db):
        self.excel_db = excel_db
    
    def get_recipe_detail(self, recipe_id, jwt_user_id=None):
        """
        获取菜谱详情
        
        Args:
            recipe_id: 菜谱ID
            jwt_user_id: JWT中的用户标识，对应users表中的user_id列，用于检查用户食材库存状态
            
        Returns:
            Recipe: 菜谱对象，包含详细信息
        """
        print(f"\n===== 获取菜谱ID: {recipe_id} 的详情 =====")
        
        # 1. 获取基本菜谱信息
        recipes_df = self.excel_db.read_table('recipes')
        if recipes_df.empty:
            print("菜谱表为空")
            return None
        
        # 查找指定ID的菜谱
        recipe_data = recipes_df[recipes_df['id'] == recipe_id]
        if recipe_data.empty:
            print(f"未找到ID为 {recipe_id} 的菜谱")
            return None
        
        # 转换为字典
        recipe_dict = recipe_data.iloc[0].to_dict()
        print(f"找到菜谱: {recipe_dict.get('name')}")
        
        # 打印原始字段信息，帮助调试
        print(f"菜谱原始字段列表: {list(recipe_dict.keys())}")
        
        # 2. 获取菜谱食材信息
        # 如果提供了用户ID，则检查用户的食材库存状态
        if jwt_user_id:
            print(f"检查用户(JWT标识: {jwt_user_id})的食材库存状态")
            ingredients = self._get_recipe_ingredients_with_stock_status(recipe_id, jwt_user_id)
        else:
            ingredients = self._get_recipe_ingredients(recipe_id)
            
        recipe_dict['ingredients'] = ingredients
        
        # 3. 从recipe表的JSON字段中获取菜谱工具信息
        tools = self._parse_json_field(recipe_dict, 'tools', [])
        recipe_dict['tools'] = tools
        # 控制台输出工具信息
        print(f"\n===== 菜谱工具信息 =====")
        if tools:
            print(f"菜谱共需要 {len(tools)} 种工具:")
            for idx, tool in enumerate(tools, 1):
                if isinstance(tool, dict):
                    tool_name = tool.get('name', '未知工具')
                    print(f"{idx}. {tool_name}")
                else:
                    print(f"{idx}. {tool}")
        else:
            print("菜谱未指定工具")
        
        # 4. 从recipe表的JSON字段中获取预处理步骤
        prep_steps = self._parse_json_field(recipe_dict, 'prep_steps', [])
        recipe_dict['prep_steps'] = prep_steps
        # 控制台输出预处理步骤
        print(f"\n===== 菜谱预处理步骤 =====")
        if prep_steps:
            print(f"菜谱共有 {len(prep_steps)} 个预处理步骤:")
            for idx, step in enumerate(prep_steps, 1):
                if isinstance(step, dict):
                    step_num = step.get('step', idx)
                    step_desc = step.get('desc', '') or step.get('content', '')
                    print(f"步骤 {step_num}: {step_desc}")
                else:
                    print(f"步骤 {idx}: {step}")
        else:
            print("菜谱未指定预处理步骤")
        
        # 5. 从recipe表的JSON字段中获取烹饪步骤
        steps = self._parse_json_field(recipe_dict, 'steps', [])
        recipe_dict['steps'] = steps
        # 控制台输出烹饪步骤
        print(f"\n===== 菜谱烹饪步骤 =====")
        if steps:
            print(f"菜谱共有 {len(steps)} 个烹饪步骤:")
            for idx, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    step_num = step.get('step', idx)
                    step_desc = step.get('desc', '') or step.get('content', '')
                    print(f"步骤 {step_num}: {step_desc}")
                else:
                    print(f"步骤 {idx}: {step}")
        else:
            print("菜谱未指定烹饪步骤")
        
        # 6. 从recipe表的JSON字段中获取烹饪小贴士
        tips = recipe_dict.get('tips')
        recipe_dict['tips'] = tips
        # 控制台输出小贴士
        print(f"\n===== 菜谱小贴士 =====")
        if tips:
            if isinstance(tips, list):
                for idx, tip in enumerate(tips, 1):
                    print(f"贴士 {idx}: {tip}")
            else:
                print(f"贴士: {tips}")
        else:
            print("菜谱未提供小贴士")
        
        # 7. 生成菜谱标签
        tags = self._generate_tags(recipe_dict)
        recipe_dict['tags'] = tags
        
        # 创建Recipe对象
        recipe = Recipe.from_dict(recipe_dict)
        
        # 最终输出完整菜谱详情结构
        print(f"\n===== 菜谱详情结构概览 =====")
        print(f"菜谱ID: {recipe_id}")
        print(f"菜谱名称: {recipe_dict.get('name', '')}")
        print(f"食材数量: {len(ingredients)}")
        print(f"工具数量: {len(tools)}")
        print(f"预处理步骤数量: {len(prep_steps)}")
        print(f"烹饪步骤数量: {len(steps)}")
        print(f"是否有小贴士: {'是' if tips else '否'}")
        print(f"标签: {tags}")
        
        return recipe
    
    def _parse_json_field(self, recipe_dict, field_name, default_value):
        """
        解析recipes表中的JSON字段
        
        Args:
            recipe_dict: 菜谱字典
            field_name: 字段名称
            default_value: 默认值（如果字段不存在或解析失败）
            
        Returns:
            解析后的数据
        """
        try:
            field_data = recipe_dict.get(field_name)
            
            # 字段不存在
            if field_data is None or pd.isna(field_data):
                print(f"菜谱中不存在 {field_name} 字段，使用默认值")
                return default_value
                
            # 如果已经是字典或列表类型，直接返回
            if isinstance(field_data, (list, dict)):
                print(f"字段 {field_name} 已是结构化数据类型: {type(field_data)}")
                return field_data
                
            # 如果是字符串，尝试解析JSON
            if isinstance(field_data, str):
                try:
                    parsed_data = json.loads(field_data)
                    print(f"成功解析 {field_name} 字段")
                    return parsed_data
                except json.JSONDecodeError as e:
                    print(f"解析 {field_name} 字段失败: {str(e)}，使用默认值")
                    # 尝试保留原始字符串作为值，如果不是JSON
                    if field_name == 'tips':
                        return field_data  # 对于tips，如果解析失败，可能是纯文本，直接返回
                    return default_value
                    
            print(f"{field_name} 字段类型未知：{type(field_data)}，使用默认值")
            return default_value
            
        except Exception as e:
            print(f"处理 {field_name} 字段时出错: {str(e)}")
            return default_value
    
    def _get_recipe_ingredients(self, recipe_id):
        """获取菜谱所需食材"""
        ingredients = []
        
        # 获取菜谱食材关联表
        recipe_ingredients_df = self.excel_db.read_table('recipe_ingredients')
        if recipe_ingredients_df.empty:
            return ingredients
        
        # 筛选当前菜谱的食材关联记录
        recipe_ingredients = recipe_ingredients_df[recipe_ingredients_df['recipe_id'] == recipe_id]
        
        # 获取食材表
        ingredients_df = self.excel_db.read_table('ingredients')
        
        # 如果有食材记录，添加到列表中
        if not ingredients_df.empty and not recipe_ingredients.empty:
            for _, row in recipe_ingredients.iterrows():
                ingredient_id = row['ingredient_id']
                ingredient_data = ingredients_df[ingredients_df['id'] == ingredient_id]
                
                if not ingredient_data.empty:
                    # 从ingredients表获取食材基本信息
                    ingredient = ingredient_data.iloc[0].to_dict()
                    
                    # 尝试从recipe_ingredients表获取特定菜谱的数量信息
                    quantity = row.get('quantity', 0)
                    # 确保数量是数值类型
                    try:
                        quantity = float(quantity) if isinstance(quantity, str) else quantity
                    except (ValueError, TypeError):
                        quantity = 0
                    
                    # 处理单位信息
                    # 首先尝试从recipe_ingredients表获取特定菜谱的单位
                    recipe_unit = row.get('unit', '')
                    # 如果recipe_ingredients没有单位，则使用ingredients表中的默认单位
                    ingredient_unit = ingredient.get('unit', '')
                    
                    # 确定最终使用的单位
                    final_unit = recipe_unit if recipe_unit else ingredient_unit
                    
                    # 添加数量和单位信息到食材字典
                    ingredient['quantity'] = quantity
                    ingredient['unit'] = final_unit
                    
                    # 调试输出
                    print(f"食材 {ingredient.get('name', '')}(ID:{ingredient_id}): 数量 {quantity} {final_unit}")
                    
                    ingredients.append(ingredient)
        
        print(f"菜谱共需要 {len(ingredients)} 种食材")
        return ingredients
    
    def _get_recipe_tools(self, recipe_id):
        """
        获取菜谱所需工具（已废弃，由_parse_json_field方法替代）
        保留此方法是为了兼容性
        """
        return []
    
    def _get_recipe_prep_steps(self, recipe_id):
        """
        获取菜谱预处理步骤（已废弃，由_parse_json_field方法替代）
        保留此方法是为了兼容性
        """
        return []
    
    def _get_recipe_steps(self, recipe_id):
        """
        获取菜谱烹饪步骤（已废弃，由_parse_json_field方法替代）
        保留此方法是为了兼容性
        """
        return []
    
    def _get_recipe_tips(self, recipe_id):
        """
        获取菜谱小贴士（已废弃，由_parse_json_field方法替代）
        保留此方法是为了兼容性
        """
        return None
    
    def _generate_tags(self, recipe_dict):
        """根据菜谱卡路里、烹饪时长和难度生成标签"""
        tags = []
        
        # 从菜谱字典中获取卡路里、烹饪时长和难度
        calories = recipe_dict.get('calories')
        cook_time = recipe_dict.get('cook_time')
        difficulty = recipe_dict.get('difficulty')
        
        # 根据卡路里生成标签
        if calories is not None and pd.notna(calories):
            # 确保卡路里是数值类型
            try:
                calories = float(calories) if isinstance(calories, str) else calories
                if calories < 300:
                    tags.append('低卡')
                elif calories < 600:
                    tags.append('中卡')
                else:
                    tags.append('高卡')
            except (ValueError, TypeError):
                print(f"卡路里格式错误: {calories}")
        
        # 根据烹饪时长生成标签
        if cook_time is not None and pd.notna(cook_time):
            # 确保cook_time是数字
            try:
                cook_time = float(cook_time) if isinstance(cook_time, str) else cook_time
                cook_time = int(cook_time)
                if cook_time < 15:
                    tags.append('快速料理')
                elif cook_time < 30:
                    tags.append('半小时内')
                else:
                    tags.append('耗时较长')
            except (ValueError, TypeError):
                print(f"烹饪时长格式错误: {cook_time}")
        
        # 根据难度生成标签
        if difficulty is not None and pd.notna(difficulty):
            try:
                # 尝试将难度转为整数（如果是数字表示）
                if isinstance(difficulty, (int, float)) or (isinstance(difficulty, str) and difficulty.isdigit()):
                    difficulty_val = int(difficulty)
                    if difficulty_val <= 1:
                        tags.append('新手友好')
                    elif difficulty_val <= 3:
                        tags.append('中等难度')
                    else:
                        tags.append('大厨水平')
                # 处理文字描述的难度
                elif isinstance(difficulty, str):
                    difficulty_lower = difficulty.lower()
                    # 简单/新手级别
                    if '简单' in difficulty_lower or '容易' in difficulty_lower or '入门' in difficulty_lower or '新手' in difficulty_lower:
                        tags.append('新手友好')
                    # 中等难度
                    elif '中等' in difficulty_lower or '适中' in difficulty_lower:
                        tags.append('中等难度')
                    # 高难度
                    elif '困难' in difficulty_lower or '复杂' in difficulty_lower or '高级' in difficulty_lower or '大厨' in difficulty_lower:
                        tags.append('大厨水平')
                    else:
                        print(f"未能识别的难度描述: {difficulty}")
            except (ValueError, TypeError) as e:
                print(f"难度格式错误: {difficulty}, 错误信息: {str(e)}")
        
        print(f"生成的标签: {tags}")
        return tags
    
    def test_get_ingredients(self, recipe_id):
        """测试获取食材列表的功能"""
        print(f"\n===== 测试获取菜谱ID: {recipe_id} 的食材 =====")
        
        ingredients = self._get_recipe_ingredients(recipe_id)
        
        if not ingredients:
            print("未找到食材或菜谱不存在")
            return []
            
        print(f"找到 {len(ingredients)} 种食材:")
        for idx, ing in enumerate(ingredients, 1):
            name = ing.get('name', '未知食材')
            quantity = ing.get('quantity', 0)
            unit = ing.get('unit', '')
            print(f"{idx}. {name}: {quantity} {unit}")
            
        return ingredients
    
    def _get_recipe_ingredients_with_stock_status(self, recipe_id, jwt_user_id):
        """
        获取菜谱所需食材并检查用户库存状态
        
        Args:
            recipe_id: 菜谱ID
            jwt_user_id: JWT中的用户标识，对应users表中的user_id列
            
        Returns:
            list: 食材列表，每个食材包含库存状态
        """
        # 先获取普通的食材列表
        ingredients = self._get_recipe_ingredients(recipe_id)
        
        # 如果没有食材，直接返回空列表
        if not ingredients:
            return []
            
        # 1. 根据JWT中获取的user_id找到users表中对应的id
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            print("用户表为空，无法获取用户信息")
            # 返回原始食材列表，不添加库存状态
            return ingredients
        
        # 确认users表中是否存在user_id列
        if 'user_id' not in users_df.columns:
            print(f"警告: users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
            return ingredients
        
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
            
            # 如果仍未找到记录，返回原始食材列表
            if user_record.empty:
                print(f"在users表中未找到与JWT标识匹配的用户记录，不添加库存状态")
                return ingredients
        
        # 获取用户在数据库中的id (主键)
        db_user_id = user_record.iloc[0]['id']
        print(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
        
        # 2. 获取用户食材库
        user_ingredients_df = self.excel_db.read_table('user_ingredients')
        if user_ingredients_df.empty:
            print("用户食材库表为空，所有食材标记为库存不足")
            # 所有食材标记为库存不足
            for ingredient in ingredients:
                ingredient['stock_status'] = 'insufficient'
            return ingredients
        
        # 使用数据库id(主键)筛选当前用户的食材
        user_ingredients_df = user_ingredients_df[user_ingredients_df['user_id'] == db_user_id]
        if user_ingredients_df.empty:
            print(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})没有食材，所有食材标记为库存不足")
            # 所有食材标记为库存不足
            for ingredient in ingredients:
                ingredient['stock_status'] = 'insufficient'
            return ingredients
        
        print(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})拥有 {len(user_ingredients_df)} 种食材")
        
        # 将用户食材转换为字典，方便查询
        user_ingredient_dict = {}
        for _, row in user_ingredients_df.iterrows():
            ingredient_id = row['ingredient_id']
            quantity = row.get('quantity', 0)
            # 确保数量是数值类型
            try:
                quantity = float(quantity) if isinstance(quantity, str) else quantity
            except (ValueError, TypeError):
                quantity = 0
            user_ingredient_dict[ingredient_id] = quantity
        
        # 3. 检查每个食材的库存状态
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            required_quantity = ingredient.get('quantity', 0)
            # 确保数量是数值类型
            try:
                required_quantity = float(required_quantity) if isinstance(required_quantity, str) else required_quantity
            except (ValueError, TypeError):
                required_quantity = 0
            
            # 检查用户是否拥有该食材，以及数量是否足够
            if ingredient_id in user_ingredient_dict:
                user_quantity = user_ingredient_dict[ingredient_id]
                
                if user_quantity >= required_quantity:
                    ingredient['stock_status'] = 'sufficient'
                    print(f"食材 {ingredient.get('name')}(ID:{ingredient_id}): 需要 {required_quantity}，库存 {user_quantity}，状态: 充足")
                else:
                    ingredient['stock_status'] = 'insufficient'
                    print(f"食材 {ingredient.get('name')}(ID:{ingredient_id}): 需要 {required_quantity}，库存 {user_quantity}，状态: 不足")
            else:
                ingredient['stock_status'] = 'missing'
                print(f"食材 {ingredient.get('name')}(ID:{ingredient_id}): 需要 {required_quantity}，库存: 无，状态: 缺失")
        
        return ingredients 