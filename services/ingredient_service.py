import pandas as pd
import random
from datetime import datetime, timedelta
from flask import current_app
from utils.jwt_utils import get_user_id_from_token

class IngredientService:
    """食材服务类"""
    
    def __init__(self, excel_db):
        self.excel_db = excel_db
    
    def get_ingredient_stats(self, token_or_user_id):
        """
        获取用户食材库存统计
        
        Args:
            token_or_user_id: JWT令牌或用户ID
            
        Returns:
            dict: 包含新鲜食材数量、临期食材数量和过期食材数量的字典
        """
        # 如果传入的是令牌，则从令牌中提取用户ID
        if isinstance(token_or_user_id, str) and (token_or_user_id.startswith('Bearer ') or '.' in token_or_user_id):
            jwt_user_id = get_user_id_from_token(token_or_user_id)
            if not jwt_user_id:
                current_app.logger.error("无法从令牌中获取有效的用户ID")
                return {'fresh_count': 0, 'expiring_count': 0, 'expired_count': 0}
        else:
            # 如果传入的是用户ID，则直接使用
            jwt_user_id = token_or_user_id
        
        current_app.logger.info(f"统计用户(JWT标识) {jwt_user_id} 的食材")
        
        # 1. 根据JWT中获取的user_id找到users表中对应的id
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            current_app.logger.warning("用户表为空，无法获取用户信息")
            return {'fresh_count': 0, 'expiring_count': 0, 'expired_count': 0}
        
        # 确认users表中是否存在user_id列
        if 'user_id' not in users_df.columns:
            current_app.logger.warning(f"users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
            return {'fresh_count': 0, 'expiring_count': 0, 'expired_count': 0}
        
        # 根据JWT中的user_id查找用户记录
        user_record = users_df[users_df['user_id'] == jwt_user_id]
        
        if user_record.empty:
            current_app.logger.warning(f"在users表中未找到user_id={jwt_user_id}的记录")
            # 尝试其他可能的格式转换
            if isinstance(jwt_user_id, str) and jwt_user_id.startswith('u_'):
                # 尝试去掉前缀
                user_id_without_prefix = jwt_user_id[2:]
                user_record = users_df[users_df['user_id'] == user_id_without_prefix]
                if not user_record.empty:
                    current_app.logger.info(f"通过去掉'u_'前缀找到用户记录")
            
            # 如果仍未找到记录，返回空结果
            if user_record.empty:
                current_app.logger.warning(f"在users表中未找到与JWT标识匹配的用户记录")
                return {'fresh_count': 0, 'expiring_count': 0, 'expired_count': 0}
        
        # 获取用户在数据库中的id (主键)
        db_user_id = user_record.iloc[0]['id']
        current_app.logger.info(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
        
        # 2. 获取用户食材库
        user_ingredients_df = self.excel_db.read_table('user_ingredients')
        if user_ingredients_df.empty:
            current_app.logger.warning("用户食材库表为空")
            return {'fresh_count': 0, 'expiring_count': 0, 'expired_count': 0}
        
        # 使用数据库id(主键)筛选当前用户的食材
        user_ingredients_df = user_ingredients_df[user_ingredients_df['user_id'] == db_user_id]
        if user_ingredients_df.empty:
            current_app.logger.warning(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})没有食材")
            return {'fresh_count': 0, 'expiring_count': 0, 'expired_count': 0}
        
        current_app.logger.info(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})拥有 {len(user_ingredients_df)} 种食材")
        
        # 3. 计算临期、过期和新鲜食材的数量
        today = datetime.now().date()
        expiring_threshold = today + timedelta(days=3)  # 3天内过期的视为临期食材
        
        # 初始化计数器
        fresh_count = 0
        expiring_count = 0
        expired_count = 0
        
        # 遍历用户的食材
        for _, row in user_ingredients_df.iterrows():
            # 确保数据不为空且格式正确
            if 'expiry_date' in row and row['expiry_date'] and pd.notna(row['expiry_date']):
                try:
                    # 尝试转换日期格式
                    if isinstance(row['expiry_date'], str):
                        expiry_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date()
                    elif isinstance(row['expiry_date'], pd.Timestamp):
                        expiry_date = row['expiry_date'].date()
                    else:
                        expiry_date = row['expiry_date']
                    
                    # 判断是否已过期
                    if expiry_date <= today:
                        expired_count += 1
                        current_app.logger.info(f"食材ID {row['ingredient_id']} 已在 {expiry_date} 过期或今天过期，标记为过期")
                    # 判断是否临期
                    elif expiry_date <= expiring_threshold:
                        expiring_count += 1
                        current_app.logger.info(f"食材ID {row['ingredient_id']} 将在 {expiry_date} 过期，标记为临期")
                    else:
                        fresh_count += 1
                        current_app.logger.info(f"食材ID {row['ingredient_id']} 过期日期为 {expiry_date}，标记为新鲜")
                except (ValueError, TypeError) as e:
                    # 日期格式错误，计入新鲜食材
                    current_app.logger.info(f"食材ID {row['ingredient_id']} 的过期日期 {row['expiry_date']} 格式错误: {str(e)}，默认计入新鲜食材")
                    fresh_count += 1
            else:
                # 没有过期日期，计入新鲜食材
                current_app.logger.info(f"食材ID {row['ingredient_id']} 没有过期日期信息，默认计入新鲜食材")
                fresh_count += 1
        
        result = {
            'fresh_count': fresh_count,
            'expiring_count': expiring_count,
            'expired_count': expired_count
        }
        
        current_app.logger.info(f"统计结果: 新鲜食材 {fresh_count} 种，临期食材 {expiring_count} 种，过期食材 {expired_count} 种")
        return result
        
    def get_most_expiring_ingredient(self, token_or_user_id):
        """
        获取用户食材库中最快过期的一个食材
        
        Args:
            token_or_user_id: JWT令牌或用户ID
            
        Returns:
            dict: 包含食材名称、数量和单位的字典，若无临期食材则返回None
        """
        # 如果传入的是令牌，则从令牌中提取用户ID
        if isinstance(token_or_user_id, str) and (token_or_user_id.startswith('Bearer ') or '.' in token_or_user_id):
            jwt_user_id = get_user_id_from_token(token_or_user_id)
            if not jwt_user_id:
                current_app.logger.error("无法从令牌中获取有效的用户ID")
                return None
        else:
            # 如果传入的是用户ID，则直接使用
            jwt_user_id = token_or_user_id
        
        current_app.logger.info(f"获取用户(JWT标识) {jwt_user_id} 最快过期的食材")
        
        # 1. 根据JWT中获取的user_id找到users表中对应的id
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            current_app.logger.warning("用户表为空，无法获取用户信息")
            return None
        
        # 确认users表中是否存在user_id列
        if 'user_id' not in users_df.columns:
            current_app.logger.warning(f"警告: users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
            return None
        
        # 根据JWT中的user_id查找用户记录
        user_record = users_df[users_df['user_id'] == jwt_user_id]
        
        if user_record.empty:
            current_app.logger.warning(f"在users表中未找到user_id={jwt_user_id}的记录")
            # 尝试其他可能的格式转换
            if isinstance(jwt_user_id, str) and jwt_user_id.startswith('u_'):
                # 尝试去掉前缀
                user_id_without_prefix = jwt_user_id[2:]
                user_record = users_df[users_df['user_id'] == user_id_without_prefix]
                if not user_record.empty:
                    current_app.logger.info(f"通过去掉'u_'前缀找到用户记录")
            
            # 如果仍未找到记录，返回空结果
            if user_record.empty:
                current_app.logger.warning(f"在users表中未找到与JWT标识匹配的用户记录")
                return None
        
        # 获取用户在数据库中的id (主键)
        db_user_id = user_record.iloc[0]['id']
        current_app.logger.info(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
        
        # 2. 获取用户食材库
        user_ingredients_df = self.excel_db.read_table('user_ingredients')
        if user_ingredients_df.empty:
            current_app.logger.warning("用户食材库表为空")
            return None
        
        # 使用数据库id(主键)筛选当前用户的食材
        user_ingredients_df = user_ingredients_df[user_ingredients_df['user_id'] == db_user_id]
        if user_ingredients_df.empty:
            current_app.logger.warning(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})没有食材")
            return None
        
        current_app.logger.info(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})拥有 {len(user_ingredients_df)} 种食材")
        
        # 3. 获取食材表，用于获取食材名称和单位
        ingredients_df = self.excel_db.read_table('ingredients')
        if ingredients_df.empty:
            current_app.logger.warning("食材表为空，无法获取食材信息")
            return None
            
        # 4. 筛选有过期日期的食材
        valid_ingredients = []
        today = datetime.now().date()
        
        for _, row in user_ingredients_df.iterrows():
            ingredient_id = row['ingredient_id']
            quantity = row.get('quantity', 0)
            
            # 获取食材详细信息
            ingredient_info = ingredients_df[ingredients_df['id'] == ingredient_id]
            if ingredient_info.empty:
                current_app.logger.warning(f"未找到ID为 {ingredient_id} 的食材信息")
                continue
                
            ingredient_name = ingredient_info.iloc[0].get('name', f'未知食材({ingredient_id})')
            ingredient_unit = ingredient_info.iloc[0].get('unit', '')
            
            # 检查是否有过期日期
            if 'expiry_date' in row and row['expiry_date'] and pd.notna(row['expiry_date']):
                try:
                    # 尝试转换日期格式
                    if isinstance(row['expiry_date'], str):
                        expiry_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date()
                    elif isinstance(row['expiry_date'], pd.Timestamp):
                        expiry_date = row['expiry_date'].date()
                    else:
                        expiry_date = row['expiry_date']
                    
                    # 计算与当前日期的差距（天数）
                    days_until_expiry = (expiry_date - today).days
                    
                    # 如果已经过期或当天过期，天数为0
                    if days_until_expiry <= 0:
                        days_until_expiry = 0  # 已过期或当天到期视为0天
                    
                    current_app.logger.info(f"食材 {ingredient_name}(ID:{ingredient_id}): 还有 {days_until_expiry} 天过期")
                    
                    # 添加到有效食材列表
                    valid_ingredients.append({
                        'id': ingredient_id,
                        'name': ingredient_name,
                        'quantity': quantity,
                        'unit': ingredient_unit,
                        'days_until_expiry': days_until_expiry,
                        'expiry_date': expiry_date
                    })
                except (ValueError, TypeError) as e:
                    current_app.logger.warning(f"食材 {ingredient_name}(ID:{ingredient_id}) 的过期日期格式错误: {str(e)}")
            else:
                current_app.logger.info(f"食材 {ingredient_name}(ID:{ingredient_id}) 没有设置过期日期")
        
        # 5. 如果没有有效食材，返回None
        if not valid_ingredients:
            current_app.logger.warning("没有找到设置了过期日期的食材")
            return None
        
        # 6. 按过期天数排序，选择最快过期的食材
        valid_ingredients.sort(key=lambda x: x['days_until_expiry'])
        
        # 找出所有过期天数与最小值相同的食材
        min_days = valid_ingredients[0]['days_until_expiry']
        most_expiring_ingredients = [ingr for ingr in valid_ingredients if ingr['days_until_expiry'] == min_days]
        
        # 如果有多个同样快过期的食材，随机选择一个
        if len(most_expiring_ingredients) > 1:
            current_app.logger.info(f"找到 {len(most_expiring_ingredients)} 个食材将在 {min_days} 天后过期，随机选择一个")
            selected = random.choice(most_expiring_ingredients)
        else:
            selected = most_expiring_ingredients[0]
        
        current_app.logger.info(f"选择的食材: {selected['name']}，数量: {selected['quantity']} {selected['unit']}，还有 {selected['days_until_expiry']} 天过期")
        
        # 7. 返回结果
        result = {
            'name': selected['name'],
            'quantity': selected['quantity'],
            'unit': selected['unit'],
            'days_until_expiry': selected['days_until_expiry'],
            'expiry_date': selected['expiry_date'].strftime('%Y-%m-%d')
        }
        
        return result

    def get_top_expiring_ingredients(self, token_or_user_id, limit=5):
        """
        获取用户食材库中最快过期的多个食材（按过期日期排序）
        
        Args:
            token_or_user_id: JWT令牌或用户ID
            limit: 返回的食材数量上限，默认为5
            
        Returns:
            list: 包含食材信息的列表，按过期日期从近到远排序
        """
        # 如果传入的是令牌，则从令牌中提取用户ID
        if isinstance(token_or_user_id, str) and (token_or_user_id.startswith('Bearer ') or '.' in token_or_user_id):
            jwt_user_id = get_user_id_from_token(token_or_user_id)
            if not jwt_user_id:
                current_app.logger.error("无法从令牌中获取有效的用户ID")
                return []
        else:
            # 如果传入的是用户ID，则直接使用
            jwt_user_id = token_or_user_id
        
        current_app.logger.info(f"获取用户(JWT标识) {jwt_user_id} 最快过期的 {limit} 个食材")
        
        # 1. 根据JWT中获取的user_id找到users表中对应的id
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            current_app.logger.warning("用户表为空，无法获取用户信息")
            return []
        
        # 确认users表中是否存在user_id列
        if 'user_id' not in users_df.columns:
            current_app.logger.warning(f"警告: users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
            return []
        
        # 根据JWT中的user_id查找用户记录
        user_record = users_df[users_df['user_id'] == jwt_user_id]
        
        if user_record.empty:
            current_app.logger.warning(f"在users表中未找到user_id={jwt_user_id}的记录")
            # 尝试其他可能的格式转换
            if isinstance(jwt_user_id, str) and jwt_user_id.startswith('u_'):
                # 尝试去掉前缀
                user_id_without_prefix = jwt_user_id[2:]
                user_record = users_df[users_df['user_id'] == user_id_without_prefix]
                if not user_record.empty:
                    current_app.logger.info(f"通过去掉'u_'前缀找到用户记录")
            
            # 如果仍未找到记录，返回空结果
            if user_record.empty:
                current_app.logger.warning(f"在users表中未找到与JWT标识匹配的用户记录")
                return []
        
        # 获取用户在数据库中的id (主键)
        db_user_id = user_record.iloc[0]['id']
        current_app.logger.info(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
        
        # 2. 获取用户食材库
        user_ingredients_df = self.excel_db.read_table('user_ingredients')
        if user_ingredients_df.empty:
            current_app.logger.warning("用户食材库表为空")
            return []
        
        # 使用数据库id(主键)筛选当前用户的食材
        user_ingredients_df = user_ingredients_df[user_ingredients_df['user_id'] == db_user_id]
        if user_ingredients_df.empty:
            current_app.logger.warning(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})没有食材")
            return []
        
        current_app.logger.info(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})拥有 {len(user_ingredients_df)} 种食材")
        
        # 3. 获取食材表，用于获取食材名称和单位
        ingredients_df = self.excel_db.read_table('ingredients')
        if ingredients_df.empty:
            current_app.logger.warning("食材表为空，无法获取食材信息")
            return []
            
        # 4. 筛选有过期日期的食材
        valid_ingredients = []
        today = datetime.now().date()
        
        for _, row in user_ingredients_df.iterrows():
            ingredient_id = row['ingredient_id']
            quantity = row.get('quantity', 0)
            
            # 获取食材详细信息
            ingredient_info = ingredients_df[ingredients_df['id'] == ingredient_id]
            if ingredient_info.empty:
                current_app.logger.warning(f"未找到ID为 {ingredient_id} 的食材信息")
                continue
                
            ingredient_name = ingredient_info.iloc[0].get('name', f'未知食材({ingredient_id})')
            ingredient_unit = ingredient_info.iloc[0].get('unit', '')
            
            # 检查是否有过期日期
            if 'expiry_date' in row and row['expiry_date'] and pd.notna(row['expiry_date']):
                try:
                    # 尝试转换日期格式
                    if isinstance(row['expiry_date'], str):
                        expiry_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date()
                    elif isinstance(row['expiry_date'], pd.Timestamp):
                        expiry_date = row['expiry_date'].date()
                    else:
                        expiry_date = row['expiry_date']
                    
                    # 计算与当前日期的差距（天数）
                    days_until_expiry = (expiry_date - today).days
                    
                    # 如果已经过期或当天过期，天数为0
                    if days_until_expiry <= 0:
                        days_until_expiry = 0  # 已过期或当天到期视为0天
                    
                    current_app.logger.info(f"食材 {ingredient_name}(ID:{ingredient_id}): 还有 {days_until_expiry} 天过期")
                    
                    # 添加到有效食材列表
                    valid_ingredients.append({
                        'id': ingredient_id,
                        'name': ingredient_name,
                        'quantity': quantity,
                        'unit': ingredient_unit,
                        'days_until_expiry': days_until_expiry,
                        'expiry_date': expiry_date
                    })
                except (ValueError, TypeError) as e:
                    current_app.logger.warning(f"食材 {ingredient_name}(ID:{ingredient_id}) 的过期日期格式错误: {str(e)}")
            else:
                current_app.logger.info(f"食材 {ingredient_name}(ID:{ingredient_id}) 没有设置过期日期")
        
        # 5. 如果没有有效食材，返回空列表
        if not valid_ingredients:
            current_app.logger.warning("没有找到设置了过期日期的食材")
            return []
        
        # 6. 按过期天数排序
        valid_ingredients.sort(key=lambda x: x['days_until_expiry'])
        
        # 7. 只返回前limit个
        result_ingredients = valid_ingredients[:limit]
        
        current_app.logger.info(f"返回 {len(result_ingredients)} 个最快过期的食材")
        for idx, ingr in enumerate(result_ingredients, 1):
            current_app.logger.info(f"{idx}. {ingr['name']}: {ingr['quantity']} {ingr['unit']}, 还有 {ingr['days_until_expiry']} 天过期")
        
        # 8. 格式化结果
        result = []
        for ingr in result_ingredients:
            result.append({
                'id': ingr['id'],
                'name': ingr['name'],
                'quantity': ingr['quantity'],
                'unit': ingr['unit'],
                'days_until_expiry': ingr['days_until_expiry'],
                'expiry_date': ingr['expiry_date'].strftime('%Y-%m-%d')
            })
        
        return result

    def get_all_ingredients(self, token_or_user_id):
        """
        获取用户食材库中所有食材的信息
        
        Args:
            token_or_user_id: JWT令牌或用户ID
            
        Returns:
            list: 包含所有食材信息的列表
        """
        # 如果传入的是令牌，则从令牌中提取用户ID
        if isinstance(token_or_user_id, str) and (token_or_user_id.startswith('Bearer ') or '.' in token_or_user_id):
            jwt_user_id = get_user_id_from_token(token_or_user_id)
            if not jwt_user_id:
                current_app.logger.error("无法从令牌中获取有效的用户ID")
                return []
        else:
            # 如果传入的是用户ID，则直接使用
            jwt_user_id = token_or_user_id
        
        current_app.logger.info(f"获取用户(JWT标识) {jwt_user_id} 的所有食材")
        
        # 1. 根据JWT中获取的user_id找到users表中对应的id
        users_df = self.excel_db.read_table('users')
        if users_df.empty:
            current_app.logger.warning("用户表为空，无法获取用户信息")
            return []
        
        # 确认users表中是否存在user_id列
        if 'user_id' not in users_df.columns:
            current_app.logger.warning(f"警告: users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
            return []
        
        # 根据JWT中的user_id查找用户记录
        user_record = users_df[users_df['user_id'] == jwt_user_id]
        
        if user_record.empty:
            current_app.logger.warning(f"在users表中未找到user_id={jwt_user_id}的记录")
            # 尝试其他可能的格式转换
            if isinstance(jwt_user_id, str) and jwt_user_id.startswith('u_'):
                # 尝试去掉前缀
                user_id_without_prefix = jwt_user_id[2:]
                user_record = users_df[users_df['user_id'] == user_id_without_prefix]
                if not user_record.empty:
                    current_app.logger.info(f"通过去掉'u_'前缀找到用户记录")
            
            # 如果仍未找到记录，返回空结果
            if user_record.empty:
                current_app.logger.warning(f"在users表中未找到与JWT标识匹配的用户记录")
                return []
        
        # 获取用户在数据库中的id (主键)
        db_user_id = user_record.iloc[0]['id']
        current_app.logger.info(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
        
        # 2. 获取用户食材库
        user_ingredients_df = self.excel_db.read_table('user_ingredients')
        if user_ingredients_df.empty:
            current_app.logger.warning("用户食材库表为空")
            return []
        
        # 使用数据库id(主键)筛选当前用户的食材
        user_ingredients_df = user_ingredients_df[user_ingredients_df['user_id'] == db_user_id]
        if user_ingredients_df.empty:
            current_app.logger.warning(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})没有食材")
            return []
        
        current_app.logger.info(f"用户(JWT标识={jwt_user_id}, 数据库ID={db_user_id})拥有 {len(user_ingredients_df)} 种食材")
        
        # 3. 获取食材表，用于获取食材名称和单位
        ingredients_df = self.excel_db.read_table('ingredients')
        if ingredients_df.empty:
            current_app.logger.warning("食材表为空，无法获取食材信息")
            return []
        
        # 4. 处理所有食材
        all_ingredients = []
        today = datetime.now().date()
        
        for _, row in user_ingredients_df.iterrows():
            ingredient_id = row['ingredient_id']
            quantity = row.get('quantity', 0)
            
            # 获取食材详细信息
            ingredient_info = ingredients_df[ingredients_df['id'] == ingredient_id]
            if ingredient_info.empty:
                current_app.logger.warning(f"未找到ID为 {ingredient_id} 的食材信息")
                continue
                
            ingredient_name = ingredient_info.iloc[0].get('name', f'未知食材({ingredient_id})')
            ingredient_unit = ingredient_info.iloc[0].get('unit', '')
            
            # 创建基本食材信息
            ingredient_data = {
                'id': ingredient_id,
                'name': ingredient_name,
                'quantity': quantity,
                'unit': ingredient_unit
            }
            
            # 处理过期日期（如果有）
            if 'expiry_date' in row and row['expiry_date'] and pd.notna(row['expiry_date']):
                try:
                    # 尝试转换日期格式
                    if isinstance(row['expiry_date'], str):
                        expiry_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date()
                    elif isinstance(row['expiry_date'], pd.Timestamp):
                        expiry_date = row['expiry_date'].date()
                    else:
                        expiry_date = row['expiry_date']
                    
                    # 计算与当前日期的差距（天数）
                    days_until_expiry = (expiry_date - today).days
                    
                    # 如果已经过期或当天过期，天数为0
                    if days_until_expiry <= 0:
                        days_until_expiry = 0  # 已过期或当天到期视为0天
                    
                    # 添加过期信息
                    ingredient_data['expiry_date'] = expiry_date.strftime('%Y-%m-%d')
                    ingredient_data['days_until_expiry'] = days_until_expiry
                    
                except ValueError as e:
                    current_app.logger.warning(f"食材 {ingredient_name}(ID:{ingredient_id}) 的过期日期格式错误: {str(e)}")
            
            # 添加到食材列表
            all_ingredients.append(ingredient_data)
        
        current_app.logger.info(f"成功获取用户的 {len(all_ingredients)} 种食材信息")
        return all_ingredients
        
    def delete_ingredient(self, token_or_user_id, ingredient_id):
        """
        删除用户食材库中的特定食材
        
        Args:
            token_or_user_id: JWT令牌或用户ID
            ingredient_id: 要删除的食材ID
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        # 如果传入的是令牌，则从令牌中提取用户ID
        if isinstance(token_or_user_id, str) and (token_or_user_id.startswith('Bearer ') or '.' in token_or_user_id):
            jwt_user_id = get_user_id_from_token(token_or_user_id)
            if not jwt_user_id:
                current_app.logger.error("无法从令牌中获取有效的用户ID")
                return False
        else:
            # 如果传入的是用户ID，则直接使用
            jwt_user_id = token_or_user_id
        
        current_app.logger.info(f"准备删除用户(JWT标识: {jwt_user_id})的食材(ID: {ingredient_id})")
        
        try:
            # 1. 根据JWT中获取的user_id找到users表中对应的id
            users_df = self.excel_db.read_table('users')
            if users_df.empty:
                current_app.logger.warning("用户表为空，无法获取用户信息")
                return False
            
            # 确认users表中是否存在user_id列
            if 'user_id' not in users_df.columns:
                current_app.logger.warning(f"警告: users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
                return False
            
            # 根据JWT中的user_id查找用户记录
            user_record = users_df[users_df['user_id'] == jwt_user_id]
            
            if user_record.empty:
                current_app.logger.warning(f"在users表中未找到user_id={jwt_user_id}的记录")
                # 尝试其他可能的格式转换
                if isinstance(jwt_user_id, str) and jwt_user_id.startswith('u_'):
                    # 尝试去掉前缀
                    user_id_without_prefix = jwt_user_id[2:]
                    user_record = users_df[users_df['user_id'] == user_id_without_prefix]
                    if not user_record.empty:
                        current_app.logger.info(f"通过去掉'u_'前缀找到用户记录")
                
                # 如果仍未找到记录，返回失败
                if user_record.empty:
                    current_app.logger.warning(f"在users表中未找到与JWT标识匹配的用户记录")
                    return False
            
            # 获取用户在数据库中的id (主键)
            db_user_id = user_record.iloc[0]['id']
            current_app.logger.info(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
            
            # 2. 获取用户食材库
            user_ingredients_df = self.excel_db.read_table('user_ingredients')
            if user_ingredients_df.empty:
                current_app.logger.warning("用户食材库表为空")
                return False
            
            # 3. 检查食材是否存在
            # 筛选当前用户的特定食材
            ingredient_to_delete = user_ingredients_df[
                (user_ingredients_df['user_id'] == db_user_id) & 
                (user_ingredients_df['ingredient_id'] == ingredient_id)
            ]
            
            if ingredient_to_delete.empty:
                current_app.logger.warning(f"用户(JWT标识={jwt_user_id})没有ID为{ingredient_id}的食材")
                return False
            
            # 获取食材名称（用于日志）
            ingredients_df = self.excel_db.read_table('ingredients')
            ingredient_name = "未知食材"
            if not ingredients_df.empty:
                ingredient_info = ingredients_df[ingredients_df['id'] == ingredient_id]
                if not ingredient_info.empty:
                    ingredient_name = ingredient_info.iloc[0].get('name', f"未知食材({ingredient_id})")
            
            # 4. 删除食材
            # 找出要删除的行索引
            index_to_delete = ingredient_to_delete.index[0]
            
            # 创建新的DataFrame，排除要删除的行
            new_user_ingredients_df = user_ingredients_df.drop(index_to_delete)
            
            # 保存更新后的表格
            self.excel_db.write_table('user_ingredients', new_user_ingredients_df)
            
            current_app.logger.info(f"成功删除用户(JWT标识={jwt_user_id})的食材: {ingredient_name}(ID={ingredient_id})")
            return True
            
        except Exception as e:
            current_app.logger.error(f"删除食材时出错: {str(e)}")
            return False

    def update_ingredient(self, token_or_user_id, ingredient_id, quantity=None, expiry_date=None):
        """
        更新用户食材库中的特定食材信息
        
        Args:
            token_or_user_id: JWT令牌或用户ID
            ingredient_id: 要更新的食材ID
            quantity: 新的食材数量，不更新则传入None
            expiry_date: 新的过期日期(格式: YYYY-MM-DD)，不更新则传入None
            
        Returns:
            dict: 包含更新结果的字典，成功时返回更新后的食材信息，失败时返回None
        """
        # 如果传入的是令牌，则从令牌中提取用户ID
        if isinstance(token_or_user_id, str) and (token_or_user_id.startswith('Bearer ') or '.' in token_or_user_id):
            jwt_user_id = get_user_id_from_token(token_or_user_id)
            if not jwt_user_id:
                current_app.logger.error("无法从令牌中获取有效的用户ID")
                return None
        else:
            # 如果传入的是用户ID，则直接使用
            jwt_user_id = token_or_user_id
        
        current_app.logger.info(f"准备更新用户(JWT标识: {jwt_user_id})的食材(ID: {ingredient_id})信息")
        
        # 检查是否至少有一个需要更新的字段
        if quantity is None and expiry_date is None:
            current_app.logger.warning("没有提供需要更新的字段")
            return None
        
        try:
            # 1. 根据JWT中获取的user_id找到users表中对应的id
            users_df = self.excel_db.read_table('users')
            if users_df.empty:
                current_app.logger.warning("用户表为空，无法获取用户信息")
                return None
            
            # 确认users表中是否存在user_id列
            if 'user_id' not in users_df.columns:
                current_app.logger.warning(f"警告: users表中不存在'user_id'列！可用列: {users_df.columns.tolist()}")
                return None
            
            # 根据JWT中的user_id查找用户记录
            user_record = users_df[users_df['user_id'] == jwt_user_id]
            
            if user_record.empty:
                current_app.logger.warning(f"在users表中未找到user_id={jwt_user_id}的记录")
                # 尝试其他可能的格式转换
                if isinstance(jwt_user_id, str) and jwt_user_id.startswith('u_'):
                    # 尝试去掉前缀
                    user_id_without_prefix = jwt_user_id[2:]
                    user_record = users_df[users_df['user_id'] == user_id_without_prefix]
                    if not user_record.empty:
                        current_app.logger.info(f"通过去掉'u_'前缀找到用户记录")
                
                # 如果仍未找到记录，返回失败
                if user_record.empty:
                    current_app.logger.warning(f"在users表中未找到与JWT标识匹配的用户记录")
                    return None
            
            # 获取用户在数据库中的id (主键)
            db_user_id = user_record.iloc[0]['id']
            current_app.logger.info(f"找到用户(JWT标识={jwt_user_id})的数据库ID(主键): {db_user_id}")
            
            # 2. 获取用户食材库
            user_ingredients_df = self.excel_db.read_table('user_ingredients')
            if user_ingredients_df.empty:
                current_app.logger.warning("用户食材库表为空")
                return None
            
            # 3. 检查食材是否存在
            # 筛选当前用户的特定食材
            ingredient_to_update = user_ingredients_df[
                (user_ingredients_df['user_id'] == db_user_id) & 
                (user_ingredients_df['ingredient_id'] == ingredient_id)
            ]
            
            if ingredient_to_update.empty:
                current_app.logger.warning(f"用户(JWT标识={jwt_user_id})没有ID为{ingredient_id}的食材")
                return None
            
            # 获取食材名称（用于日志）
            ingredients_df = self.excel_db.read_table('ingredients')
            ingredient_name = "未知食材"
            ingredient_unit = ""
            if not ingredients_df.empty:
                ingredient_info = ingredients_df[ingredients_df['id'] == ingredient_id]
                if not ingredient_info.empty:
                    ingredient_name = ingredient_info.iloc[0].get('name', f"未知食材({ingredient_id})")
                    ingredient_unit = ingredient_info.iloc[0].get('unit', '')
            
            # 4. 更新食材信息
            # 找出要更新的行索引和原始数据
            index_to_update = ingredient_to_update.index[0]
            original_row = user_ingredients_df.loc[index_to_update].copy()
            
            # 记录原始值（用于日志）
            original_quantity = original_row.get('quantity', 0)
            original_expiry_date = original_row.get('expiry_date', None)
            
            # 创建更新后的行数据
            updated_row = original_row.copy()
            
            # 更新数量
            if quantity is not None:
                updated_row['quantity'] = quantity
                current_app.logger.info(f"更新食材数量: {original_quantity} -> {quantity}")
            
            # 更新过期日期
            if expiry_date is not None:
                # 尝试转换日期格式
                try:
                    # 如果传入的是字符串，转换为日期对象
                    if isinstance(expiry_date, str):
                        expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                    else:
                        expiry_date_obj = expiry_date
                    
                    updated_row['expiry_date'] = expiry_date_obj
                    
                    # 格式化日期用于日志
                    original_date_str = "无" if original_expiry_date is None or pd.isna(original_expiry_date) else (
                        original_expiry_date.strftime('%Y-%m-%d') if hasattr(original_expiry_date, 'strftime') else str(original_expiry_date)
                    )
                    new_date_str = expiry_date_obj.strftime('%Y-%m-%d')
                    current_app.logger.info(f"更新食材过期日期: {original_date_str} -> {new_date_str}")
                    
                except ValueError as e:
                    current_app.logger.error(f"无效的日期格式: {expiry_date}, 错误: {str(e)}")
                    return None
            
            # 更新DataFrame
            user_ingredients_df.loc[index_to_update] = updated_row
            
            # 保存更新后的表格
            self.excel_db.write_table('user_ingredients', user_ingredients_df)
            
            current_app.logger.info(f"成功更新用户(JWT标识={jwt_user_id})的食材: {ingredient_name}(ID={ingredient_id})信息")
            
            # 5. 构建返回结果
            # 获取当前日期，用于计算剩余天数
            today = datetime.now().date()
            
            result = {
                'id': ingredient_id,
                'name': ingredient_name,
                'quantity': updated_row['quantity'],
                'unit': ingredient_unit
            }
            
            # 添加过期日期信息（如果有）
            if 'expiry_date' in updated_row and updated_row['expiry_date'] and pd.notna(updated_row['expiry_date']):
                expiry_date_obj = updated_row['expiry_date']
                if isinstance(expiry_date_obj, pd.Timestamp):
                    expiry_date_obj = expiry_date_obj.date()
                
                # 计算与当前日期的差距（天数）
                days_until_expiry = (expiry_date_obj - today).days
                
                # 如果已经过期或当天过期，天数为0
                if days_until_expiry <= 0:
                    days_until_expiry = 0
                
                result['expiry_date'] = expiry_date_obj.strftime('%Y-%m-%d')
                result['days_until_expiry'] = days_until_expiry
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"更新食材时出错: {str(e)}")
            return None 