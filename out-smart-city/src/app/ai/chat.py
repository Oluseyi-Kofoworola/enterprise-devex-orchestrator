"""AI Chat Router -- domain-aware chat with entity context and RAG.

Capabilities: chat, embeddings, rag, agents, content-safety
Handles any enterprise domain by grounding responses in the app's own data.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from ai.client import CHAT_MODEL, chat_completion, get_ai_client
from core.dependencies import get_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _search_rag_context(query: str, top_k: int = 3) -> str:
    """Retrieve context from Azure AI Search when configured."""
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    if not search_endpoint:
        return ""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.search.documents import SearchClient

        credential = DefaultAzureCredential(
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
        )
        client = SearchClient(
            endpoint=search_endpoint,
            index_name=os.getenv("AZURE_SEARCH_INDEX", "documents"),
            credential=credential,
        )
        results = client.search(search_text=query, top=top_k)
        chunks = [doc.get("content", "") for doc in results if doc.get("content")]
        return "\n\n".join(chunks)
    except Exception as e:
        logger.warning("ai_search.rag_fallback", extra={"error": str(e)})
        return ""


def _build_domain_context() -> dict:
    """Build structured domain context from the app\'s own entity repositories."""
    result: dict[str, list[dict]] = {}
    try:
        repo = get_repository("incident")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["Incident"] = records
    except Exception:
        pass
    try:
        repo = get_repository("asset")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["Asset"] = records
    except Exception:
        pass
    try:
        repo = get_repository("sensor")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["Sensor"] = records
    except Exception:
        pass
    try:
        repo = get_repository("service_request")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["ServiceRequest"] = records
    except Exception:
        pass
    try:
        repo = get_repository("transit_route")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["TransitRoute"] = records
    except Exception:
        pass
    try:
        repo = get_repository("vehicle")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["Vehicle"] = records
    except Exception:
        pass
    try:
        repo = get_repository("zone")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["Zone"] = records
    except Exception:
        pass
    try:
        repo = get_repository("work_order")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["WorkOrder"] = records
    except Exception:
        pass
    try:
        repo = get_repository("audit_log")
        items = repo.list_all()
        records = []
        for item in items:
            if hasattr(item, "__dict__"):
                records.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
            elif isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": str(item)})
        result["AuditLog"] = records
    except Exception:
        pass
    return result


