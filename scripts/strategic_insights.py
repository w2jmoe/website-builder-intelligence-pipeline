#!/usr/bin/env python3
"""基于竞品数据的规则化战略洞察生成（不依赖外部大模型）。"""

from __future__ import annotations

from typing import Any


def _text_blob(c: dict[str, Any]) -> str:
    parts = [
        c.get("target_customer") or "",
        c.get("pricing") or "",
        " ".join(c.get("core_features") or []),
        " ".join(c.get("technical_highlights") or []),
    ]
    return " ".join(parts).lower()


def _count_keyword_hits(competitors: list[dict[str, Any]], keywords: tuple[str, ...]) -> int:
    hits = 0
    for c in competitors:
        blob = _text_blob(c)
        if any(kw in blob for kw in keywords):
            hits += 1
    return hits


def _collect_all_features(competitors: list[dict[str, Any]]) -> set[str]:
    features: set[str] = set()
    for c in competitors:
        for feat in c.get("core_features") or []:
            features.add(feat.lower())
    return features


def _names_with_keywords(competitors: list[dict[str, Any]], keywords: tuple[str, ...]) -> list[str]:
    names: list[str] = []
    for c in competitors:
        if any(kw in _text_blob(c) for kw in keywords):
            names.append(c.get("name", ""))
    return names


