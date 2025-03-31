import os
import uuid
import base64
import re
from flask import current_app
from werkzeug.utils import secure_filename

def save_base64_image(base64_data):
    """
    保存Base64编码的图像数据
    
    Args:
        base64_data: Base64编码的图像数据
        
    Returns:
        str: 保存后的图像URL
    """
    # 验证Base64格式
    if not base64_data or not isinstance(base64_data, str):
        raise ValueError("无效的Base64图像数据")
        
    # 解析Base64数据
    matches = re.match(r'^data:image/(\w+);base64,(.+)$', base64_data)
    if not matches:
        raise ValueError("无效的Base64图像格式")
        
    image_ext = matches.group(1)
    image_data = matches.group(2)
    
    # 生成唯一文件名
    filename = f"{uuid.uuid4().hex}.{image_ext}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # 保存图像文件
    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(image_data))
    
    # 返回可访问的URL
    return f"/static/avatars/{filename}"

def process_avatar_file(file):
    """
    处理上传的头像文件
    
    Args:
        file: 上传的文件对象
        
    Returns:
        str: 保存后的图像URL
    """
    if not file:
        raise ValueError("未提供文件")
        
    # 验证文件类型
    filename = secure_filename(file.filename)
    if not filename or '.' not in filename:
        raise ValueError("无效的文件名")
        
    file_ext = filename.rsplit('.', 1)[1].lower()
    if file_ext not in ['jpg', 'jpeg', 'png', 'gif']:
        raise ValueError("不支持的图像格式")
    
    # 生成唯一文件名
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
    
    # 保存文件
    file.save(file_path)
    
    # 返回可访问的URL
    return f"/static/avatars/{new_filename}" 