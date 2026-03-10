# 羽翼Pro V2 - Web管理界面使用指南

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd yuyi_pro_v2

# 安装依赖（包含Web框架）
pip install -r requirements.txt
```

### 2. 启动Web服务器

```bash
# 方法1：使用Python直接启动
python -m webapp.main

# 方法2：使用uvicorn启动（推荐）
uvicorn webapp.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. 访问Web界面

打开浏览器访问：
- **主页面**: http://localhost:8080
- **API文档**: http://localhost:8080/api/docs
- **健康检查**: http://localhost:8080/health

---

## 📋 系统要求

- Python 3.8+
- ffmpeg（用于视频合并）
- 已生成的视频项目（在`outputs/`目录）

---

## 🎯 功能说明

### 当前已实现（阶段1）

✅ **基础Web服务器**
- FastAPI后端服务
- 静态文件服务（HTML/CSS/JS）
- 视频文件服务（/videos/ 路由）
- 健康检查API

✅ **前端基础框架**
- Vue 3单页应用
- Element Plus UI组件库
- 响应式设计
- 美观的用户界面

### 即将实现

⏳ **阶段2：项目列表** （开发中）
- 查看所有视频项目
- 项目卡片展示
- 基本信息展示（分镜数、时长、爆款分）

⏳ **阶段3：分镜编辑**
- 分镜列表展示
- 拖拽调整顺序
- 视频预览播放

⏳ **阶段4：视频导出**
- 配置导出参数
- 一键合并视频
- 实时进度显示

---

## 🔧 配置说明

配置文件：`webapp/config.py`

```python
# Web服务器配置
HOST = "0.0.0.0"    # 监听地址
PORT = 8080         # 监听端口

# 目录配置
OUTPUTS_DIR = "outputs"  # 视频输出目录
STATIC_DIR = "webapp/static"  # 静态文件目录

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "logs/webapp.log"
```

---

## 📁 目录结构

```
yuyi_pro_v2/
├── webapp/                      # Web应用
│   ├── __init__.py
│   ├── main.py                  # FastAPI主程序
│   ├── config.py                # 配置文件
│   │
│   ├── api/                     # API路由（待实现）
│   │   └── __init__.py
│   │
│   ├── services/                # 业务逻辑（待实现）
│   │   └── __init__.py
│   │
│   ├── models/                  # 数据模型（待实现）
│   │   └── __init__.py
│   │
│   └── static/                  # 前端文件
│       ├── index.html           # 主页面
│       ├── css/
│       │   └── app.css          # 样式文件
│       └── js/
│           └── app.js           # Vue应用
│
├── outputs/                     # 视频输出目录
│   └── video_*/                 # 视频项目
│
└── requirements.txt             # 依赖文件
```

---

## 🐛 故障排查

### 问题1：服务器启动失败

**错误**: `ModuleNotFoundError: No module named 'fastapi'`

**解决**:
```bash
pip install -r requirements.txt
```

### 问题2：静态文件无法访问

**错误**: 404 Not Found

**解决**: 确保`webapp/static/`目录存在，包含index.html文件

### 问题3：视频文件无法播放

**错误**: 403 Forbidden 或 404 Not Found

**解决**:
- 确保`outputs/`目录存在
- 确保视频文件权限正确
- 检查浏览器控制台错误信息

### 问题4：端口被占用

**错误**: `[Errno 10048] error while attempting to bind on address`

**解决**:
```bash
# 更改端口
uvicorn webapp.main:app --port 8888

# 或关闭占用8080端口的程序
netstat -ano | findstr :8080
taskkill /PID <进程ID> /F
```

---

## 📝 开发日志

### 2026-02-08

✅ **阶段1完成：基础Web服务器**
- 创建FastAPI应用
- 配置静态文件服务
- 创建Vue前端骨架
- 集成Element Plus UI
- 添加健康检查API

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

开发环境设置：
```bash
git clone <repo>
cd yuyi_pro_v2
pip install -r requirements.txt
uvicorn webapp.main:app --reload  # 启动开发服务器
```

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [Vue 3](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI组件库
- [Sortable.js](https://sortablejs.github.io/Sortable/) - 拖拽库

---

Made with ❤️ by YuyiPro Team | 2026-02-08
