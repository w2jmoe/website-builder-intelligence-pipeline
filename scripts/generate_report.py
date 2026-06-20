#!/usr/bin/env python3
"""读取 competitors.json，生成 HTML 竞品分析报告。"""

from __future__ import annotations

import html
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategic_insights import generate_insights

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "competitors.json"
REPORT_PATH = BASE_DIR / "reports" / "report.html"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_competitors(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"未找到 {path}，请先运行: python scripts/collect_competitors.py"
        )

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("competitors.json 格式错误，应为数组")

    return data


def esc(value: Any) -> str:
    return html.escape(str(value) if value is not None else "")


def format_list(items: list[str]) -> str:
    if not items:
        return '<span class="muted">—</span>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def build_overview_cards(competitors: list[dict[str, Any]]) -> str:
    cards = []
    for c in competitors:
        cards.append(
            f"""
            <article class="card">
              <h3>{esc(c.get("name", ""))}</h3>
              <p><a href="{esc(c.get("website", ""))}" target="_blank" rel="noopener">{esc(c.get("website", ""))}</a></p>
              <p class="label">目标客户</p>
              <p>{esc(c.get("target_customer") or "—")}</p>
              <p class="label">定价摘要</p>
              <p>{esc(c.get("pricing") or "—")}</p>
            </article>
            """
        )
    return "\n".join(cards)


