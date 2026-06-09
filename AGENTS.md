# AGENTS.md — AI 代理使用说明（简明）

目的
- 为代码库内的 AI 编码代理（如 Copilot）提供必要的上下文、关键命令与约定，便于快速定位可运行脚本和重要配置。

快速上手命令（关键位置：`scraper`）
- 创建与激活虚拟环境（Unix/macOS 示例）：

  cd scraper
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

- 运行抓取脚本：

  cd scraper
  python run.py

- 单独运行维基统计脚本：

  cd scraper
  python collect_wikipedia.py

重要文件与约定（Link, don’t embed）
- 项目根文档：[README.md](README.md) — 项目总体说明。
- 抓取模块：[scraper/README.md](scraper/README.md) — 包含安装、运行示例与依赖说明（优先阅读）。
- 抓取配置：[scraper/config.py](scraper/config.py) — 关键参数（keywords、max_* 等）。
- 输出目录：`scraper/output/` — 产出 JSON 文件（例如 `overseas_data.json`, `wikipedia_data.json`）。
- 资料来源：[Materials/SOURCES.md](Materials/SOURCES.md)

环境与凭证
- 抓取脚本需要外部 API 密钥（YouTube Data API v3、Reddit PRAW 等），通常通过 `.env` 或环境变量提供。在没有密钥时，代理应避免尝试真实请求并改为局部模拟或建议用户提供测试凭证。

开发约定（简短提醒）
- 优先不要修改前端 HTML/CSS（如 `index.html`、`styles.css`）除非明确要求；这些是呈现层资产。
- 对于跨模块改动，先在 `scraper` 下运行脚本并确认输出格式（JSON）保持兼容。

如果你希望，我可以：
- 将此文件合并到 `.github/copilot-instructions.md`（如果你偏好放在 .github 下）；
- 或为前端/后端分别生成更细化的 agent 指令（例如 `AGENTS_frontend.md` / `AGENTS_backend.md`）。

请告诉我你偏好的放置位置或是否需要更多细节.
