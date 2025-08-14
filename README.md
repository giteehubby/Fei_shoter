# 飞书笔记转小红书图文工具

这是一个自动化工具，可以将飞书笔记转换为小红书图文内容，支持自动截图与AI文案生成。

> 重要说明：当前版本仅实现以下功能：
> - 自动对飞书笔记进行完整截图
> - 基于笔记内容生成小红书风格文案（可选）
>
> 小红书的“自动发布”功能尚未实现。请将生成的图片与文案手动在小红书发布。

## 功能特性

- 🔄 **自动截图**: 按指定比例自动截取飞书笔记的完整内容
- 🤖 **AI文案生成**: 调用大模型接口根据笔记内容生成小红书风格文案
- 📝 **草稿保存**: 生成的内容会保存为草稿文件，方便手动编辑
- 🔄 **批量处理**: 支持批量处理多个飞书笔记
- ⚙️ **灵活配置**: 支持自定义截图尺寸、重叠比例等参数
- 🗓️ **计划中**: 自动发布到小红书平台（尚未实现）

## 安装要求

- Python 3.7+
- Chrome浏览器
- 飞书账号
- OpenAI API Key（可选，用于AI文案生成）

## 安装步骤

1. 克隆或下载项目文件
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量（可选）：
   ```bash
   # 复制示例配置文件
   cp env_example.txt .env
   
   # 编辑 .env 文件，填入你的账号信息
   ```

4. 运行前端应用：
   ```bash
   streamlit run app.py
   ```

## 配置说明

在 `.env` 文件中配置以下信息（均为可选）：

```env
# 飞书账号配置（如需登录受限文档）
FEISHU_EMAIL=your_email@example.com
FEISHU_PASSWORD=your_password

# OpenAI API配置（用于AI生成文案）
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

## 使用方法

### 前端应用（推荐）

启动基于 Streamlit 的前端界面：
```bash
streamlit run app.py
```
在页面中填写：
- 笔记网址：飞书云文档 / Wiki 链接
- 截图宽高比 r（宽/高）：例如 9:16 ≈ 0.5625；程序会以浏览器默认宽度，按 r 计算高度
- 使用 AI（可选）：勾选后填写 `api_key` 与 `base_url`
- 输出目录、截图目录（可按需修改）

点击“开始处理”后，应用会：
1) 自动对笔记进行整页截图（按 r 调整窗口高度）
2) 可选地调用 AI 生成小红书风格文案
3) 展示截图预览，保存草稿到 `output/`

> 说明：当前不支持自动发布到小红书，请将生成的截图与文案手动发布。

### 命令行（基础）

```bash
# 处理单个飞书笔记（默认生成截图与草稿）
python main.py "https://your-feishu-note-url.com"

# 不使用AI生成文案
python main.py "https://your-feishu-note-url.com" --no-ai
```

### 批量处理

1. 创建URL列表文件 `urls.txt`：
   ```
   https://feishu-note-1.com
   https://feishu-note-2.com
   https://feishu-note-3.com
   ```

2. 执行批量处理：
   ```bash
   python main.py --batch urls.txt
   ```

## 输出文件

- `screenshots/`: 原始截图文件
- `output/`: 优化后的图片和草稿文件
- `logs/`: 运行日志文件

## 当前限制

- 小红书自动发布功能尚未实现；请使用工具生成的图片和文案手动到小红书发布。
- 飞书页面内容存在懒加载时，首次处理可能需要额外时间以滚动加载完整内容。

## 故障排除

### OpenAI API 版本问题

如果遇到以下错误：
```
You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0
```

**解决方案**：
1. 确保使用最新版本的代码（已修复此问题）
2. 或者降级到旧版本：
   ```bash
   pip install openai==0.28
   ```

### 测试AI功能

运行测试脚本验证AI功能：
```bash
python test_ai_fix.py
```

### 示例使用

查看AI功能使用示例：
```bash
python example_ai_usage.py
```

## 注意事项

1. **账号安全**: 请妥善保管账号，不要将 `.env` 文件提交到版本控制系统
2. **功能范围**: 当前不支持自动发布到小红书，请手动发布
3. **API限制**: 使用AI功能时请注意OpenAI API的使用限制和费用
4. **浏览器兼容**: 确保Chrome浏览器版本与ChromeDriver兼容

## 开发说明

### 项目结构

```
fei2hong/
├── app.py                 # 前端应用（Streamlit）
├── main.py                # 命令行入口（基础）
├── config.py              # 配置管理
├── feishu_screenshot.py   # 飞书截图模块（支持 r=宽/高）
├── ai_summary.py          # AI文案生成模块
├── xiaohongshu_poster.py  # 小红书发布模块（开发中，未实现自动发布）
├── requirements.txt       # 依赖包列表
├── env_example.txt        # 环境变量示例
└── README.md              # 说明文档
```

### 自定义配置

可以在 `config.py` 中修改以下配置：

- 截图默认宽/高（当未提供 r 时使用）
- 浏览器设置
- 文案长度限制
- 文件路径配置

## 许可证

本项目仅供学习和个人使用，请遵守相关平台的使用条款。

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。 