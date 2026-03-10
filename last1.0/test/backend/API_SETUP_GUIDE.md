# 🔑 API配置指南

## 概述

羽翼Pro V2使用nanobanana API（Fal.ai平台）来生成关键帧图片。本指南将帮助您配置API密钥。

---

## 🚀 快速配置（3步完成）

### 方法1：环境变量（推荐）

#### Windows

```bash
# 临时设置（当前命令行窗口有效）
set NANOBANANA_API_KEY=your_api_key_here
set NANOBANANA_API_BASE_URL=https://api.remenbaike.com

# 启动Web服务器
python -m webapp.main
```

#### Linux/Mac

```bash
# 临时设置
export NANOBANANA_API_KEY=your_api_key_here
export NANOBANANA_API_BASE_URL=https://api.remenbaike.com

# 启动Web服务器
python -m webapp.main
```

### 方法2：.env文件

创建`.env`文件（项目根目录）：

```env
# NanoBanana API配置
NANOBANANA_API_KEY=your_api_key_here
NANOBANANA_API_BASE_URL=https://api.remenbaike.com
```

然后安装python-dotenv：

```bash
pip install python-dotenv
```

在`webapp/config.py`顶部添加：

```python
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件
```

### 方法3：直接修改config.py

打开`webapp/config.py`，找到以下部分：

```python
# NanoBanana API (Fal.ai平台 - 图片生成)
NANOBANANA_API_KEY = os.getenv("NANOBANANA_API_KEY", "")  # 从环境变量读取
NANOBANANA_API_BASE_URL = os.getenv("NANOBANANA_API_BASE_URL", "https://api.remenbaike.com")
```

直接修改为：

```python
NANOBANANA_API_KEY = "your_api_key_here"  # 替换为实际API Key
NANOBANANA_API_BASE_URL = "https://api.remenbaike.com"
```

⚠️ **注意**：不要将包含真实API Key的config.py提交到Git！

---

## 📊 API使用说明

### 支持的功能