def _local_data_reply(question: str, context: dict) -> str:
    """Smart analytical data engine with conversational reasoning -- works without an AI provider."""
    import re as _re
    from collections import Counter

    q = question.lower().strip()
    entity_names = list(context.keys())
    total_records = sum(len(v) for v in context.values())

    # --- Intent detection ---
    def _is_greeting():
        return any(w in q for w in ("hello", "hi ", "hey", "good morning", "good afternoon", "greetings", "howdy")) or q in ("hi", "hey")

    def _is_count():
        return any(w in q for w in ("how many", "count", "total", "number of", "quantity"))

    def _is_list():
        return any(w in q for w in ("list", "show me", "show all", "display", "get all", "what are the", "give me"))

    def _is_status():
        return any(w in q for w in ("status", "health", "overview", "summary", "dashboard", "report", "how is", "how are"))

    def _is_analytics():
        return any(w in q for w in ("analyze", "analyse", "trend", "insight", "breakdown", "distribution", "statistic", "average", "mean", "compare", "correlation", "pattern", "top", "bottom", "worst", "best", "highest", "lowest", "most", "least", "peak"))

    def _is_help():
        return any(w in q for w in ("help", "what can you", "capabilities", "what do you", "how do i", "how to"))

    def _is_action():
        return any(w in q for w in ("create", "add", "update", "delete", "remove", "fix", "resolve", "assign", "triage", "escalate", "dispatch", "approve", "schedule"))

    def _is_filter():
        return any(w in q for w in ("where", "which", "filter", "find", "with", "without", "that have", "that are", "pending", "active", "completed", "critical", "high", "low", "open", "closed"))

    def _is_temporal():
        return any(w in q for w in ("latest", "recent", "newest", "oldest", "last updated", "first", "when was", "most recent", "earliest", "last created", "last added", "new record", "updated record", "last record", "ago"))

    def _is_recommendation():
        return any(w in q for w in ("improve", "improvement", "suggest", "suggestion", "recommend", "recommendation", "future", "what should", "next step", "forecast", "optimize", "optimise", "enhance", "gap", "missing", "weakness", "opportunity", "priority action", "attention"))

    def _is_crossentity():
        return any(w in q for w in ("related", "belong", "associated", "linked", "connected", "between", "correlation", "correlate", "across entities", "across all", "comparison", "compare all"))

    # --- Entity matching (flexible NLP) ---
    def _find_entity() -> tuple[str, list[dict]]:
        best_match = ("", [])
        best_score = 0
        for name in entity_names:
            name_lower = name.lower()
            score = 0
            # Exact match
            if name_lower in q or name_lower + "s" in q:
                score = 10
            elif name_lower.rstrip("s") in q:
                score = 9
            else:
                # CamelCase split: "ServiceRequest" -> ["service", "request"]
                words = _re.split(r'(?<=[a-z])(?=[A-Z])', name)
                words = [w.lower() for w in words if w]
                # snake_case split
                snake_parts = name_lower.split("_")
                all_tokens = set(words + snake_parts)
                matched_tokens = sum(1 for w in all_tokens if len(w) > 2 and w in q)
                if matched_tokens > 0:
                    score = matched_tokens * 3
                # Singular/plural variations
                for w in all_tokens:
                    if len(w) > 3:
                        if w + "s" in q or w.rstrip("s") in q:
                            score = max(score, 5)
            if score > best_score:
                best_score = score
                best_match = (name, context[name])
        return best_match

    # --- HTML helpers ---
    def _table(records: list[dict], keys: list[str] | None = None, max_rows: int = 10) -> str:
        if not records:
            return "<em>No records found.</em>"
        keys = keys or [k for k in records[0].keys() if k != "id"][:6]
        headers = "".join(f"<th>{k.replace('_', ' ').title()}</th>" for k in keys)
        rows = ""
        for r in records[:max_rows]:
            cells = ""
            for k in keys:
                v = r.get(k, "")
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v[:3])
                elif v is None:
                    v = ""
                cells += f"<td>{v}</td>"
            rows += f"<tr>{cells}</tr>"
        more = f"<tr><td colspan='{len(keys)}' style='text-align:center;color:#666;font-style:italic'>...and {len(records) - max_rows} more</td></tr>" if len(records) > max_rows else ""
        return f"<table class='ai-table'><thead><tr>{headers}</tr></thead><tbody>{rows}{more}</tbody></table>"

    def _stat_card(label: str, value, color: str = "#0078d4") -> str:
        return f"<span class='ai-stat' style='border-color:{color}'><strong style='color:{color}'>{value}</strong> {label}</span>"

    def _section(title: str, body: str) -> str:
        return f"<div class='ai-section'><div class='ai-section-title'>{title}</div>{body}</div>"

    def _status_breakdown(records: list[dict]) -> dict[str, int]:
        statuses = [str(r.get("status", "unknown")).lower() for r in records]
        return dict(Counter(statuses).most_common())

    def _field_distribution(records: list[dict], field: str) -> dict[str, int]:
        values = [str(r.get(field, "unknown")).lower() for r in records if r.get(field)]
        return dict(Counter(values).most_common(10))

    def _bar_chart(distribution: dict[str, int], color: str = "#0078d4") -> str:
        if not distribution:
            return ""
        max_val = max(distribution.values())
        bars = ""
        for label, count in distribution.items():
            pct = (count / max_val) * 100 if max_val else 0
            bars += f"<div class='ai-bar-row'><span class='ai-bar-label'>{label}</span><div class='ai-bar-track'><div class='ai-bar-fill' style='width:{pct}%;background:{color}'></div></div><span class='ai-bar-val'>{count}</span></div>"
        return f"<div class='ai-bar-chart'>{bars}</div>"

    def _numeric_stats(records: list[dict], field: str) -> dict | None:
        vals = []
        for r in records:
            v = r.get(field)
            if v is not None:
                try:
                    vals.append(float(v))
                except (ValueError, TypeError):
                    pass
        if not vals:
            return None
        return {"min": min(vals), "max": max(vals), "avg": sum(vals)/len(vals), "count": len(vals)}

    # --- Responses ---

    if _is_greeting():
        cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
        return (
            f"<div class='ai-greeting'>👋 Hello! I'm your intelligent data assistant for this platform.</div>"
            f"<div class='ai-stats-row'>{cards}</div>"
            f"<div class='ai-hint'>I can analyze <strong>{total_records} records</strong> across "
            f"<strong>{len(entity_names)} entities</strong>. Try asking me:</div>"
            f"<ul class='ai-suggestions'>"
            f"<li>\"How many incidents are critical?\"</li>"
            f"<li>\"Show me a breakdown of asset status\"</li>"
            f"<li>\"What needs attention right now?\"</li>"
            f"<li>\"Analyze sensor health trends\"</li></ul>"
        )

    if _is_help():
        return (
            f"<div class='ai-section-title'>💡 What I Can Do</div>"
            f"<ul class='ai-suggestions'>"
            f"<li><strong>Count & Summarize</strong> — \"How many work orders are pending?\"</li>"
            f"<li><strong>Browse Data</strong> — \"Show me all sensors\" or \"List critical incidents\"</li>"
            f"<li><strong>Analyze Patterns</strong> — \"Breakdown incidents by status\" or \"Analyze asset health\"</li>"
            f"<li><strong>Find & Filter</strong> — \"Which vehicles are active?\" or \"Find pending requests\"</li>"
            f"<li><strong>Temporal Queries</strong> — \"Show latest incidents\" or \"What was the first work order?\"</li>"
            f"<li><strong>Cross-Entity</strong> — \"Compare all entities\" or \"Status across all\"</li>"
            f"<li><strong>Recommendations</strong> — \"What should we improve?\" or \"Future suggestions\"</li>"
            f"<li><strong>Action Guidance</strong> — \"How do I create an incident?\" or \"How to triage?\"</li></ul>"
            f"<div class='ai-hint'>I have access to {total_records} records across: {', '.join(entity_names)}</div>"
        )

    # --- Temporal queries BEFORE action (so "latest updated" doesn't trigger action via "update") ---
    if _is_temporal():
        ename, edata = _find_entity()
        if not ename and entity_names:
            ename, edata = entity_names[0], context[entity_names[0]]
        if edata:
            is_oldest = any(w in q for w in ("oldest", "first", "earliest"))
            sorted_records = sorted(edata, key=lambda r: str(r.get("created_at", r.get("updated_at", r.get("timestamp", "")))), reverse=not is_oldest)
            direction = "Oldest" if is_oldest else "Most Recent"
            top_records = sorted_records[:5]
            display_keys = [k for k in top_records[0].keys() if k != "id"][:7]
            # ensure created_at is included
            if "created_at" not in display_keys:
                display_keys.append("created_at")
            return (
                f"<div class='ai-section-title'>🕒 {direction} {ename} Records</div>"
                f"<div class='ai-hint'>Showing {len(top_records)} {direction.lower()} of {len(edata)} total records, sorted by timestamp.</div>"
                + _table(top_records, display_keys)
                + f"<div class='ai-hint'>Latest record: <strong>{sorted_records[0].get('created_at', 'N/A')}</strong></div>"
            )
        return f"<div class='ai-hint'>Specify an entity, e.g. \"show latest incidents\" or \"oldest work orders\"</div>"

    if _is_action():
        ename, edata = _find_entity()
        if not ename:
            ename = entity_names[0] if entity_names else "Resource"
        sn = _re.sub(r'(?<=[a-z])(?=[A-Z])', '_', ename).lower()
        plural = sn + "s"
        return (
            f"<div class='ai-section-title'>🔧 API Actions for {ename}</div>"
            f"<table class='ai-table'><thead><tr><th>Action</th><th>Method</th><th>Endpoint</th></tr></thead>"
            f"<tbody>"
            f"<tr><td>List all</td><td><code>GET</code></td><td><code>/api/v1/{plural}</code></td></tr>"
            f"<tr><td>Get by ID</td><td><code>GET</code></td><td><code>/api/v1/{plural}/{{id}}</code></td></tr>"
            f"<tr><td>Create</td><td><code>POST</code></td><td><code>/api/v1/{plural}</code></td></tr>"
            f"<tr><td>Update</td><td><code>PUT</code></td><td><code>/api/v1/{plural}/{{id}}</code></td></tr>"
            f"<tr><td>Delete</td><td><code>DELETE</code></td><td><code>/api/v1/{plural}/{{id}}</code></td></tr>"
            f"</tbody></table>"
            f"<div class='ai-hint'>Use the <strong>API Docs</strong> link in the footer for interactive testing.</div>"
        )

    if _is_filter():
        ename, edata = _find_entity()
        if not ename:
            for name, records in context.items():
                ename, edata = name, records
                break
        if edata:
            filter_terms = [t for t in ("pending","active","completed","critical","high","low","open","closed","in_progress","healthy","unhealthy","degraded","failed") if t in q]
            if filter_terms:
                matched = [r for r in edata if any(t in json.dumps(r, default=str).lower() for t in filter_terms)]
                desc = " & ".join(filter_terms)
                if matched:
                    display_keys = [k for k in matched[0].keys() if k != "id"][:6]
                    return (
                        f"<div class='ai-section-title'>🔍 {ename} — \"{desc}\"</div>"
                        f"<div class='ai-hint'>Found <strong>{len(matched)}</strong> of {len(edata)} records matching.</div>"
                        + _table(matched, display_keys)
                    )
                else:
                    return (
                        f"<div class='ai-section-title'>{ename} — filter \"{desc}\"</div>"
                        f"<div class='ai-hint'>No records match that filter. Current statuses:</div>"
                        + _bar_chart(_status_breakdown(edata))
                    )
            else:
                display_keys = [k for k in edata[0].keys() if k != "id"][:6] if edata else []
                return f"<div class='ai-section-title'>{ename} ({len(edata)} records)</div>" + _table(edata, display_keys)
        return f"<div class='ai-hint'>Specify an entity to filter, e.g. \"which incidents are critical?\"</div>"

    if _is_count():
        ename, edata = _find_entity()
        if ename:
            status_dist = _status_breakdown(edata)
            cards = "".join(
                _stat_card(s.title(), c, "#107c10" if s in ("completed","resolved","healthy") else "#d83b01" if s in ("critical","failed","unhealthy") else "#0078d4")
                for s, c in status_dist.items()
            )
            return (
                f"<div class='ai-section-title'>📊 {ename} — {len(edata)} total records</div>"
                f"<div class='ai-stats-row'>{cards}</div>"
                + (_bar_chart(status_dist) if len(status_dist) > 1 else "")
            )
        else:
            cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
            return (
                f"<div class='ai-section-title'>📊 Record Counts</div>"
                f"<div class='ai-stats-row'>{cards}</div>"
                + _stat_card("Total Records", total_records, "#107c10")
            )

    # --- Cross-entity comparison (must be before analytics to avoid "compare" collision) ---
    if _is_crossentity():
        parts = [f"<div class='ai-section-title'>📊 Cross-Entity Comparison</div>"]
        comparison_rows = ""
        for name, records in context.items():
            total = len(records)
            status_dist = _status_breakdown(records)
            needs_action = sum(v for k, v in status_dist.items() if k in ("pending","critical","open","failed","unhealthy","degraded"))
            resolved = sum(v for k, v in status_dist.items() if k in ("completed","resolved","closed","healthy"))
            in_progress = sum(v for k, v in status_dist.items() if k in ("in_progress","active"))
            health_pct = (resolved * 100 // total) if total > 0 else 0
            health_color = "#107c10" if health_pct >= 70 else "#d83b01" if health_pct < 40 else "#ffc107"
            comparison_rows += (
                f"<tr><td><strong>{name}</strong></td><td>{total}</td>"
                f"<td style='color:#d83b01'>{needs_action}</td>"
                f"<td style='color:#0078d4'>{in_progress}</td>"
                f"<td style='color:#107c10'>{resolved}</td>"
                f"<td style='color:{health_color}'>{health_pct}%</td></tr>"
            )
        parts.append(
            f"<table class='ai-table'><thead><tr>"
            f"<th>Entity</th><th>Total</th><th>⚠ Action</th><th>🔄 Progress</th><th>✅ Done</th><th>Health</th>"
            f"</tr></thead><tbody>{comparison_rows}</tbody></table>"
        )
        all_action = sum(
            sum(1 for r in records if str(r.get('status','')).lower() in ('pending','critical','open','failed','unhealthy','degraded'))
            for records in context.values()
        )
        worst_entity = max(context.items(), key=lambda x: sum(1 for r in x[1] if str(r.get('status','')).lower() in ('pending','critical','open','failed')))
        parts.append(
            f"<div class='ai-hint'>💡 <strong>{all_action}</strong> items need action across all entities. "
            f"<strong>{worst_entity[0]}</strong> has the most items requiring attention.</div>"
        )
        return "".join(parts)

    # --- Recommendation / improvement engine (must be before analytics) ---
    if _is_recommendation():
        parts = [f"<div class='ai-section-title'>💡 Platform Improvement Recommendations</div>"]
        recommendations = []
        high_action_entities = []
        for name, records in context.items():
            total = len(records)
            if total == 0:
                continue
            status_dist = _status_breakdown(records)
            needs_action = sum(v for k, v in status_dist.items() if k in ("pending","critical","open","failed","unhealthy","degraded"))
            action_pct = needs_action * 100 // total if total > 0 else 0
            if action_pct > 30:
                high_action_entities.append((name, action_pct, needs_action))
            if records and records[0].get("priority") or records[0].get("severity"):
                field = "priority" if "priority" in records[0] else "severity"
                dist = _field_distribution(records, field)
                critical_count = sum(v for k, v in dist.items() if k in ("critical","high"))
                if critical_count > total * 0.3:
                    recommendations.append(
                        f"🔴 <strong>{name}</strong> has {critical_count} critical/high priority items "
                        f"({critical_count * 100 // total}%) — consider adding more resources or automated triage."
                    )
        if high_action_entities:
            for ename, pct, count in sorted(high_action_entities, key=lambda x: -x[1]):
                recommendations.append(
                    f"⚠️ <strong>{ename}</strong> has {count} items ({pct}%) pending action — "
                    f"prioritize processing these to reduce backlog."
                )
        recommendations.extend([
            f"📈 <strong>Automation</strong> — Set up automated status transitions for records idle >48 hours.",
            f"🔒 <strong>Security</strong> — Ensure all API endpoints use RBAC with Managed Identity authentication.",
            f"🔍 <strong>Monitoring</strong> — Add Azure Monitor alerts for entities with >50% pending items.",
            f"📊 <strong>Dashboards</strong> — Create per-team dashboards filtering by assigned_to or zone.",
            f"⚡ <strong>Performance</strong> — Index frequently queried fields (status, priority, created_at) for faster lookups.",
            f"🔄 <strong>CI/CD</strong> — Add automated regression tests for all {len(entity_names)} entity endpoints.",
        ])
        parts.append("<ol class='ai-suggestions'>" + "".join(f"<li>{r}</li>" for r in recommendations) + "</ol>")
        parts.append(
            f"<div class='ai-hint'>🎯 Based on analysis of {total_records} records across {len(entity_names)} entities. "
            f"Ask about a specific entity for targeted recommendations.</div>"
        )
        return "".join(parts)

    if _is_analytics():
        ename, edata = _find_entity()
        if not ename and entity_names:
            ename, edata = entity_names[0], context[entity_names[0]]
        if edata:
            parts = [f"<div class='ai-section-title'>📊 Analysis: {ename}</div>"]
            status_dist = _status_breakdown(edata)
            if len(status_dist) > 1:
                parts.append(_section("Status Distribution", _bar_chart(status_dist)))
            numeric_insights = []
            if edata:
                for key in edata[0].keys():
                    stats = _numeric_stats(edata, key)
                    if stats and stats["count"] > 1:
                        numeric_insights.append(
                            f"<tr><td>{key.replace('_', ' ').title()}</td>"
                            f"<td>{stats['min']:.1f}</td><td>{stats['max']:.1f}</td>"
                            f"<td>{stats['avg']:.1f}</td></tr>"
                        )
            if numeric_insights:
                parts.append(_section("Numeric Statistics",
                    f"<table class='ai-table'><thead><tr><th>Field</th><th>Min</th><th>Max</th><th>Avg</th></tr></thead>"
                    f"<tbody>{''.join(numeric_insights[:6])}</tbody></table>"
                ))
            if edata:
                for field in ("category","type","priority","severity","asset_type","zone_id","assigned_to"):
                    if field in edata[0]:
                        dist = _field_distribution(edata, field)
                        if len(dist) > 1:
                            parts.append(_section(f"By {field.replace('_', ' ').title()}", _bar_chart(dist, "#005a9e")))
                            break
            insights = []
            needs_action = [r for r in edata if str(r.get("status","")).lower() in ("pending","critical","open","failed","unhealthy","degraded")]
            if needs_action:
                pct = len(needs_action) * 100 // len(edata)
                insights.append(f"⚠️ <strong>{len(needs_action)}</strong> records ({pct}%) need attention")
            resolved = [r for r in edata if str(r.get("status","")).lower() in ("completed","resolved","closed","healthy")]
            if resolved:
                pct = len(resolved) * 100 // len(edata)
                insights.append(f"✅ <strong>{len(resolved)}</strong> records ({pct}%) are resolved/completed")
            if insights:
                parts.append(_section("💡 Key Insights", "<ul>" + "".join(f"<li>{i}</li>" for i in insights) + "</ul>"))
            return "".join(parts)
        return "<div class='ai-hint'>Specify an entity to analyze, e.g. \"analyze incidents\" or \"breakdown sensor status\".</div>"

    if _is_list():
        ename, edata = _find_entity()
        if ename and edata:
            display_keys = [k for k in edata[0].keys() if k != "id"][:6]
            return f"<div class='ai-section-title'>{ename} ({len(edata)} records)</div>" + _table(edata, display_keys)
        parts = [f"<div class='ai-section-title'>All Available Data</div>"]
        for name, records in context.items():
            keys = [k for k in records[0].keys() if k != "id"][:4] if records else []
            parts.append(_section(f"{name} ({len(records)})", _table(records, keys, 3)))
        return "".join(parts)

    if _is_status():
        parts = [f"<div class='ai-greeting'>📋 Platform Status Overview</div>"]
        cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
        parts.append(f"<div class='ai-stats-row'>{cards}</div>")
        all_needs_action = 0
        all_resolved = 0
        for name, records in context.items():
            dist = _status_breakdown(records)
            all_needs_action += sum(v for k, v in dist.items() if k in ("pending","critical","open","failed","unhealthy","degraded"))
            all_resolved += sum(v for k, v in dist.items() if k in ("completed","resolved","closed","healthy"))
        action_color = "#d83b01" if all_needs_action > 0 else "#107c10"
        parts.append(
            f"<div class='ai-stats-row'>"
            + _stat_card("Needs Action", all_needs_action, action_color)
            + _stat_card("Resolved", all_resolved, "#107c10")
            + _stat_card("Total", total_records, "#0078d4")
            + f"</div>"
        )
        parts.append(f"<div class='ai-hint'>✅ All systems operational. Ask about a specific entity for deeper analysis.</div>")
        return "".join(parts)

    # Entity-specific mention fallback
    ename, edata = _find_entity()
    if ename and edata:
        display_keys = [k for k in edata[0].keys() if k != "id"][:5]
        status_dist = _status_breakdown(edata)
        cards = "".join(
            _stat_card(s.title(), c, "#107c10" if s in ("completed","resolved","healthy") else "#d83b01" if s in ("critical","failed") else "#0078d4")
            for s, c in status_dist.items()
        ) if len(status_dist) > 1 else ""
        return (
            f"<div class='ai-section-title'>{ename} — {len(edata)} records</div>"
            + (f"<div class='ai-stats-row'>{cards}</div>" if cards else "")
            + _table(edata, display_keys, 5)
            + f"<div class='ai-hint'>Ask me to \"analyze {ename.lower()}\" for deeper insights, or \"filter by status\".</div>"
        )

    # Conversational fallback — smarter response based on question type
    # Try to give useful data even for unexpected queries
    if any(w in q for w in ("what", "tell", "explain", "describe", "about")):
        ename, edata = _find_entity()
        if ename and edata:
            display_keys = [k for k in edata[0].keys() if k != "id"][:6]
            status_dist = _status_breakdown(edata)
            cards = "".join(
                _stat_card(s.title(), c, "#107c10" if s in ("completed","resolved","healthy") else "#d83b01" if s in ("critical","failed") else "#0078d4")
                for s, c in status_dist.items()
            ) if len(status_dist) > 1 else ""
            sorted_recs = sorted(edata, key=lambda r: str(r.get("created_at", "")), reverse=True)
            return (
                f"<div class='ai-section-title'>{ename} — {len(edata)} records</div>"
                + (f"<div class='ai-stats-row'>{cards}</div>" if cards else "")
                + _table(sorted_recs[:5], display_keys)
                + f"<div class='ai-hint'>Showing 5 most recent records. Try \"analyze {ename.lower()}\" or \"latest {ename.lower()}\".</div>"
            )
    cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
    all_action = sum(
        sum(1 for r in records if str(r.get("status","")).lower() in ("pending","critical","open","failed"))
        for records in context.values()
    )
    return (
        f"<div class='ai-greeting'>🤖 I'm your intelligent data assistant.</div>"
        f"<div class='ai-stats-row'>{cards}</div>"
        f"<div class='ai-hint'>I have <strong>{total_records} records</strong> across "
        f"<strong>{len(entity_names)} entities</strong>"
        + (f" (⚠️ {all_action} need action)" if all_action > 0 else "") +
        f".</div>"
        f"<ul class='ai-suggestions'>"
        f"<li>📋 \"Show latest incidents\" or \"What was the most recent work order?\"</li>"
        f"<li>📊 \"Analyze asset health\" or \"Breakdown sensor status\"</li>"
        f"<li>🔍 \"Which items are critical?\" or \"Find pending requests\"</li>"
        f"<li>💡 \"What should we improve?\" or \"Give me recommendations\"</li>"
        f"<li>📈 \"Compare all entities\" or \"Status across all\"</li></ul>"
    )


SYSTEM_PROMPT = """You are an AI assistant for smart-city-ai-operations-platform-extre.
Project: smart-city-ai-operations-platform-extre
Description: Build an enterprise-grade AI-powered smart city operations platform that orchestrates **9 distinct domain entities** across every supported data store (Cosmos DB, SQL, Blob Storage, Redis, AI Search, 

You have access to the following domain entities:
  - Incident: title, description, category, severity, status, latitude, longitude, zone_id, reporter_name, reporter_phone, affected_population, estimated_damage, ai_confidence, ai_triage_notes, photo_url, audio_transcript, assigned_units, resolution_notes, response_time_minutes\n  - Asset: name, asset_type, status, location_address, latitude, longitude, zone_id, install_date, expected_lifespan_years, manufacturer, model_number, last_inspection_date, health_score, replacement_cost, maintenance_budget, sensor_ids, ai_failure_prediction, ai_health_trend\n  - Sensor: name, sensor_type, status, latitude, longitude, zone_id, asset_id, vendor, protocol, last_reading_value, last_reading_unit, last_reading_timestamp, threshold_min, threshold_max, alert_enabled, battery_level, firmware_version, calibration_date\n  - ServiceRequest: title, description, category, priority, status, citizen_name, citizen_email, citizen_phone, latitude, longitude, zone_id, assigned_team, estimated_completion_date, ai_duplicate_score, ai_category_confidence, ai_suggested_resolution, photo_url, satisfaction_rating\n  - TransitRoute: name, route_number, route_type, status, start_location, end_location, total_stops, daily_ridership, average_delay_minutes, on_time_percentage, fare_revenue_daily, operating_cost_daily, vehicle_count, zone_ids, ai_demand_forecast, ai_optimization_notes, last_disruption_reason\n  - Vehicle: name, vehicle_type, status, license_plate, vin_number, current_latitude, current_longitude, assigned_department, driver_name, fuel_level_pct, odometer_miles, last_maintenance_date, next_maintenance_due, maintenance_cost_ytd, ai_maintenance_prediction, gps_speed_mph, engine_health_score\n  - Zone: name, zone_code, zone_type, status, population, area_sq_miles, council_district, emergency_contacts, active_incident_count, active_sensor_count, active_asset_count, air_quality_index, noise_level_db, power_load_pct, ai_risk_score, ai_trend_summary\n  - WorkOrder: title, description, work_type, priority, status, asset_id, assigned_team, scheduled_date, estimated_hours, actual_hours, parts_cost, labor_cost, total_cost, ai_generated, ai_justification, completion_notes, quality_rating\n  - AuditLog: event_type, agent_name, user_id, user_role, prompt_text, completion_text, token_count_prompt, token_count_completion, latency_ms, model_name, content_safety_result, content_safety_categories, pii_detected, session_id, correlation_id, ip_address, status

When answering questions:
- Use the provided data context to give accurate, specific answers
- Reference actual records and data when relevant
- Provide actionable insights based on the data
- If asked about data you don't have, say so clearly
- Be concise but thorough
"""


class ChatRequest(BaseModel):
    """Chat request with message and optional history."""

    message: str = Field(..., description="User message", max_length=4000)
    conversation_id: str = Field(default="", description="Conversation ID for history")
    history: list[dict] = Field(default_factory=list, description="Previous messages")


class ChatResponse(BaseModel):
    """Chat response from the AI model."""

    reply: str
    model: str
    provider: str = ""
    usage: dict = Field(default_factory=dict)
    context_used: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI model grounded in domain data."""
    # Build structured domain context from repositories
    domain_context = _build_domain_context()
    rag_ext = _search_rag_context(request.message)

    # Try AI provider first, fall back to local data-aware engine
    try:
        get_ai_client()
    except RuntimeError:
        reply = _local_data_reply(request.message, domain_context)
        return ChatResponse(
            reply=reply, model="local-data-engine", provider="local",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            context_used=True,
        )

    # Convert structured context to string for LLM
    context_str = json.dumps(domain_context, default=str, indent=2)
    if rag_ext:
        context_str += "\n\nExternal Knowledge:\n" + rag_ext

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Current data context:\n{context_str}"},
    ]

    # Add conversation history
    for msg in request.history[-10:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    messages.append({"role": "user", "content": request.message})

    result = chat_completion(messages)
    logger.info("ai_chat.complete", extra={"model": result["model"], "tokens": result["usage"].get("total_tokens", 0)})

    return ChatResponse(
        reply=result["reply"],
        model=result["model"],
        provider=result.get("provider", ""),
        usage=result["usage"],
        context_used=bool(domain_context),
    )


@router.get("/models")
async def list_models():
    """List available AI model deployments and provider status."""
    try:
        _, provider = get_ai_client()
        return {
            "chat_model": CHAT_MODEL,
            "provider": provider,
            "status": "available",
        }
    except RuntimeError:
        return {
            "chat_model": CHAT_MODEL,
            "provider": "none",
            "status": "not_configured",
            "help": "Set AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY",
        }


@router.get("/context")
async def get_context():
    """Preview the domain context used for RAG grounding."""
    context = _build_domain_context()
    return {
        "context": context,
        "entities": ['Incident', 'Asset', 'Sensor', 'ServiceRequest', 'TransitRoute', 'Vehicle', 'Zone', 'WorkOrder', 'AuditLog'],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# -- File types and processing strategies ----------------------------
_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp", "image/bmp", "image/tiff"}
_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/webm", "audio/mp4", "audio/x-m4a"}
_DOC_TYPES = {
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json", "text/plain", "text/csv", "text/html", "text/markdown", "text/xml",
    "application/xml",
}
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _detect_file_category(content_type: str, filename: str) -> str:
    """Classify uploaded file into a processing category."""
    ct = (content_type or "").lower()
    fn = (filename or "").lower()

    if ct in _IMAGE_TYPES or fn.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff")):
        return "image"
    if ct in _AUDIO_TYPES or fn.endswith((".mp3", ".wav", ".ogg", ".webm", ".m4a")):
        return "audio"
    if ct == "application/pdf" or fn.endswith(".pdf"):
        return "document"
    if fn.endswith((".xlsx", ".xls")):
        return "spreadsheet"
    if fn.endswith((".csv",)):
        return "csv"
    if ct in _DOC_TYPES or fn.endswith((".txt", ".md", ".html", ".xml", ".json", ".docx")):
        return "text"
    return "binary"


async def _process_image(file_bytes: bytes, filename: str) -> str:
    """Process image using OpenAI Vision (GPT-4o) or description fallback."""
    try:
        client, provider = get_ai_client()
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a document and image analysis assistant for smart-city-ai-operations-platform-extre. Analyze the image and extract all relevant information including text (OCR), objects, data, receipts, invoices, charts, diagrams, or any structured content. Return a detailed analysis."},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Analyze this file: {filename}"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
                ]}
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content or "Image processed but no content extracted."
    except Exception as e:
        logger.warning("ai_upload.image_fallback", extra={"error": str(e)})
        return f"Image received: {filename} ({len(file_bytes)} bytes). AI vision processing unavailable: {e}. Configure an OpenAI-compatible model with vision support."


async def _process_audio(file_bytes: bytes, filename: str) -> str:
    """Process audio using OpenAI Whisper transcription."""
    try:
        client, _ = get_ai_client()
        import io
        audio_file = io.BytesIO(file_bytes)
        audio_file.name = filename

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        text = transcript.text
        # Summarize the transcript
        summary = chat_completion([
            {"role": "system", "content": "You are an assistant for smart-city-ai-operations-platform-extre. Summarize and extract key information from the following audio transcript."},
            {"role": "user", "content": f"Transcript from {filename}:\n\n{text}"},
        ])
        return f"**Transcript:**\n{text}\n\n**Analysis:**\n{summary['reply']}"
    except Exception as e:
        logger.warning("ai_upload.audio_fallback", extra={"error": str(e)})
        return f"Audio received: {filename} ({len(file_bytes)} bytes). Whisper transcription unavailable: {e}."


async def _process_text_content(content: str, filename: str) -> str:
    """Process text-based files (PDF text, CSV, JSON, etc.) through AI analysis."""
    try:
        # Truncate very large files for the context window
        if len(content) > 15000:
            content = content[:15000] + f"\n\n... (truncated, {len(content)} total characters)"

        result = chat_completion([
            {"role": "system", "content": "You are a document analysis assistant for smart-city-ai-operations-platform-extre. Analyze the uploaded file and extract key information, patterns, summaries, and actionable insights. For receipts/invoices, extract line items, totals, dates. For data files, summarize structure and key findings. For documents, provide a comprehensive summary."},
            {"role": "user", "content": f"Analyze this file ({filename}):\n\n{content}"},
        ])
        return result["reply"]
    except Exception as e:
        return f"File received: {filename} ({len(content)} chars). AI analysis unavailable: {e}"


async def _extract_text(file_bytes: bytes, filename: str, category: str) -> str:
    """Extract readable text from various file formats."""
    fn = filename.lower()

    if category == "csv" or fn.endswith(".csv"):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith(".json"):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith((".txt", ".md", ".html", ".xml")):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith(".pdf"):
        # Try basic PDF text extraction 
        text = file_bytes.decode("latin-1", errors="replace")
        # Extract text between stream markers (basic)
        import re
        streams = re.findall(r'BT\s*(.*?)\s*ET', text, re.DOTALL)
        if streams:
            # Extract text operators
            extracted = []
            for stream in streams:
                texts = re.findall(r'\(([^)]+)\)', stream)
                extracted.extend(texts)
            if extracted:
                return " ".join(extracted)
        return f"[PDF file: {len(file_bytes)} bytes - for full extraction configure Azure Document Intelligence]"
    if fn.endswith(".docx"):
        # Basic docx extraction (XML inside zip)
        try:
            import zipfile, io
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                if "word/document.xml" in z.namelist():
                    xml = z.read("word/document.xml").decode("utf-8")
                    import re
                    texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', xml)
                    return " ".join(texts)
        except Exception:
            pass
        return f"[DOCX file: {len(file_bytes)} bytes]"
    if fn.endswith((".xlsx", ".xls")):
        return f"[Spreadsheet: {len(file_bytes)} bytes - upload as CSV for text analysis]"

    return f"[Binary file: {len(file_bytes)} bytes]"


class UploadResponse(BaseModel):
    """Response after file upload and processing."""
    analysis: str
    filename: str
    file_type: str
    size_bytes: int
    model: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process(file: UploadFile = File(...)):
    """Upload and process a file (image, document, audio, receipt, etc.).

    Supports: images (OCR/vision), audio (transcription), PDFs, DOCX,
    CSV, JSON, spreadsheets, receipts, invoices, and text files.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {_MAX_FILE_SIZE // (1024*1024)}MB)")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    category = _detect_file_category(file.content_type or "", file.filename)
    logger.info("ai_upload.processing", extra={
        "filename": file.filename,
        "category": category,
        "size": len(file_bytes),
        "content_type": file.content_type,
    })

    if category == "image":
        analysis = await _process_image(file_bytes, file.filename)
    elif category == "audio":
        analysis = await _process_audio(file_bytes, file.filename)
    else:
        # Text-based processing: extract text then analyze
        text_content = await _extract_text(file_bytes, file.filename, category)
        analysis = await _process_text_content(text_content, file.filename)

    return UploadResponse(
        analysis=analysis,
        filename=file.filename,
        file_type=category,
        size_bytes=len(file_bytes),
        model=CHAT_MODEL,
    )


@router.get("/upload/supported")
async def supported_file_types():
    """List supported file types for upload and processing."""
    return {
        "image": ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"],
        "audio": ["mp3", "wav", "ogg", "webm", "m4a"],
        "document": ["pdf", "docx"],
        "data": ["csv", "json", "xlsx", "xls"],
        "text": ["txt", "md", "html", "xml"],
        "max_size_mb": 20,
        "features": {
            "image": "OCR, receipt/invoice extraction, diagram analysis (via GPT-4o Vision)",
            "audio": "Transcription and summarization (via Whisper)",
            "document": "Text extraction and AI analysis",
            "data": "Structure analysis and insights",
        },
    }
