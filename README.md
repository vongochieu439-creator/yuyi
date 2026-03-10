# Yuyi · AI 视频生成与编辑系统

Yuyi 是一个端到端的 **AI 视频生成与编辑系统**，包含 Python 后端服务、Web 管理界面（FastAPI + Vue3）、以及一套完整的视频生成流水线与测试脚本。

本项目适合作为：

- AI 视频生成/多模态内容创作的参考实现
- 学习 FastAPI + Vue3 + Vite 的全栈示例
- 本地化运行的工具型应用（提供 CLI 与 Web UI 两种使用方式）

---

## 功能概览

- **AI 视频生成流水线**
  - 通过脚本一键生成多段视频片段
  - 支持从“产品配置 / 文案 / 模板”生成完整视频
- **Web 管理后台（Yuyi Web）**
  - 通过浏览器管理项目、镜头（shots）、模板等资源
  - 在线查看、编辑生成结果
- **后端 API 服务**
  - 基于 FastAPI 提供标准化 HTTP API
  - 自带 `/health` 健康检查与 `/api/docs` Swagger 文档
- **测试与验证**
  - 视频生成流水线测试脚本
  - 后端 API 端到端测试
  - 后端 + 前端联调的 e2e 测试脚本

---

## 技术栈

**后端 Backend（`last1.0/test/backend`）**

- 语言：Python 3.8+
- Web 框架：FastAPI + Uvicorn
- 主要依赖：
  - `ffmpeg-python`：视频处理
  - `pydantic`：数据模型
  - `httpx`、`websockets` 等网络组件
  - `loguru`：日志
  - 详见：`last1.0/test/backend/requirements.txt`

**前端 Frontend（`last1.0/test/frontend`）**

- 语言：TypeScript
- 框架与工具：
  - Vue 3
  - Vue Router
  - Pinia
  - Element Plus
  - Vite
- 包管理：npm（使用 `package-lock.json`）

---

## 目录结构（简要）

> 只列出与运行/开发最相关的部分，实际目录会更丰富。

```text
last1.0/
  test/
    backend/           # Python 后端与 Web API
      webapp/          # FastAPI Web UI 入口
      config.py        # 全局配置
      yuyi_pro.py      # 核心视频生成脚本（CLI）
      yuyi_pro_remenbaike.py  # 示例脚本/场景
      requirements.txt
      build.bat        # 使用 PyInstaller 打包为 exe
      START_WEB.md     # 启动 Web UI 的说明
      TESTING_GUIDE.md # 测试说明
      e2e_test.py      # 后端+前端端到端测试
    frontend/          # Vue3 + Vite 前端
      package.json
      src/main.ts      # 前端入口
    test_video_pipeline.py    # 视频生成流水线测试
