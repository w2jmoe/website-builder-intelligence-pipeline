# AI Usage Log

## Project Goal

自动采集 AI Website Builder 赛道竞品数据，生成可复用的 HTML 分析报告，并建立基础监控与战略洞察能力。

---

## AI-Assisted Development Process

### Step 1 - Project Scaffolding

**AI 帮助完成了什么**

- 搭建 `data/`、`scripts/`、`reports/` 目录结构
- 编写 `collect_competitors.py`：配置驱动采集、单竞品异常隔离、输出 `competitors.json`
- 编写 `generate_report.py`：读取 JSON 生成 `report.html`（概览、功能矩阵、定价/客户/技术对比）
- 生成 `requirements.txt`、`README.md`
- 竞品列表写入 `competitors_config.json`，避免硬编码进 Python 逻辑

**人工做了什么决策**

- 确定 5 个初始竞品：Lovable、Bolt、v0、Replit、Durable
- 规定输出字段结构（name、website、pricing、target_customer、core_features、technical_highlights）
- 明确要求暂不接入 AI 分析模块，先完成基础工程骨架
- 环境变量策略：不新建 template 类文件，沿用现有 `.env` 约定（本项目无 API 依赖，未涉及）

---

### Step 2 - Competitor Collection

**AI 帮助完成了什么**

- 实现基于 `requests` + BeautifulSoup 的通用 HTML 抓取
- 从 meta description、列表项、标题中提取字段
- 支持 `pricing_url` 与 `overrides` 配置扩展
- 本地跑通 5 个竞品采集并生成首版报告

**人工做了什么决策**

- 接受首版启发式抓取方案，而非为每个竞品写专用 Parser（成本与维护权衡）
- 发现功能矩阵混入大量导航项（Resources、Community、LinkedIn 等）及长营销文案后，要求提升 `core_features` 质量
- 指定黑名单词汇与 80 字符长度上限，要求最小改动、不重构采集架构

---

### Step 3 - Monitoring Pipeline

**AI 帮助完成了什么**

- 新增独立模块 `monitor.py`
- 每次采集后保存 `data/history/YYYY-MM-DD.json`
- 自动比较最近两次快照，输出 `data/change_report.json`
- 终端打印 `[CHANGED]` / `[UNCHANGED]` 日志
- 在 `collect_competitors.py` 末尾增加一行调用，不改动原有采集流程

**人工做了什么决策**

- 要求单个竞品失败不影响整体（Step 1 已确立，Monitoring 沿用同一原则）
- 明确监控字段：pricing、core_features、target_customer、technical_highlights
- 历史不足 2 份快照时跳过比较，避免误报
- 保持模块独立，拒绝将监控逻辑散落到采集脚本内部

---

### Step 4 - Strategic Insights

**AI 帮助完成了什么**

- 新增 `strategic_insights.py` 规则引擎（无外部 LLM）
- 基于竞品数据统计 Enterprise/Free 覆盖、SMB vs 开发者定位密度、集成缺口等
- 在 `report.html` 追加 Strategic Insights 章节：Market Opportunities、Strategic Recommendation、Top Risks、Future Monitoring Metrics
- 样式与现有报告保持一致，保留全部既有对比表与功能矩阵

**人工做了什么决策**

- 明确要求规则生成，不依赖大模型 API（成本、稳定性、可复现性）
- 指定输出结构与最低条目数（机会 ≥3、风险 ≥2）
- 将 Future Monitoring Metrics 定位为 Competitive Intelligence Pipeline 的一部分，而非孤立列表
- 不删除现有功能矩阵，战略模块作为增量章节叠加

---

### Step 5 - Builder's Perspective

**AI 帮助完成了什么**

- 在 `generate_report.py` 新增 `build_builders_perspective_section()`
- 于 Strategic Insights 之后插入独立标题与正文（约 379 字）
- 仅修改报告生成层，未触碰采集逻辑与功能矩阵

**人工做了什么决策**

- 确定核心论点：竞争焦点在 Website Creation，下一阶段可能转向 Grow Website
- 要求专业分析报告风格，禁止营销语气
- 字数控制在 200–400 字
- 内容以人工给出的战略判断为主，AI 负责结构化排版与落地

---

## Example of Incorrect AI Output

### 案例：`core_features` 将 Persona 误判为产品功能

**现象**

过滤导航项后，Lovable 的 `core_features` 仍包含：

- Founders
- Designers
- Marketers
- Product Managers

功能矩阵中，这些条目与「AI Website Builder」「Templates」等并列出现，看起来像产品能力。

**如何发现问题**

人工打开 `data/competitors.json` 与 `report.html` 功能对比表，对照 Lovable 官网结构复查。上述词条出现在「Solutions / For who」类区块，描述的是目标用户画像，而非可交付的功能模块。

**为什么判断是错的**

- **Persona** 回答「谁在用」——Founders、Designers 是用户角色
- **Product Feature** 回答「产品能做什么」——如 SEO、Deployment、Templates
- 混淆两者会导致功能矩阵虚增维度，后续 Strategic Insights 的「功能缺口」分析产生偏差

**如何修复**

- 增加 `NON_FEATURE_EXACT` 黑名单，过滤 Resources、Community、Press 等导航词
- 增加 80 字符上限，剔除长营销文案（如 Durable 的预约时段描述）
- 增加「以 Products 开头且词数 ≥4」规则，过滤 Replit 拼接导航字符串

**遗留问题（Remaining Limitations）**

Persona-related labels were subsequently filtered through PERSONA_LABELS and additional feature validation rules.

Current known limitations are:

- Marketing slogans may still pass filtering if they contain feature-like keywords (e.g. build, design).
- Replit feature extraction remains sparse because only a subset of meaningful page elements is captured.
- Duplicate features may still appear (e.g. template/template variations).
- Feature extraction is still DOM-order based rather than semantic-section based.

---

## Human Decisions

| 决策 | 原因 |
|------|------|
| 选择 AI Website Builder 赛道 | 产品密度高、定位差异可观察，适合验证采集 + 报告 + 监控闭环 |
| 配置驱动竞品列表 | 新增竞品只改 JSON，降低脚本变更频率 |
| 增加 Monitoring Pipeline | 竞品分析的价值在「变化」，单次快照无法支撑持续决策 |
| 增加 Strategic Insights | 原始对比表信息量大但缺少归纳，需要结构化战略输出 |
| 规则引擎而非 LLM | 可复现、零 API 成本、输出稳定；当前数据质量不足以支撑可靠 LLM 推断 |
| 增加 Builder's Perspective | 补充「Build → Grow」趋势判断，与 Strategic Insights 的数据归纳形成观点层 |
| 不修改采集逻辑即可加 Perspective | 分离采集层与报告层，降低回归风险 |
| 保留通用抓取而非 per-site Parser | 5 个竞品用统一逻辑可快速验证；精度问题通过过滤规则渐进修正 |

---

## Estimated Effort

假设由一名熟悉 Python 的开发者独立完成，含本地测试与报告复查：

| 阶段 | 预估工时 |
|------|----------|
| Project Scaffolding | 1.5 – 2 h |
| Competitor Collection | 2 – 2.5 h |
| Monitoring Pipeline | 1 – 1.5 h |
| Strategic Analysis | 1.5 – 2 h |
| Report Generation | 1 – 1.5 h |
| **合计** | **7 – 9.5 h** |

说明：上述为「已有需求文档、不含产品方向争论」的估算。若计入多轮数据质量复查（如 Persona 误判）与报告内容审校，上限可至 10 h。
