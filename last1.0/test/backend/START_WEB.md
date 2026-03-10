# 羽翼Pro V2 - Web界面启动指南

## 🚀 快速启动（3步）

### 步骤1：安装依赖

```bash
cd C:\Users\86187\Desktop\yuyi_pro_v2
pip install -r requirements.txt
```

**需要的依赖**：
- fastapi>=0.104.0
- uvicorn[standard]>=0.24.0
- python-multipart>=0.0.6
- websockets>=12.0
- ffmpeg-python>=0.2.0
- pydantic>=2.5.0

### 步骤2：确保ffmpeg已安装

```bash
# 测试ffmpeg是否可用
ffmpeg -version

# 如果未安装，请从以下地址下载：
# https://ffmpeg.org/download.html
# 或使用包管理器安装：
# - Windows: choco install ffmpeg
# - Mac: brew install ffmpeg
# - Linux: apt-get install ffmpeg
```

### 步骤3：启动Web服务器

```bash
# 方法1：直接运行（推荐）
python -m webapp.main

# 方法2：使用uvicorn
uvicorn webapp.main:app --host 0.0.0.0 --port 8080 --reload
```

## 🌐 访问Web界面

启动成功后，在浏览器打开：

- **主页面**: http://localhost:8080
- **API文档**: http://localhost:8080/api/docs
- **健康检查**: http://localhost:8080/health

## 📋 功能概览

### ✅ 已实现的功能

1. **项目列表页**
   - 查看所有生成的视频项目
   - 项目卡片展示（缩略图、标题、分镜数、时长、爆款分）
   - 点击项目卡片进入编辑页

2. **分镜编辑页**
   - 查看项目的所有分镜
   - 拖拽调整分镜顺序（Sortable.js）
   - 实时预览视频片段
   - 显示分镜元数据（时长、文件大小、描述等）

3. **视频导出**
   - 配置导出参数（分辨率、帧率、码率）
   - 一键合并所有分镜
   - 实时进度显示（WebSocket推送）
   - 导出完成后下载

## 🎯 使用流程

### 完整工作流程：

```
1. 生成视频分镜
   python yuyi_pro_remenbaike.py

2. 启动Web界面
   python -m webapp.main

3. 打开浏览器
   http://localhost:8080

4. 选择项目
   点击项目卡片进入编辑页

5. 调整分镜顺序
   拖拽左侧分镜列表重新排序

6. 导出完整视频
   点击"导出完整视频"按钮
   配置参数后开始导出
   等待进度条完成

7. 下载视频
   导出完成后，视频保存在项目目录中
```

## 🔧 配置说明

配置文件位置：`webapp/config.py`

```python
# 服务器配置
HOST = "0.0.0.0"    # 监听所有网络接口
PORT = 8080         # 端口号

# 目录配置
OUTPUTS_DIR = "outputs"         # 视频输出目录
STATIC_DIR = "webapp/static"    # 静态文件目录

# 导出配置
DEFAULT_RESOLUTION = "1920x1080"  # 默认分辨率
DEFAULT_FPS = 30                  # 默认帧率
DEFAULT_BITRATE = "5M"            # 默认码率
MAX_CONCURRENT_EXPORTS = 3        # 最多同时导出3个视频
```

## ⚙️ API端点列表

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/projects` | 获取所有项目列表 |
| GET | `/api/projects/{id}` | 获取项目详情 |
| GET | `/api/projects/{id}/shots` | 获取分镜列表 |
| PUT | `/api/projects/{id}/shots/reorder` | 重排序分镜 |
| POST | `/api/projects/{id}/export` | 创建导出任务 |
| GET | `/api/export/{task_id}/status` | 查询导出状态 |
| WS | `/ws/export/{task_id}` | 导出进度推送 |

## 🐛 故障排查

### 问题1：端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 更改端口
uvicorn webapp.main:app --port 8888

# 或关闭占用8080端口的程序
netstat -ano | findstr :8080
taskkill /PID <进程ID> /F
```

### 问题2：ffmpeg未找到

**错误**: `ffmpeg: command not found`

**解决**: 安装ffmpeg
```bash
# Windows (使用Chocolatey)
choco install ffmpeg

# 或手动下载并添加到PATH
https://ffmpeg.org/download.html
```

### 问题3：视频文件无法播放

**原因**: 浏览器不支持视频格式或路径错误

**解决**:
- 确保outputs目录存在且包含视频文件
- 检查视频文件权限
- 尝试不同的浏览器（推荐Chrome/Edge）

### 问题4：导出失败

**原因**: ffmpeg参数错误或文件权限问题

**解决**:
- 检查ffmpeg是否正确安装
- 查看日志文件：`logs/webapp.log`
- 确保项目目录有写入权限

## 📊 性能优化

### 提高导出速度

在 `video_merger.py` 中调整ffmpeg参数：

```python
# 使用更快的编码预设
"-preset", "fast",  # ultrafast/superfast/veryfast/faster/fast

# 降低质量以换取速度
"-crf", "28",  # 18-28，数值越大速度越快但质量越低
```

### 减少内存占用

在 `config.py` 中调整并发数：

```python
MAX_CONCURRENT_EXPORTS = 1  # 同时只导出1个视频
```

## 📝 日志文件

日志保存位置：`logs/webapp.log`

```bash
# 查看实时日志
tail -f logs/webapp.log

# 查看错误日志
grep ERROR logs/webapp.log
```

## 🎓 技术栈

- **后端**: FastAPI + Python 3.8+
- **前端**: Vue 3 + Element Plus + Sortable.js
- **视频处理**: ffmpeg-python
- **WebSocket**: 实时进度推送
- **日志**: loguru

## 💡 提示

1. **第一次使用前**，确保至少生成一个视频项目
2. **导出大视频**（>30个分镜）可能需要几分钟
3. **修改分镜顺序后**会自动保存到metadata.json
4. **导出的视频**保存在项目目录下，文件名可自定义

## 📞 需要帮助？

查看完整文档：
- `README_WEB.md` - 详细使用说明
- `EXAMPLES.md` - 代码示例
- `/api/docs` - API文档（在线）

---

**祝您使用愉快！🎉**
