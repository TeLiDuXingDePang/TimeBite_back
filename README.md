# 食光机小程序后端

## 主要功能

- **用户管理**：
  - 微信小程序登录与授权
  - 用户信息更新与管理
  - 用户头像上传与存储
  - 用户健康目标设置

- **食材管理**：
  - 添加、更新、删除食材库存
  - 食材过期日期跟踪与提醒
  - 最快过期食材列表展示
  - 食材库存数量与分类管理

- **菜谱功能**：
  - 基于用户库存食材的菜谱推荐
  - 基于即将过期食材的精准菜谱匹配
  - 详细菜谱信息展示（包括步骤、用料、工具等）
  - 菜谱难度与烹饪时间计算

- **食物识别**：
  - 基于豆包AI视觉模型的食物图像识别
  - 自动提取图像中的食材信息
  - 基于识别结果的菜谱智能推荐
  - 识别结果的结构化处理

- **数据统计与分析**：
  - 食材库存统计与分类展示
  - 食材过期时间分析
  - 库存使用情况可视化

## 技术栈

- **开发语言**：Python 3
- **Web框架**：Flask
- **数据存储**：Excel数据库（pandas + openpyxl）
- **认证**：JWT（JSON Web Token）
- **API文档**：Markdown
- **AI能力**：豆包AI视觉模型API

## 目录结构

```
├── app.py                 # 应用入口文件
├── config.py              # 应用配置
├── extensions.py          # 扩展初始化
├── requirements.txt       # 项目依赖
├── controllers/           # 控制器层
├── models/                # 数据模型
├── repositories/          # 数据访问层
├── routes/                # 路由定义
├── services/              # 业务逻辑层
├── utils/                 # 工具函数
├── static/                # 静态文件（图片等）
│   ├── avatars/           # 用户头像
│   └── recipes/           # 菜谱图片
├── data/                  # 数据文件
│   └── database.xlsx      # Excel数据库文件
├── 接口文档/               # API接口文档
└── 数据库设计/             # 数据库设计文档
```

## 安装与运行

### 环境要求

- Python 3.8+
- 推荐使用虚拟环境

### 安装步骤

1. 克隆代码仓库
   ```bash
   git clone [仓库地址]
   ```

2. 创建并激活虚拟环境（可选）
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # MacOS/Linux
   source venv/bin/activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量（可选）
   ```bash
   # Windows
   set WECHAT_APPID=你的小程序AppID
   set WECHAT_SECRET=你的小程序Secret
   set DOUBAO_API_KEY=你的豆包AIAPI密钥
   
   # MacOS/Linux
   export WECHAT_APPID=你的小程序AppID
   export WECHAT_SECRET=你的小程序Secret
   export DOUBAO_API_KEY=你的豆包AIAPI密钥
   ```
   
   或创建.env文件：
   ```
   WECHAT_APPID=你的小程序AppID
   WECHAT_SECRET=你的小程序Secret
   DOUBAO_API_KEY=你的豆包AIAPI密钥
   ```

5. 运行项目
   ```bash
   python app.py
   ```
   
   服务将在 http://0.0.0.0:5000 启动

## API接口概述

### 用户相关

- `POST /api/login` - 微信小程序登录
- `PUT /api/user/profile` - 更新用户信息
- `POST /api/user/avatar` - 上传用户头像

### 食材管理

- `GET /api/ingredients` - 获取食材库存列表
- `POST /api/ingredients` - 添加食材库存
- `PUT /api/ingredients/:id` - 更新食材库存
- `DELETE /api/ingredients/:id` - 删除食材库存
- `GET /api/ingredients/expiring` - 获取即将过期食材列表
- `GET /api/ingredients/stats` - 获取食材库存统计信息

### 菜谱相关

- `GET /api/recipes/recommend` - 获取推荐菜谱
- `GET /api/recipes/:id` - 获取菜谱详情
- `GET /api/recipes/expiring-match` - 基于过期食材匹配菜谱

### 图像识别

- `POST /api/image/recognize` - 食物图像识别

详细API文档请参考 `接口文档` 目录下的相关文件。

## 数据库设计

项目使用Excel作为轻量级数据库，包含以下表格：

- 食材表 (ingredients)
- 菜谱表 (recipes)
- 菜谱食材关联表 (recipe_ingredients)
- 用户表 (users)
- 用户食材库存表 (user_ingredients)

详细数据库设计请参考 `数据库设计` 目录下的文档。

