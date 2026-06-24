#!/usr/bin/env python3
"""Rule-based strategic insights from competitor data (no external LLM)."""

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
    """Generate strategic insight structure from competitors.json data."""
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
            "opportunity": "Focus on acquisition-oriented websites for local SMBs rather than generic site builders",
            "why": (
                f"Among {count} competitors, only about {smb_focus_count} clearly emphasize business growth, SEO, or lead gen; "
                "most still target developers or general prototyping—leaving room in the SMB segment."
            ),
        })
    else:
        opportunities.append({
            "opportunity": "Offer vertical industry templates and workflows on top of SMB website building",
            "why": (
                "Generic AI website builders are well covered, but vertical depth (legal, restaurants, home services) remains shallow; "
                "industry templates plus tailored copy can shorten time-to-launch and improve conversion."
            ),
        })

    if enterprise_count >= 3:
        opportunities.append({
            "opportunity": "Ship a lightweight team tier below Enterprise for small and mid-size teams",
            "why": (
                f"{enterprise_count}/{count} competitors promote Enterprise, "
                "but pricing and feature gates are high; teams of 5–50 need collaboration, permissions, and brand consistency without enterprise sales cycles."
            ),
        })
    else:
        opportunities.append({
            "opportunity": "Enter the mid-market with transparent, predictable usage-based pricing",
            "why": (
                f"About {free_tier_count}/{count} competitors emphasize free or low-cost entry, "
                "but upgrade paths and credit mechanics remain opaque; clear tiered pricing builds trust quickly."
            ),
        })

    integration_gap = not any(
        kw in feat for feat in all_features for kw in ("integrat", "zapier", "stripe", "crm", "webhook")
    )
    if integration_gap:
        opportunities.append({
            "opportunity": "Bundle CRM, payments, and booking integrations to close the build-to-operate loop",
            "why": (
                "Integration capabilities are rarely highlighted in competitor feature matrices; "
                "pre-built Stripe, Calendly, and HubSpot connections reduce friction from launch to revenue."
            ),
        })
    elif student_focus:
        opportunities.append({
            "opportunity": "Offer a low-cost collaborative tier for education and maker communities",
            "why": (
                f"Competitors such as {', '.join(student_focus)} already reach students, "
                "but course collaboration, portfolio showcases, and mentor review workflows remain underserved niches."
            ),
        })
    else:
        opportunities.append({
            "opportunity": "Strengthen design systems and cross-project brand consistency exports",
            "why": (
                "Many products generate quickly, but reusing brand rules (color, typography, components) across projects is weak; "
                "design systems plus one-click code/hosting export is a pain point professional teams will pay for."
            ),
        })

    if len(opportunities) < 3:
        opportunities.append({
            "opportunity": "Add multilingual and international website support",
            "why": "Most competitors target English-first markets; multilingual SEO and localized templates can serve cross-border SMBs and global teams.",
        })

    if smb_focus_count <= dev_focus_count:
        direction = "Vertical SMB growth AI Website Builder (SEO + lead gen + lightweight CRM)"
        reasons = [
            "Competitors densely cover developers and full-stack builders; SMB outcome-oriented positioning is relatively sparse.",
            "Products like Durable touch business scenarios but still have room on vertical depth and integrated growth loops.",
            "SMB buyers pay for customer acquisition, not generated code alone—clearer monetization path.",
        ]
    else:
        direction = "AI prototype-to-production export tool for product and design teams"
        reasons = [
            "Lovable, Bolt, and v0 validate conversational building, but production-grade component reuse and team workflows remain incomplete.",
            "Sit between v0's design strength and Bolt's full-stack depth with an export workflow engineers can ship.",
            "Avoid direct IDE competition (e.g. Replit); focus on websites and landing pages.",
        ]

    risks: list[dict[str, str]] = [
        {
            "risk": "Incumbents iterate fast, compressing differentiation windows",
            "impact": (
                f"The category already has {count} mature players (e.g. "
                f"{', '.join(c.get('name', '') for c in competitors[:3])}), "
                "and AI generation plus one-click deploy are becoming table stakes—differentiation may last only 6–12 months."
            ),
        },
        {
            "risk": "Free tiers and credit pricing fuel price wars and inflated user expectations",
            "impact": (
                f"About {free_tier_count}/{count} competitors offer free entry; "
                "after low-cost trials, paid conversion and ARPU pressure rises—new entrants need high operational efficiency to profit."
            ),
        },
    ]

    if enterprise_count >= 3:
        risks.append({
            "risk": "Enterprise segment pre-empted by incumbents",
            "impact": "Large-account sales cycles are long, and existing brands already hold security and compliance trust; new brands struggle to enter high-ACV markets quickly.",
        })
    else:
        risks.append({
            "risk": "Dependency on third-party cloud and model providers creates cost and stability risk",
            "impact": "Hosting and LLM API price or policy shifts can erode margins and degrade generation quality and latency.",
        })

    monitoring_metrics = [
        {
            "metric": "Pricing Changes",
            "description": "Changes to Free/Pro/Team/Enterprise tiers, credit allowances, and billing definitions.",
        },
        {
            "metric": "New Features",
            "description": "New AI capabilities, template libraries, collaboration, or export/deploy options.",
        },
        {
            "metric": "Positioning Changes",
            "description": "Shifts in homepage and pricing messaging on audience, value prop, and differentiation.",
        },
        {
            "metric": "Integrations",
            "description": "New third-party connections (payments, CRM, analytics, design tools, databases).",
        },
        {
            "metric": "Target Customer Changes",
            "description": "Pivots toward Enterprise, developers, SMB, students, or other segments.",
        },
        {
            "metric": "Landing Page Messaging Changes",
            "description": "Hero copy, CTAs, social proof, case studies, and feature priority ordering.",
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
