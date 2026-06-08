# 海外平台数据抓取脚本

为「海外平台如何看敦煌」两屏（`#overseas` / `#overseas-voices`）生成**真实数据**。
脚本抓取海外平台上飞天 / Dunhuang 相关的内容与评论，统计平台分布、评论高频词
（按主题分组）、语言分布、情绪近似，并摘出代表性评论，输出一个 JSON。

> 诚实说明：本脚本只覆盖**有合法 API 的平台**——**YouTube**（Data API v3）与
> **Reddit**（PRAW）。TikTok / Instagram / X 有强反爬或付费 API，不在默认范围内
> （见文末「扩展」）。所有数字都来自**抓取样本**，不是全网总体。

## 1. 安装

用 uv（推荐）：

```bash
cd scraper
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

或用 pip：

```bash
cd scraper
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 配置密钥

```bash
cp .env.example .env      # 然后填进去
set -a; source .env; set +a   # 把变量导入当前 shell
```

- **YouTube**：[Google Cloud Console](https://console.cloud.google.com) → 新建项目 →
  启用「YouTube Data API v3」→ 凭据 → 创建 API key。免费额度约 10,000 单位/天
  （每次 search 花 100 单位，约够 100 次关键词搜索）。
- **Reddit**：[reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → create app →
  选 **script** 类型 → 拿到 client id 与 secret（免费，只读，不需登录账号）。

只配一个平台也能跑，缺哪个就跳过哪个。

## 3. 运行

平台抓取（YouTube + Reddit）：

```bash
python run.py
```

输出：`output/overseas_data.json`。

维基百科词条浏览量（免密钥，独立运行）：

```bash
python collect_wikipedia.py
```

输出：`output/wikipedia_data.json`。统计 6 个敦煌相关词条近一年的浏览量，
作为「主动检索」信号，与平台「被动刷到」对照。

调参在 [config.py](config.py)：`keywords`、`max_videos_per_keyword`、
`max_comments_per_item` 等；维基词条列表在 [collect_wikipedia.py](collect_wikipedia.py) 的 `_ARTICLES`。

## 4. 输出字段 → 页面位置

`overseas_data.json`：

| JSON 字段 | 页面位置 |
|---|---|
| `kpi.items` / `kpi.comments` / `kpi.languages` | 第一屏 KPI（相关视频 / 评论样本 / 评论语言数） |
| `engagement.total_views` / `median_views` | 第一屏 KPI「样本视频总播放」与「播放高度集中」口径 |
| `engagement.top_videos[]` | 可选，最高播放视频清单 |
| `platform_distribution[].pct` | 第一屏「平台分布」条形宽度 |
| `language_distribution[]` | 第一屏「评论语言分布」条形 |
| `word_frequency.<theme>.words` | 第二屏「高频词·按主题分组」各条 |
| `sample_comments[]` | 第二屏「代表性评论」卡片（含来源链接） |
| `sentiment` | 第二屏「评论情绪」堆叠条（VADER 近似） |

`wikipedia_data.json`：

| JSON 字段 | 页面位置 |
|---|---|
| `articles[].views` | 第二屏底部「主动检索」维基浏览量条形 |
| `total_views` | 该图标题「全语种合计」 |

> 注意：YouTube / Reddit 的 API **拿不到评论者所在国家**（没有 IP / 地理字段）。
> 所以脚本给的是**评论语言分布**，KPI 用「评论语言数」而非「评论来源国」，
> 否则属于无法核验的指标。

`meta.caveats` 里已经写好可直接放进图注的口径与局限说明。

## 5. 扩展 TikTok / Instagram / X（可选）

这些平台没有简单合法的 API：

- **TikTok**：可用 `yt-dlp` 抓单视频元数据，或第三方服务（如 Apify）批量。
- **Instagram / X**：需登录态或付费 API（X API 现为付费）。

要加平台，只需新增一个 `collect_xxx.py`，返回同样的
`(list[MediaItem], list[Comment])`（见 [models.py](models.py)），在
[run.py](run.py) 的 collector 列表里加上即可，分析与输出会自动覆盖。

## 6. 复现性

`meta` 里记录了采集日期、关键词、各平台抓取上限、去重规则（按内容 id 与评论 id）。
重跑同样参数即可复现；建议把每次的 `overseas_data.json` 连同日期一起存档。