def build_feature_matrix(competitors: list[dict[str, Any]]) -> str:
    all_features: list[str] = []
    seen: set[str] = set()
    for c in competitors:
        for feat in c.get("core_features") or []:
            key = feat.lower()
            if key not in seen:
                seen.add(key)
                all_features.append(feat)

    if not all_features:
        all_features = ["（暂无采集到的功能项）"]

    header = "<tr><th>功能 / 竞品</th>" + "".join(
        f"<th>{esc(c.get('name', ''))}</th>" for c in competitors
    ) + "</tr>"

    rows = []
    for feat in all_features:
        cells = [f"<td>{esc(feat)}</td>"]
        feat_lower = feat.lower()
        for c in competitors:
            features = [f.lower() for f in (c.get("core_features") or [])]
            mark = "✓" if any(feat_lower in f or f in feat_lower for f in features) else "—"
            cells.append(f'<td class="center">{mark}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    return f"<table><thead>{header}</thead><tbody>{''.join(rows)}</tbody></table>"


def build_simple_table(
    competitors: list[dict[str, Any]],
    field: str,
    title: str,
) -> str:
    rows = []
    for c in competitors:
        value = c.get(field) or "—"
        rows.append(
            f"<tr><td>{esc(c.get('name', ''))}</td><td>{esc(value)}</td></tr>"
        )
    return f"""
    <section>
      <h2>{esc(title)}</h2>
      <table class="simple">
        <thead><tr><th>竞品</th><th>{esc(title.replace("对比", ""))}</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
    """


def build_technical_section(competitors: list[dict[str, Any]]) -> str:
    rows = []
    for c in competitors:
        rows.append(
            f"<tr><td>{esc(c.get('name', ''))}</td>"
            f"<td>{format_list(c.get('technical_highlights') or [])}</td></tr>"
        )
    return f"""
    <section>
      <h2>技术亮点</h2>
      <table class="simple">
        <thead><tr><th>竞品</th><th>技术关键词</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
    """


def build_strategic_insights_section(insights: dict[str, Any]) -> str:
    opportunities_html = ""
    for item in insights.get("market_opportunities", []):
        opportunities_html += f"""
        <article class="insight-card">
          <p class="insight-title">{esc(item.get("opportunity", ""))}</p>
          <p class="label">Why it matters</p>
          <p>{esc(item.get("why", ""))}</p>
        </article>
        """

    rec = insights.get("strategic_recommendation", {})
    reasons_html = format_list(rec.get("reasons") or [])

    risks_html = ""
    for item in insights.get("top_risks", []):
        risks_html += f"""
        <article class="insight-card">
          <p class="insight-title">{esc(item.get("risk", ""))}</p>
          <p class="label">潜在影响</p>
          <p>{esc(item.get("impact", ""))}</p>
        </article>
        """

    metrics_rows = ""
    for item in insights.get("future_monitoring_metrics", []):
        metrics_rows += (
            f"<tr><td>{esc(item.get('metric', ''))}</td>"
            f"<td>{esc(item.get('description', ''))}</td></tr>"
        )

    return f"""
    <section class="strategic-section">
      <h2>Strategic Insights</h2>

      <h3 class="subsection">Market Opportunities</h3>
      <div class="insight-grid">
        {opportunities_html}
      </div>

      <h3 class="subsection">Strategic Recommendation</h3>
      <article class="insight-card highlight">
        <p class="label">推荐切入方向</p>
        <p class="insight-title">{esc(rec.get("direction", ""))}</p>
        <p class="label">推荐理由</p>
        {reasons_html}
      </article>

      <h3 class="subsection">Top Risks</h3>
      <div class="insight-grid">
        {risks_html}
      </div>

      <h3 class="subsection">Future Monitoring Metrics</h3>
      <p class="pipeline-note">Competitive Intelligence Pipeline — 建议持续监控以下指标：</p>
      <table class="simple">
        <thead><tr><th>指标</th><th>说明</th></tr></thead>
        <tbody>{metrics_rows}</tbody>
      </table>
    </section>
    """


def build_builders_perspective_section() -> str:
    return """
    <section class="builders-perspective-section">
      <h2>Builder's Perspective</h2>
      <article class="perspective-card">
        <p>通过本次竞品分析可以看出，当前 AI Website Builder 赛道的竞争焦点高度集中于 Website Creation 环节——对话式生成、模板调用、一键部署已成为各产品的共性能力。然而，网站上线后的增长运营、SEO 优化、转化提升与客户获取，仍大量依赖人工执行或第三方工具补充，尚未被主流产品系统性整合。</p>
        <p>从用户决策逻辑观察，SMB 与创业者购买此类产品的本质诉求并非「拥有一个网站」，而是「获得可衡量的业务结果」。当建站门槛持续下降，差异化价值将逐渐从 Build Website 向 Grow Website 迁移——即谁能更高效地承接上线后的获客、留存与营收闭环，谁更可能在下一阶段建立竞争优势。</p>
        <p>本次样本中，仅个别竞品在定位上涉及 SEO 与获客能力，但尚未形成从创建到增长的完整产品叙事。这一结构性空白，值得在后续监控周期中持续跟踪与验证。</p>
      </article>
    </section>
    """


def render_html(competitors: list[dict[str, Any]]) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    names = ", ".join(c.get("name", "") for c in competitors)
    insights = generate_insights(competitors)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Website Builder 竞品分析报告</title>
  <style>
    :root {{
      --bg: #f6f8fb;
      --card: #ffffff;
      --text: #1a1f36;
      --muted: #6b7280;
      --accent: #2563eb;
      --border: #e5e7eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    header {{
      background: linear-gradient(135deg, #1e3a8a, #2563eb);
      color: #fff;
      padding: 2.5rem 1.5rem;
    }}
    header h1 {{ margin: 0 0 0.5rem; font-size: 1.75rem; }}
    header p {{ margin: 0; opacity: 0.9; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem 3rem; }}
    section {{ margin-bottom: 2.5rem; }}
    h2 {{ font-size: 1.25rem; margin-bottom: 1rem; border-left: 4px solid var(--accent); padding-left: 0.75rem; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}
    .card h3 {{ margin: 0 0 0.5rem; }}
    .label {{ font-size: 0.8rem; color: var(--muted); margin: 0.75rem 0 0.25rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      font-size: 0.92rem;
    }}
    th, td {{ border-bottom: 1px solid var(--border); padding: 0.75rem 1rem; text-align: left; vertical-align: top; }}
    th {{ background: #f9fafb; font-weight: 600; }}
    tr:last-child td {{ border-bottom: none; }}
    .simple td:first-child {{ width: 140px; font-weight: 600; }}
    .center {{ text-align: center; }}
    .muted {{ color: var(--muted); }}
    ul {{ margin: 0; padding-left: 1.2rem; }}
    footer {{ text-align: center; color: var(--muted); font-size: 0.85rem; padding: 1rem; }}
    a {{ color: var(--accent); }}
    .strategic-section {{ margin-top: 3rem; padding-top: 1rem; border-top: 2px solid var(--border); }}
    h3.subsection {{ font-size: 1.05rem; margin: 1.75rem 0 1rem; color: var(--text); border-left: 3px solid #93c5fd; padding-left: 0.65rem; }}
    .insight-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }}
    .insight-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
    .insight-card.highlight {{ border-color: #93c5fd; background: #f8fbff; }}
    .insight-title {{ margin: 0 0 0.5rem; font-weight: 600; font-size: 1rem; }}
    .pipeline-note {{ color: var(--muted); font-size: 0.92rem; margin-bottom: 0.75rem; }}
    .builders-perspective-section {{ margin-top: 3rem; padding-top: 1rem; border-top: 2px solid var(--border); }}
    .perspective-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1.5rem 1.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); font-size: 0.95rem; color: var(--text); }}
    .perspective-card p {{ margin: 0 0 1rem; text-align: justify; }}
    .perspective-card p:last-child {{ margin-bottom: 0; }}
  </style>
</head>
<body>
  <header>
    <h1>AI Website Builder 竞品分析报告</h1>
    <p>竞品：{esc(names)} · 生成时间：{esc(generated_at)}</p>
  </header>
  <main>
    <section>
      <h2>竞品概览</h2>
      <div class="grid">
        {build_overview_cards(competitors)}
      </div>
    </section>

    <section>
      <h2>功能对比表</h2>
      {build_feature_matrix(competitors)}
    </section>

    {build_simple_table(competitors, "pricing", "定价对比")}
    {build_simple_table(competitors, "target_customer", "目标客户对比")}
    {build_technical_section(competitors)}
    {build_strategic_insights_section(insights)}
    {build_builders_perspective_section()}
  </main>
  <footer>AI Website Builder Competitive Analysis · 基础工程骨架</footer>
</body>
</html>
"""


def generate_report(
    data_path: Path = DATA_PATH,
    report_path: Path = REPORT_PATH,
) -> Path:
    competitors = load_competitors(data_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    content = render_html(competitors)
    report_path.write_text(content, encoding="utf-8")

    logger.info("报告已生成 -> %s", report_path)
    return report_path


def main() -> int:
    try:
        generate_report()
        return 0
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