| 端点 | 功能 | 文档 |
|------|------|------|
| `/fal-ai/nano-banana` | 文生图（关键帧生成） | [官方文档](https://fal.ai/models/fal-ai/nano-banana) |
| `/fal-ai/nano-banana/edit` | 图片编辑 | [官方文档](https://fal.ai/models/fal-ai/nano-banana/edit) |

### 请求格式

#### 文生图（关键帧生成）

```json
{
  "prompt": "A beautiful sunset over the ocean, cinematic lighting, 4K",
  "num_images": 1
}
```

#### 响应格式（异步队列）

**第一步：提交请求**

```json
{
  "status": "IN_QUEUE",
  "request_id": "e7e9202c-efb8-40f2-81c3-13b3f7aaa4ca",
  "response_url": "https://queue.fal.run/fal-ai/nano-banana/requests/...",
  "status_url": "https://queue.fal.run/fal-ai/nano-banana/requests/.../status",
  "queue_position": 0
}
```

**第二步：轮询状态（status_url）**

```json
{
  "status": "IN_PROGRESS",  // 或 "COMPLETED" / "FAILED"
  "queue_position": 0
}
```

**第三步：获取结果（response_url）**

```json
{
  "images": [
    {
      "url": "https://fal.media/files/...",
      "width": 1024,
      "height": 1024,
      "content_type": "image/jpeg"
    }
  ],
  "prompt": "...",
  "seed": 2841475369,
  "has_nsfw_concepts": [false]
}
```

### 成本计算

| 项目 | 成本 |
|------|------|
| 单张图片生成 | ¥0.05 |
| 单个视频生成（Kling） | ¥1.20 |

#### 示例成本计算

**传统方式（直接生成视频）**：
- 12个分镜 × ¥1.20 = **¥14.40**
- 如果不满意重新生成2次 = **¥43.20**

**新方式（先生成关键帧）**：
- 12个关键帧图片 × ¥0.05 = **¥0.60**
- 重新生成5个不满意的 × 3个版本 × ¥0.05 = **¥0.75**
- 批准后生成视频 12 × ¥1.20 = **¥14.40**
- **总计：¥15.75**（成功率95%+）

**成本对比**：
- 传统方式3次尝试：¥43.20
- 新方式1次成功：¥15.75
- **节省：¥27.45（64%）**

---

## 🧪 测试API配置

创建测试文件`test_nanobanana.py`：

```python
import asyncio
from webapp.services.nanobanana_client import NanoBananaClient

async def test():
    # 使用你的API Key
    client = NanoBananaClient(
        api_key="your_api_key_here",
        base_url="https://api.remenbaike.com"
    )

    # 生成测试图片
    prompt = "A beautiful sunset over the ocean, cinematic lighting, 4K"

    try:
        images = await client.generate_image(prompt, num_images=1)
        print(f"✅ 测试成功！生成图片URL: {images[0]}")
        print(f"💰 成本: ¥{client.calculate_cost(1):.2f}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test())
```

运行测试：

```bash
python test_nanobanana.py
```

---

## ⚠️ 常见问题

### Q1: API Key从哪里获取？

**A**: 联系热梦百科API平台获取：
- API平台地址：https://api.remenbaike.com
- 文档地址：https://s.apifox.cn/apidoc/docs-site/5479336

### Q2: 提示"NANOBANANA_API_KEY未设置"

**A**: 说明API Key未正确配置，请按照上述3种方法之一配置。

### Q3: 请求失败："401 Unauthorized"

**A**: API Key无效或过期，请检查：
1. API Key是否正确复制（无多余空格）
2. API Key是否有效（未过期）
3. API Key是否有足够的额度

### Q4: 请求超时

**A**: 可能原因：
1. 网络问题（检查是否能访问api.remenbaike.com）
2. 队列拥堵（等待时间过长）
3. 超时设置过短（默认5分钟）

可以在`nanobanana_client.py`中调整：

```python
async def _poll_until_complete(
    self,
    ...
    max_retries: int = 120,  # 增加到120次（10分钟）
    interval: float = 5.0
):
```

### Q5: 生成的图片不符合预期

**A**: 使用提示词优化功能：
1. 在前端点击"优化提示词"按钮
2. AI会自动增强你的提示词
3. 或者手动添加关键词：
   - 质量：`high quality, 4K, detailed`
   - 光照：`cinematic lighting, natural light`
   - 风格：`professional photography, artistic`

---

## 🔐 安全建议

### 1. 不要将API Key提交到Git

创建`.gitignore`文件：

```
# 环境变量
.env

# 配置文件（如果包含API Key）
webapp/config.py

# 日志文件
logs/
*.log
```

### 2. 使用环境变量

生产环境建议使用环境变量，而不是硬编码在代码中。

### 3. 定期轮换API Key

建议每3个月更换一次API Key，降低泄露风险。

### 4. 监控API使用量

定期检查API使用统计，发现异常及时报警。

---

## 📈 下一步

配置完成后，您可以：

1. ✅ 启动Web服务器：`python -m webapp.main`
2. ✅ 访问：`http://localhost:8080`
3. ✅ 选择项目 → 点击"生成关键帧"
4. ✅ 观察实时进度
5. ✅ 查看九宫格预览
6. ✅ 重新生成不满意的关键帧
7. ✅ 批准所有关键帧
8. ✅ 点击"图片生成视频"

---

## 💡 高级配置

### 自定义模型参数

在`webapp/config.py`中调整：

```python
# 图片生成默认配置
KEYFRAME_DEFAULT_MODEL = "nano-banana"
KEYFRAME_DEFAULT_QUALITY = "high"
KEYFRAME_ASPECT_RATIO = "16:9"
KEYFRAME_NUM_VERSIONS = 3  # 重新生成时的版本数

# 成本配置
COST_PER_IMAGE = 0.05
COST_PER_VIDEO = 1.20
```

### 启用AI评分

```python
# AI评分配置
ENABLE_AI_SCORING = True
AI_SCORE_PROVIDER = "gpt4-vision"  # 需要GPT-4 Vision API
```

### 启用提示词优化

```python
# 提示词优化配置
ENABLE_PROMPT_OPTIMIZATION = True
PROMPT_OPTIMIZER_PROVIDER = "gpt4"  # 需要GPT-4 API
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`logs/webapp.log`
2. 检查浏览器控制台（F12）
3. 查看API文档：https://s.apifox.cn/apidoc/docs-site/5479336
4. 联系技术支持

---

**配置完成后，您将拥有完整的AI视频生成工作流！** 🎉