def generate_insights(competitors: list[dict[str, Any]]) -> dict[str, Any]:
    """根据 competitors.json 数据生成战略洞察结构。"""
    count = len(competitors)
    enterprise_count = _count_keyword_hits(competitors, ("enterprise",))
    free_tier_count = _count_keyword_hits(competitors, ("free", "start for free", "$0"))
    dev_focus_count = _count_keyword_hits(
        competitors, ("developer", "full-stack", "full stack", "code", "github", "deploy")
    )
    smb_focus_count = _count_keyword_hits(
        competitors, ("business", "seo", "customer", "marketing", "local", "small business")
    )
    student_focus = _names_with_keywords(competitors, ("student", "students"))
    all_features = _collect_all_features(competitors)

    opportunities: list[dict[str, str]] = []

    if smb_focus_count <= max(1, count // 3):
        opportunities.append({
            "opportunity": "聚焦本地商户与小型企业的「获客型网站」而非通用建站",
            "why": (
                f"当前 {count} 个竞品中，仅约 {smb_focus_count} 个在定位上明显强调商业增长、SEO 或获客；"
                "多数产品仍偏向开发者或通用原型，SMB 场景存在差异化空间。"
            ),
        })
    else:
        opportunities.append({
            "opportunity": "在 SMB 建站基础上提供垂直行业模板与工作流",
            "why": (
                "已有竞品覆盖通用 AI 建站，但行业深度（如律所、餐饮、家政）仍较浅；"
                "垂直模板 + 行业文案可缩短上线时间并提高转化。"
            ),
        })

    if enterprise_count >= 3:
        opportunities.append({
            "opportunity": "提供轻量团队版，承接 Enterprise 以下的中小团队需求",
            "why": (
                f"{enterprise_count}/{count} 个竞品已宣传 Enterprise，"
                "但定价与功能门槛偏高；5–50 人团队需要协作、权限与品牌一致性，却不愿承担企业级销售流程。"
            ),
        })
    else:
        opportunities.append({
            "opportunity": "以透明、可预测的用量定价切入中端市场",
            "why": (
                f"约 {free_tier_count}/{count} 个竞品强调 Free/低价入门，"
                "但升级路径与 credit 机制对用户仍不透明；清晰的分层定价是获取信任的快速方式。"
            ),
        })

    integration_gap = not any(
        kw in feat for feat in all_features for kw in ("integrat", "zapier", "stripe", "crm", "webhook")
    )
    if integration_gap:
        opportunities.append({
            "opportunity": "内置 CRM / 支付 / 预约等开箱集成，形成「建站 + 运营」闭环",
            "why": (
                "竞品功能矩阵中集成类能力提及较少；"
                "新进入者可通过预置 Stripe、Calendly、HubSpot 等集成，降低用户从建站到营业的切换成本。"
            ),
        })
    elif student_focus:
        opportunities.append({
            "opportunity": "面向教育/创客场景的低价协作版",
            "why": (
                f"已有 {', '.join(student_focus)} 等竞品触达学生群体，"
                "但课程项目协作、作业展示、导师评审等教育专属流程仍可作为细分切口。"
            ),
        })
    else:
        opportunities.append({
            "opportunity": "强化设计系统与品牌一致性导出能力",
            "why": (
                "多款产品支持快速生成，但品牌规范（色彩、字体、组件库）在多项目间复用仍弱；"
                "设计系统 + 一键导出代码/托管是专业团队愿意付费的痛点。"
            ),
        })

    # 确保至少 3 条
    if len(opportunities) < 3:
        opportunities.append({
            "opportunity": "提供多语言与国际化建站支持",
            "why": "当前竞品主要面向英语市场；多语言 SEO 与本地化模板可服务跨境 SMB 与出海团队。",
        })

    # Strategic Recommendation — pick direction by rule scoring
    if smb_focus_count <= dev_focus_count:
        direction = "垂直 SMB 增长型 AI Website Builder（SEO + 获客 + 轻量 CRM）"
        reasons = [
            "竞品密集覆盖开发者与全栈构建，SMB 商业结果导向的定位相对稀疏。",
            "Durable 等虽已触达商业场景，但在行业深度、集成闭环上仍有扩展余地。",
            "SMB 用户愿为「带来客户」付费，而非仅为「生成代码」付费，商业模式更清晰。",
        ]
    else:
        direction = "面向产品/设计团队的 AI 原型 → 生产级导出工具"
        reasons = [
            "Lovable、Bolt、v0 等已验证「对话式构建」需求，但生产级组件复用与团队协作仍不充分。",
            "可在 v0 的设计优势与 Bolt 的全栈能力之间，切入「可交付给工程团队」的导出工作流。",
            "避开与 Replit 等 IDE 平台的直接竞争，聚焦网站/landing page 场景。",
        ]

    risks: list[dict[str, str]] = [
        {
            "risk": "头部竞品快速迭代，功能同质化周期缩短",
            "impact": (
                f"赛道已有 {count} 个成熟玩家（如 "
                f"{', '.join(c.get('name', '') for c in competitors[:3])} 等），"
                "AI 生成、一键部署等基础能力迅速成为标配，差异化窗口可能仅 6–12 个月。"
            ),
        },
        {
            "risk": "免费层 + Credit 定价引发价格战与用户预期抬升",
            "impact": (
                f"约 {free_tier_count}/{count} 个竞品提供免费入门；"
                "用户习惯低成本试错后，付费转化率与 ARPU 承压，新进入者需更高运营效率才能盈利。"
            ),
        },
    ]

    if enterprise_count >= 3:
        risks.append({
            "risk": "Enterprise 赛道被 incumbents 提前占位",
            "impact": "大客户采购决策周期长，且现有品牌已建立安全/compliance 信任；新品牌难以短期进入高客单价市场。",
        })
    else:
        risks.append({
            "risk": "依赖第三方云与模型供应商，成本与稳定性不可控",
            "impact": "Hosting、LLM API 价格波动或政策变更可能直接侵蚀毛利，并影响生成质量与响应速度。",
        })

    monitoring_metrics = [
        {
            "metric": "Pricing Changes",
            "description": "各竞品 Free/Pro/Team/Enterprise 层级、credit 额度与计费口径变化。",
        },
        {
            "metric": "New Features",
            "description": "新增 AI 能力、模板库、协作功能或导出/部署选项。",
        },
        {
            "metric": "Positioning Changes",
            "description": "首页与定价页对目标人群、价值主张、差异化表述的调整。",
        },
        {
            "metric": "Integrations",
            "description": "新增第三方集成（支付、CRM、分析、设计工具、数据库等）。",
        },
        {
            "metric": "Target Customer Changes",
            "description": "是否转向 Enterprise、开发者、SMB、学生等新细分客群。",
        },
        {
            "metric": "Landing Page Messaging Changes",
            "description": "Hero 文案、CTA、社会证明、案例客户与功能优先级排序变化。",
        },
    ]

    return {
        "market_opportunities": opportunities[: max(3, len(opportunities))],
        "strategic_recommendation": {
            "direction": direction,
            "reasons": reasons,
        },
        "top_risks": risks[: max(2, len(risks))],
        "future_monitoring_metrics": monitoring_metrics,
    }
