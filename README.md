# 🔥 YuqueSync

YuqueSync 是一个支持语雀文档本地同步的工具，支持 Windows、Mac 和 Linux。它不仅可以下载文档，还能持续追踪文档更新，确保本地内容与语雀保持同步。


❤️ 喜欢 YuqueSync? 给它一个星星 🌟 或者赞助来支持开发！

# 🚀 快速开始

## Docker 运行（推荐）

### 1. 获取语雀凭证

1. 打开浏览器，登录语雀
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面，找到任意一个请求
5. 在请求头中找到：
   - `yuque_ctoken`: 这是你的 YUQUE_TOKEN
   - `_yuque_session`: 这是你的 YUQUE_SESSION

### 2. 运行容器

```bash
# 方式一：直接运行
docker run -d \
  --name yuque-sync \
  --restart always \
  -e YUQUE_TOKEN="你的token" \
  -e YUQUE_SESSION="你的session" \
  -v /path/to/save:/data \
  yuque-sync

# 方式二：使用 docker-compose
# 1. 编辑 docker-compose.yaml 中的环境变量
# 2. 修改 volumes 中的本地路径
# 3. 运行：
docker-compose up -d
```

### 3. 环境变量说明

| 环境变量 | 必需 | 默认值 | 说明 |
|---------|------|--------|------|
| `YUQUE_TOKEN` | ✅ | - | 语雀 Token |
| `YUQUE_SESSION` | ✅ | - | 语雀 Session |
| `YUQUE_BASE_URL` | ❌ | `https://www.yuque.com` | 语雀网站地址 |
| `SAVE_PATH` | ❌ | `/data` | 文档保存路径 |
| `MONITOR_INTERVAL_MINUTES` | ❌ | `10` | 同步间隔（分钟） |

## 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
export YUQUE_TOKEN="你的token"
export YUQUE_SESSION="你的session"
export SAVE_PATH="./downloads"

# 3. 运行
python main.py download  # 单次下载
python main.py monitor   # 持续监控
```

# 🌟 主要特性

1. **全面的同步功能**:
   * 🔄 实时同步更新
   * 📄 支持 Markdown、PDF、Word 等多种格式
   * 🗂️ 支持同步整个知识库
   * 🔍 智能检测文档变更
   
2. **文档处理功能**:
   * 📝 保持原文档格式
   * 🔄 保留元数据

3. **便捷的使用体验**:
   * 🖥️ 跨平台支持 Windows、Mac 和 Linux
   * 📦 开箱即用，无需复杂配置
   * 🎨 支持浅色/深色主题
   * 💾 文档备份功能
   * 🐳 Docker 容器化部署

# 📝 待办事项

- [ ] 支持更多文档格式
- [ ] 同步进度显示优化
- [ ] 支持自定义同步模板
- [ ] 批量同步优化
- [ ] Bug 修复和改进 (进行中...)
- [ ] 插件功能支持
- [ ] 浏览器扩展
- [ ] 移动端支持
- [ ] 数据同步支持自定义内容


# 🤝 贡献指南

我们欢迎对 YuqueSync 的贡献！以下是一些贡献方式：

1. **贡献代码**: 开发新功能或优化现有代码
2. **修复 Bug**: 提交你发现的任何 bug 修复
3. **维护 Issues**: 帮助管理 GitHub issues
5. **编写文档**: 改进用户手册和指南

## 开始贡献

1. **Fork 仓库**: Fork 并克隆到本地
2. **创建分支**: 为你的修改创建新分支
3. **提交更改**: 提交并推送你的更改
4. **创建 Pull Request**: 描述你的更改和原因

感谢你的支持和贡献！

# 📃 许可证

[MIT License](https://opensource.org/license/mit)
