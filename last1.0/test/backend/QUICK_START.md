# ⚡ 快速开始指南

> 5分钟启动羽翼Pro V2的关键帧生成功能

---

## 🎯 3步开始

### 步骤1：配置API Key（1分钟）

**Windows（临时）**：
```bash
set NANOBANANA_API_KEY=your_api_key_here
```

**Linux/Mac（临时）**：
```bash
export NANOBANANA_API_KEY=your_api_key_here
```

> 📝 **获取API Key**：联系热梦百科API平台 https://api.remenbaike.com

### 步骤2：启动服务器（30秒）

```bash
# 确保在项目根目录
cd C:\Users\86187\Desktop\yuyi_pro_v2

# 启动Web服务器
python -m webapp.main
```

看到以下输出表示成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     羽翼Pro V2 Web服务器启动中...
```

### 步骤3：访问并测试（3分钟）

1. 打开浏览器：`http://localhost:8080`
2. 选择一个项目（如果没有，先用命令行生成）
3. 点击"生成关键帧"按钮
4. 等待生成完成（约3-5分钟，12个分镜）
5. 查看九宫格预览
6. 点击任意关键帧查看3个版本
7. 选择最佳版本并批准

**成功！** 🎉

---

## 🔧 常见问题速查

### Q: 提示"NANOBANANA_API_KEY未设置"

**A**: API Key未配置，按步骤1重新设置

### Q: 页面打不开

**A**: 检查端口8080是否被占用：
```bash
# Windows
netstat -ano | findstr :8080

# Linux/Mac
lsof -i :8080
```

### Q: 生成失败

**A**: 查看日志：
```bash
tail -f logs/webapp.log
```

### Q: API Key在哪获取？

**A**: 联系热梦百科API平台：
- API平台：https://api.remenbaike.com
- 文档：https://s.apifox.cn/apidoc/docs-site/5479336

---

## 📚 详细文档

- 📖 **完整配置指南**：`API_SETUP_GUIDE.md`
- 📊 **功能实现总结**：`P0_P1_P2_IMPLEMENTATION_COMPLETE.md`
- 🔧 **环境变量配置**：`.env.example`

---

## 💡 下一步

配置完成后，您可以：

1. ✅ 生成关键帧预览
2. ✅ 重新生成不满意的关键帧
3. ✅ 查看AI质量评分
4. ✅ 选择多个版本
5. ⏳ 图生视频（待实现）

**立即开始您的AI视频创作之旅！** 🚀
