from flask import jsonify, Blueprint, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.food_vision_service import FoodVisionService
import os
import imghdr

class FoodVisionController:
    """食物图像识别控制器"""
    
    def __init__(self, excel_db=None):
        self.food_vision_service = FoodVisionService()
        self.excel_db = excel_db
        
    def init_routes(self, blueprint):
        """初始化路由"""
        blueprint.route('/analyze', methods=['POST'])(self.analyze_food_image)
        
    @jwt_required()
    def analyze_food_image(self):
        """
        分析上传的食物图片，识别食材和数量
        """
        try:
            # 获取当前用户ID (从JWT获取的身份标识)
            jwt_identity = get_jwt_identity()
            current_app.logger.info(f"用户JWT标识: {jwt_identity} 请求食物图像分析")
            
            # 检查请求中是否包含文件
            if 'food_image' not in request.files:
                current_app.logger.warning(f"用户 {jwt_identity} 未提供食物图片")
                return jsonify({
                    'code': 400,
                    'message': '未提供食物图片',
                    'data': None
                }), 400
                
            # 获取上传的文件
            food_image = request.files['food_image']
            
            # 检查文件名是否为空
            if food_image.filename == '':
                current_app.logger.warning(f"用户 {jwt_identity} 提供的食物图片文件名为空")
                return jsonify({
                    'code': 400,
                    'message': '食物图片文件名为空',
                    'data': None
                }), 400
                
            # 从文件名检测扩展名
            file_ext = ""
            if '.' in food_image.filename:
                file_ext = food_image.filename.rsplit('.', 1)[1].lower()
                current_app.logger.info(f"上传文件扩展名: {file_ext}")
            
            # 检查文件扩展名是否允许
            allowed_extensions = {'png', 'jpg', 'jpeg'}
            if not file_ext or file_ext not in allowed_extensions:
                current_app.logger.warning(f"用户 {jwt_identity} 提供的文件类型不允许，文件名: {food_image.filename}")
                return jsonify({
                    'code': 400,
                    'message': '只允许上传PNG、JPG或JPEG格式的图片',
                    'data': None
                }), 400
                
            # 读取图片数据
            image_data = food_image.read()
            
            # 使用imghdr检测实际图片类型
            actual_type = imghdr.what(None, h=image_data)
            current_app.logger.info(f"实际检测到的图片类型: {actual_type}")
            
            # 验证实际图片类型是否与扩展名匹配或是否为允许的类型
            if actual_type not in ['jpeg', 'jpg', 'png']:
                current_app.logger.warning(f"用户 {jwt_identity} 提供的文件实际类型不允许: {actual_type}")
                return jsonify({
                    'code': 400,
                    'message': f'图片内容类型 {actual_type} 不支持，只允许JPEG或PNG格式',
                    'data': None
                }), 400
            
            # 调用服务分析图片
            result = self.food_vision_service.analyze_food_image(image_data)
            
            # 检查分析结果
            if 'error' in result:
                current_app.logger.error(f"用户 {jwt_identity} 的食物图像分析失败: {result['error']}")
                return jsonify({
                    'code': 500,
                    'message': f"食物图像分析失败: {result['error']}",
                    'data': None
                }), 500
                
            # 检查识别结果
            ingredients = result.get('ingredients', [])
            recipes = result.get('recipes', [])
            summary = result.get('summary', '')
            
            if not ingredients and 'raw_response' in result:
                # 如果没有结构化的食材信息，但有原始响应
                current_app.logger.info(f"用户 {jwt_identity} 的食物图像分析成功，但未能提取结构化食材信息")
                return jsonify({
                    'code': 200,
                    'message': '食物图像分析成功，但未能提取结构化食材信息',
                    'data': {
                        'raw_response': result['raw_response']
                    }
                })
            
            # 成功识别食材信息
            current_app.logger.info(f"用户 {jwt_identity} 的食物图像分析成功，识别到 {len(ingredients)} 种食材, 推荐 {len(recipes)} 个菜谱")
            return jsonify({
                'code': 200,
                'message': '食物图像分析成功',
                'data': {
                    'ingredients': ingredients,
                    'recipes': recipes,
                    'summary': summary,
                    'total': len(ingredients)
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"食物图像分析过程中发生错误: {str(e)}")
            return jsonify({
                'code': 500,
                'message': f"食物图像分析失败: {str(e)}",
                'data': None
            }), 500 