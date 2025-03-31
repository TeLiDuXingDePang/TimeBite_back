import os
import pandas as pd
from datetime import datetime
import uuid

class ExcelDatabase:
    """Excel数据库管理基类"""
    
    def __init__(self, excel_path):
        """
        初始化Excel数据库
        
        Args:
            excel_path: Excel文件路径
        """
        self.excel_path = excel_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """确保数据库文件存在，不存在则创建"""
        if not os.path.exists(self.excel_path):
            # 创建用户表
            users_df = pd.DataFrame(columns=[
                'id', 'user_id', 'openid', 'session_key', 'nickname', 
                'avatar_url', 'member_level', 'health_goal', 
                'last_login_time', 'created_at', 'updated_at'
            ])
            
            # 创建菜谱表
            recipes_df = pd.DataFrame(columns=[
                'id', 'name', 'cook_time', 'calories', 'image', 
                'description', 'steps', 'difficulty', 
                'created_at', 'updated_at'
            ])
            
            # 创建Excel文件，每个表保存为一个sheet
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                users_df.to_excel(writer, sheet_name='users', index=False)
                recipes_df.to_excel(writer, sheet_name='recipes', index=False)
        else:
            # 检查是否存在recipes表，如果不存在则创建
            try:
                with pd.ExcelFile(self.excel_path, engine='openpyxl') as xls:
                    sheet_names = xls.sheet_names
                    
                if 'recipes' not in sheet_names:
                    # 创建菜谱表
                    recipes_df = pd.DataFrame(columns=[
                        'id', 'name', 'cook_time', 'calories', 'image', 
                        'description', 'steps', 'difficulty', 
                        'created_at', 'updated_at'
                    ])
                    
                    # 读取所有现有表
                    dfs = {}
                    for sheet in sheet_names:
                        dfs[sheet] = pd.read_excel(self.excel_path, sheet_name=sheet, engine='openpyxl')
                    
                    # 添加新表并写回Excel
                    with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                        for sheet, df in dfs.items():
                            df.to_excel(writer, sheet_name=sheet, index=False)
                        recipes_df.to_excel(writer, sheet_name='recipes', index=False)
            except Exception as e:
                print(f"检查recipes表失败: {str(e)}")
    
    def read_table(self, table_name):
        """
        读取指定表的数据
        
        Args:
            table_name: 表名(sheet名)
            
        Returns:
            DataFrame: 表数据
        """
        try:
            if not os.path.exists(self.excel_path):
                print(f"Excel文件不存在: {self.excel_path}")
                return pd.DataFrame()
            
            return pd.read_excel(self.excel_path, sheet_name=table_name, engine='openpyxl')
        except Exception as e:
            print(f"读取表 {table_name} 失败: {str(e)}")
            # 返回空DataFrame
            return pd.DataFrame()
    
    def write_table(self, table_name, df):
        """
        写入数据到指定表
        
        Args:
            table_name: 表名(sheet名)
            df: 要写入的DataFrame
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(self.excel_path):
                # 如果文件不存在，直接创建新文件
                with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=table_name, index=False)
                return True
            
            # 读取所有sheet
            try:
                # 读取所有现有的sheet
                xls = pd.ExcelFile(self.excel_path, engine='openpyxl')
                sheet_names = xls.sheet_names
                
                # 读取所有sheet的数据
                all_dfs = {}
                for sheet in sheet_names:
                    if sheet != table_name:  # 不读取要更新的表
                        all_dfs[sheet] = pd.read_excel(self.excel_path, sheet_name=sheet, engine='openpyxl')
                
                # 添加或更新当前表
                all_dfs[table_name] = df
                
                # 写回所有表
                with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                    for sheet, sheet_df in all_dfs.items():
                        sheet_df.to_excel(writer, sheet_name=sheet, index=False)
                    
            except Exception as e:
                # 如果读取现有文件失败，尝试创建新文件
                print(f"读取现有Excel文件失败，创建新文件: {str(e)}")
                with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=table_name, index=False)
            
            return True
        except Exception as e:
            print(f"写入表 {table_name} 失败: {str(e)}")
            return False
    
    def find_user_by_openid(self, openid):
        """
        根据openid查找用户
        
        Args:
            openid: 微信openid
            
        Returns:
            dict: 用户信息，未找到返回None
        """
        users_df = self.read_table('users')
        if users_df.empty:
            return None
            
        user = users_df[users_df['openid'] == openid]
        if user.empty:
            return None
            
        return user.iloc[0].to_dict()
    
    def create_user(self, user_data):
        """
        创建新用户
        
        Args:
            user_data: 用户数据字典
            
        Returns:
            dict: 创建的用户信息
        """
        users_df = self.read_table('users')
        
        # 生成ID
        if users_df.empty:
            new_id = 1
        else:
            new_id = users_df['id'].max() + 1
        
        # 准备用户数据
        user_data['id'] = new_id
        if 'user_id' not in user_data:
            user_data['user_id'] = f"u_{uuid.uuid4().hex[:8]}"
        
        # 添加时间戳
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'created_at' not in user_data:
            user_data['created_at'] = now
        if 'updated_at' not in user_data:
            user_data['updated_at'] = now
        
        # 添加到DataFrame - 使用concat替代append
        new_row = pd.DataFrame([user_data])
        users_df = pd.concat([users_df, new_row], ignore_index=True)
        
        # 保存到Excel
        self.write_table('users', users_df)
        
        return user_data
    
    def update_user(self, openid, update_data):
        """
        更新用户信息
        
        Args:
            openid: 微信openid
            update_data: 要更新的数据字典
            
        Returns:
            dict: 更新后的用户信息，未找到返回None
        """
        users_df = self.read_table('users')
        if users_df.empty:
            return None
        
        # 查找用户
        user_idx = users_df[users_df['openid'] == openid].index
        if len(user_idx) == 0:
            return None
        
        # 更新时间戳
        update_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新用户数据
        for key, value in update_data.items():
            users_df.loc[user_idx[0], key] = value
        
        # 保存到Excel
        self.write_table('users', users_df)
        
        # 返回更新后的用户信息
        return users_df.loc[user_idx[0]].to_dict()
    
    def create_recipe(self, recipe_data):
        """
        创建新菜谱
        
        Args:
            recipe_data: 菜谱数据字典
            
        Returns:
            dict: 创建的菜谱信息
        """
        recipes_df = self.read_table('recipes')
        
        # 生成ID
        if recipes_df.empty:
            new_id = 1
        else:
            new_id = recipes_df['id'].max() + 1
        
        # 准备菜谱数据
        recipe_data['id'] = new_id
        
        # 添加时间戳
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'created_at' not in recipe_data:
            recipe_data['created_at'] = now
        if 'updated_at' not in recipe_data:
            recipe_data['updated_at'] = now
        
        # 添加到DataFrame
        new_row = pd.DataFrame([recipe_data])
        recipes_df = pd.concat([recipes_df, new_row], ignore_index=True)
        
        # 保存到Excel
        self.write_table('recipes', recipes_df)
        
        return recipe_data
    
    def get_all_recipes(self):
        """
        获取所有菜谱
        
        Returns:
            list: 菜谱列表
        """
        recipes_df = self.read_table('recipes')
        if recipes_df.empty:
            return []
        
        return recipes_df.to_dict('records')
    
    def get_recipe_by_id(self, recipe_id):
        """
        根据ID获取菜谱
        
        Args:
            recipe_id: 菜谱ID
            
        Returns:
            dict: 菜谱信息，未找到返回None
        """
        recipes_df = self.read_table('recipes')
        if recipes_df.empty:
            return None
        
        recipe = recipes_df[recipes_df['id'] == recipe_id]
        if recipe.empty:
            return None
        
        return recipe.iloc[0].to_dict()
    
    def update_recipe(self, recipe_id, update_data):
        """
        更新菜谱信息
        
        Args:
            recipe_id: 菜谱ID
            update_data: 要更新的数据字典
            
        Returns:
            dict: 更新后的菜谱信息，未找到返回None
        """
        recipes_df = self.read_table('recipes')
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
        self.write_table('recipes', recipes_df)
        
        # 返回更新后的菜谱信息
        return recipes_df.loc[recipe_idx[0]].to_dict()
    
    def delete_recipe(self, recipe_id):
        """
        删除菜谱
        
        Args:
            recipe_id: 菜谱ID
            
        Returns:
            bool: 是否成功
        """
        recipes_df = self.read_table('recipes')
        if recipes_df.empty:
            return False
        
        # 查找菜谱
        recipe_idx = recipes_df[recipes_df['id'] == recipe_id].index
        if len(recipe_idx) == 0:
            return False
        
        # 删除菜谱
        recipes_df = recipes_df.drop(recipe_idx)
        
        # 保存到Excel
        self.write_table('recipes', recipes_df)
        
        return True
    
    def init_sample_recipes(self):
        """初始化示例菜谱数据"""
        # 检查是否已有菜谱数据
        recipes_df = self.read_table('recipes')
        if not recipes_df.empty:
            return  # 已有数据，不再初始化
        
        # 准备示例菜谱数据
        sample_recipes = [
            {
                'name': '低脂鸡胸肉沙拉',
                'cook_time': '15分钟',
                'calories': 320,
                'image': '/static/recipes/chicken_salad.jpg',
                'description': '这是一道健康美味的低脂沙拉，富含蛋白质和多种维生素，适合减脂期间食用。',
                'steps': '[{"step": 1, "content": "将鸡胸肉切成小块，用少量盐、胡椒粉和橄榄油腌制10分钟"}, {"step": 2, "content": "平底锅中小火煎熟鸡胸肉"}, {"step": 3, "content": "将生菜、小番茄、黄瓜切好，与煎好的鸡胸肉一起放入碗中"}, {"step": 4, "content": "调制酱汁：橄榄油、柠檬汁、盐、黑胡椒混合均匀"}, {"step": 5, "content": "将酱汁淋在沙拉上，轻轻拌匀即可食用"}]',
                'difficulty': '简单',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '蒸鲈鱼配时蔬',
                'cook_time': '25分钟',
                'calories': 280,
                'image': '/static/recipes/steamed_fish.jpg',
                'description': '清蒸鲈鱼保留了鱼肉的鲜美和营养，搭配时令蔬菜，是一道低脂高蛋白的健康菜品。',
                'steps': '[{"step": 1, "content": "鲈鱼洗净，在鱼身两侧各划三刀"}, {"step": 2, "content": "鱼身抹上少量盐和料酒，腌制10分钟"}, {"step": 3, "content": "姜切丝，葱切段，部分铺在盘底，部分放在鱼身上"}, {"step": 4, "content": "蒸锅水烧开后，放入鱼，大火蒸8-10分钟"}, {"step": 5, "content": "取出后，淋上少量生抽和热油，撒上香菜即可"}]',
                'difficulty': '中等',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # 添加示例菜谱
        for recipe in sample_recipes:
            self.create_recipe(recipe)
        
        print("示例菜谱数据初始化完成")

    def ensure_table_exists(self, table_name, columns):
        """
        确保指定的表存在
        
        Args:
            table_name: 表名
            columns: 列名列表
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查表是否存在
            if not os.path.exists(self.excel_path):
                # 如果文件不存在，创建文件和表
                df = pd.DataFrame(columns=columns)
                with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=table_name, index=False)
                return True
            
            # 读取所有sheet
            try:
                xls = pd.ExcelFile(self.excel_path, engine='openpyxl')
                sheet_names = xls.sheet_names
                
                if table_name not in sheet_names:
                    # 表不存在，创建新表
                    df = pd.DataFrame(columns=columns)
                    
                    # 读取所有现有表
                    all_dfs = {}
                    for sheet in sheet_names:
                        all_dfs[sheet] = pd.read_excel(self.excel_path, sheet_name=sheet, engine='openpyxl')
                    
                    # 添加新表
                    all_dfs[table_name] = df
                    
                    # 写回所有表
                    with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                        for sheet, sheet_df in all_dfs.items():
                            sheet_df.to_excel(writer, sheet_name=sheet, index=False)
                            
                return True
            except Exception as e:
                print(f"检查表 {table_name} 是否存在失败: {str(e)}")
                return False
            
        except Exception as e:
            print(f"确保表 {table_name} 存在失败: {str(e)}")
            return False
    
    def add_row(self, table_name, row_data):
        """
        向表中添加一行数据
        
        Args:
            table_name: 表名
            row_data: 行数据（字典）
            
        Returns:
            bool: 是否成功
        """
        try:
            # 读取表数据
            df = self.read_table(table_name)
            
            # 添加新行
            new_row = pd.DataFrame([row_data])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # 写回表
            self.write_table(table_name, df)
            
            return True
        except Exception as e:
            print(f"向表 {table_name} 添加行失败: {str(e)}")
            return False 