import json
from datetime import datetime

class Recipe:
    """菜谱模型"""
    
    def __init__(self, id=None, name=None, cook_time=None, calories=None, 
                 image=None, description=None, difficulty=None, steps=None, 
                 created_at=None, updated_at=None, ingredients=None, tools=None, 
                 prep_steps=None, tips=None, tags=None):
        """
        初始化菜谱对象
        
        Args:
            id: 菜谱ID
            name: 菜谱名称
            cook_time: 烹饪时间(分钟)
            calories: 卡路里
            image: 菜谱图片URL
            description: 菜谱描述
            difficulty: 难度等级(1-5)
            steps: 烹饪步骤列表，每个步骤包含step(序号)和desc(描述)
            created_at: 创建时间
            updated_at: 更新时间
            ingredients: 所需食材列表，每个食材包含id、name、quantity和unit
            tools: 所需工具列表，每个工具包含name和desc(可选)
            prep_steps: 预处理步骤列表，每个步骤包含step(序号)和desc(描述)
            tips: 烹饪小贴士
            tags: 菜谱标签列表
        """
        self.id = id
        self.name = name
        self.cook_time = cook_time
        self.calories = calories
        self.image = image
        self.description = description
        self.difficulty = difficulty
        self.steps = steps or []
        self.created_at = created_at
        self.updated_at = updated_at
        self.ingredients = ingredients or []
        self.tools = tools or []
        self.prep_steps = prep_steps or []
        self.tips = tips
        self.tags = tags or []
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建菜谱对象
        
        Args:
            data: 包含菜谱数据的字典
            
        Returns:
            Recipe: 菜谱对象
        """
        # 预处理数值字段
        cook_time = data.get('cook_time')
        calories = data.get('calories')
        difficulty = data.get('difficulty')
        
        # 尝试转换cook_time为数值
        if cook_time is not None:
            try:
                cook_time = float(cook_time) if isinstance(cook_time, str) else cook_time
            except (ValueError, TypeError):
                pass  # 保持原值
                
        # 尝试转换calories为数值
        if calories is not None:
            try:
                calories = float(calories) if isinstance(calories, str) else calories
            except (ValueError, TypeError):
                pass  # 保持原值
                
        # 尝试转换difficulty为数值
        if difficulty is not None and isinstance(difficulty, str) and difficulty.isdigit():
            try:
                difficulty = int(difficulty)
            except (ValueError, TypeError):
                pass  # 保持原值
                
        # 预处理食材列表中的数量字段
        ingredients = data.get('ingredients')
        if ingredients:
            for ing in ingredients:
                if 'quantity' in ing:
                    try:
                        ing['quantity'] = float(ing['quantity']) if isinstance(ing['quantity'], str) else ing['quantity']
                    except (ValueError, TypeError):
                        ing['quantity'] = 0
        
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            cook_time=cook_time,
            calories=calories,
            image=data.get('image'),
            description=data.get('description'),
            difficulty=difficulty,
            steps=data.get('steps'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            ingredients=ingredients,
            tools=data.get('tools'),
            prep_steps=data.get('prep_steps'),
            tips=data.get('tips'),
            tags=data.get('tags')
        )
    
    def to_dict(self):
        """
        将菜谱对象转换为字典
        
        Returns:
            dict: 菜谱数据字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'cook_time': self.cook_time,
            'calories': self.calories,
            'image': self.image,
            'description': self.description,
            'difficulty': self.difficulty,
            'steps': self.steps,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'ingredients': self.ingredients,
            'tools': self.tools,
            'prep_steps': self.prep_steps,
            'tips': self.tips,
            'tags': self.tags
        }
    
    def to_response_dict(self):
        """
        将菜谱对象转换为API响应格式的字典
        
        Returns:
            dict: API响应格式的菜谱数据
        """
        # 获取基本字段
        result = self.to_dict()
        
        # 确保数值型字段是数值类型
        # 转换cook_time
        if result.get('cook_time') is not None:
            try:
                result['cook_time'] = float(result['cook_time']) if isinstance(result['cook_time'], str) else result['cook_time']
                result['cook_time'] = int(result['cook_time'])  # 烹饪时间应为整数
            except (ValueError, TypeError):
                pass  # 保持原值
                
        # 转换calories
        if result.get('calories') is not None:
            try:
                result['calories'] = float(result['calories']) if isinstance(result['calories'], str) else result['calories']
            except (ValueError, TypeError):
                pass  # 保持原值
                
        # 转换difficulty
        if result.get('difficulty') is not None:
            try:
                if isinstance(result['difficulty'], str) and result['difficulty'].isdigit():
                    result['difficulty'] = int(result['difficulty'])
            except (ValueError, TypeError):
                pass  # 保持原值
        
        # 确保食材列表完整保留所有属性，包括库存状态
        if self.ingredients:
            # 确保食材数量是数值类型
            for ing in result['ingredients']:
                if 'quantity' in ing:
                    try:
                        ing['quantity'] = float(ing['quantity']) if isinstance(ing['quantity'], str) else ing['quantity']
                    except (ValueError, TypeError):
                        ing['quantity'] = 0
        
        # 确保明确返回tools字段
        if self.tools is None:
            result['tools'] = []
        else:
            result['tools'] = self.tools
            
        # 确保明确返回prep_steps字段
        if self.prep_steps is None:
            result['prep_steps'] = []
        else:
            result['prep_steps'] = self.prep_steps
            
        # 确保明确返回tips字段
        result['tips'] = self.tips
        
        # 确保每个字段在返回前转换为适合API响应的格式
        # 例如：将None转为[]或适当的默认值
        for field in ['steps']:
            if result.get(field) is None:
                result[field] = []
                
        return result 