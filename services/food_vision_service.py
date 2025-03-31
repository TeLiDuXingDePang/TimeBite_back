import requests
import base64
import json
import os
import imghdr
from flask import current_app
from io import BytesIO

class FoodVisionService:
    """食物图像识别服务"""
    
    def __init__(self):
        # 豆包视觉模型API设置将从应用配置中获取
        pass
    
    def analyze_food_image(self, image_data):
        """
        分析食物图片并识别食材和数量
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            dict: 包含识别结果的字典
        """
        try:
            # 从当前应用配置中获取API设置
            api_url = current_app.config.get('DOUBAO_API_URL')
            model = current_app.config.get('DOUBAO_MODEL')
            api_key = current_app.config.get('DOUBAO_API_KEY')
            
            # 将图片数据转换为Base64编码
            if isinstance(image_data, BytesIO):
                image_bytes = image_data.getvalue()
            else:
                image_bytes = image_data
            
            # 检测图片类型
            image_type = imghdr.what(None, h=image_bytes)
            current_app.logger.info(f"检测到图片类型: {image_type}")
            
            # 如果无法检测到图片类型，默认设为jpeg
            if not image_type:
                image_type = 'jpeg'
                current_app.logger.warning("无法检测图片类型，默认使用jpeg")
            
            # 转换为Base64编码
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # 构建正确的数据URI
            data_uri = f"data:image/{image_type};base64,{base64_image}"
            current_app.logger.info(f"使用MIME类型: image/{image_type}")
            
            # 构建请求头
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            # 构建请求体，使用新的提示词
            prompt = """请执行以下分步骤任务：

1. 食材识别与分析：
- 精确识别图片中的所有可见食材
- 对每种食材给出准确的数量（不使用"大约"、"适量"等模糊描述）
- 数量和单位分开表示，如数量"2"，单位"个"
- 对每种食材的置信度进行百分比评估
- 预估每种食材的保存时间（以天为单位的整数，不带单位）

2. 创意内容生成（为每种食材添加）：
- 趣味事实：1句与食材相关的冷知识
- 厨房妙招：1条实用处理建议（不超过15字）
- 表情符号：添加1个最匹配的emoji
- 健康贴士：1句营养价值的简短说明

3. 菜肴推荐：
- 根据识别的食材推荐1-5个适合的菜肴
- 食材数量少就少推荐（1-2个），食材数量多就多推荐（3-5个）
- 为每个菜肴提供名称和与当前食材的匹配度百分比

4. 最终输出格式要求：
{
  "ingredients": [
    {
      "name": "番茄",
      "quantity": 2,
      "unit": "个",
      "confidence": "92%",
      "storage_days": 7,
      "fun_fact": "番茄最初被欧洲人当作观赏植物，认为有毒不敢食用",
      "tip": "冷冻后更易去皮",
      "emoji": "🍅",
      "health_note": "富含番茄红素，抗氧化"
    },
    ...
  ],
  "recipes": [
    {
      "name": "西红柿炒鸡蛋",
      "match_rate": "95%"
    },
    {
      "name": "番茄牛肉汤",
      "match_rate": "80%"
    },
    ...
  ],
  "summary": "根据图片共识别出X种食材"
}

附加要求：
- 优先处理画面中央的高清食材
- 对模糊/遮挡食材标注"可能为XX"
- 若识别到不常见食材，添加简要说明
- 数量必须是精确的数字，不是字符串，不使用模糊表达
- 保存时间(storage_days)必须是精确的天数，整数形式
- 根据识别的食材数量，提供合适数量的菜谱推荐（1-5个）
- 每个推荐菜谱都必须提供名称和匹配度"""
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_uri
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # 发送请求到豆包视觉模型API
            current_app.logger.info("正在发送请求到豆包视觉模型API...")
            response = requests.post(api_url, headers=headers, json=payload)
            
            # 检查响应状态
            if response.status_code != 200:
                current_app.logger.error(f"豆包API请求失败，状态码: {response.status_code}, 响应: {response.text}")
                return {"error": f"API请求失败: {response.status_code}", "details": response.text}
            
            # 解析响应数据
            response_data = response.json()
            current_app.logger.info("收到豆包API响应")
            
            # 获取AI的回复内容
            ai_content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 从回复中提取JSON数据
            try:
                # 尝试从回复中提取JSON格式的数据
                import re
                json_match = re.search(r'\{.*\}', ai_content, re.DOTALL)
                if json_match:
                    ingredients_data = json.loads(json_match.group(0))
                    return {
                        "success": True,
                        "ingredients": ingredients_data.get('ingredients', []),
                        "recipes": ingredients_data.get('recipes', []),
                        "summary": ingredients_data.get('summary', '')
                    }
                else:
                    # 如果无法提取JSON，返回原始文本
                    return {
                        "success": True,
                        "raw_response": ai_content,
                        "ingredients": []
                    }
            except Exception as e:
                current_app.logger.error(f"解析AI回复为JSON失败: {str(e)}")
                return {
                    "success": True,
                    "error": "解析结果失败",
                    "raw_response": ai_content,
                    "ingredients": []
                }
                
        except Exception as e:
            current_app.logger.error(f"食物识别过程中发生错误: {str(e)}")
            return {"error": f"食物识别失败: {str(e)}"} 