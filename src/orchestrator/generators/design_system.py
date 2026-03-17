"""Design System Engine -- domain-aware UI/UX design intelligence.

Inspired by the UI UX Pro Max concept: analyzes project domain/intent and
generates a complete design system with industry-specific colors, typography,
component styles, and anti-patterns to avoid.

Produces CSS custom properties (design tokens) so every generated frontend
has a consistent, professional, WCAG-accessible appearance without any
external design dependency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────
# Domain detection rules (inspired by UUPM's 161 industry categories)
# ────────────────────────────────────────────────────────────────────

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "healthcare": [
        "patient", "clinic", "hospital", "pharmacy", "medical", "health",
        "diagnosis", "prescription", "appointment", "triage", "ehr", "hipaa",
        "lab", "medication", "nurse", "doctor", "vital", "symptom",
    ],
    "fintech": [
        "bank", "payment", "transaction", "account", "ledger", "crypto",
        "wallet", "invoice", "billing", "loan", "insurance", "fintech",
        "portfolio", "trading", "stock", "fund", "compliance", "pci",
    ],
    "ecommerce": [
        "product", "order", "cart", "checkout", "refund", "return",
        "inventory", "catalog", "shipping", "customer", "store", "shop",
        "marketplace", "subscription", "pricing",
    ],
    "logistics": [
        "delivery", "route", "fleet", "vehicle", "shipment", "warehouse",
        "dispatch", "tracking", "supply", "freight", "cargo", "driver",
        "propane", "tank", "schedule",
    ],
    "iot_smart_city": [
        "sensor", "iot", "smart city", "telemetry", "device", "gateway",
        "incident", "alert", "emergency", "dispatch", "infrastructure",
        "citizen", "utility", "grid", "traffic",
    ],
    "legal": [
        "contract", "clause", "review", "legal", "attorney", "case",
        "litigation", "compliance", "regulation", "court", "filing",
    ],
    "education": [
        "student", "course", "enrollment", "grade", "teacher",
        "classroom", "curriculum", "exam", "assignment", "university",
    ],
    "saas": [
        "tenant", "workspace", "team", "project", "task", "board",
        "sprint", "backlog", "feature", "release", "roadmap", "saas",
    ],
    "ai_ml": [
        "agent", "chat", "model", "embedding", "rag", "prompt",
        "inference", "training", "pipeline", "copilot", "assistant",
        "voice", "nlp", "knowledge", "session",
    ],
    "real_estate": [
        "property", "listing", "tenant", "lease", "building", "unit",
        "maintenance", "inspection", "rent", "amenity",
    ],
}


@dataclass
class DesignTokens:
    """Complete set of design tokens for a generated frontend."""

    # Identity
    domain: str = "generic"
    style: str = "modern-professional"

    # Colors
    primary: str = "#2563eb"
    primary_light: str = "#3b82f6"
    primary_dark: str = "#1d4ed8"
    secondary: str = "#7c3aed"
    secondary_light: str = "#8b5cf6"
    accent: str = "#06b6d4"
    success: str = "#10b981"
    warning: str = "#f59e0b"
    danger: str = "#ef4444"
    info: str = "#3b82f6"

    # Surfaces
    bg_primary: str = "#f8fafc"
    bg_secondary: str = "#ffffff"
    bg_tertiary: str = "#f1f5f9"
    surface_card: str = "#ffffff"
    surface_modal: str = "#ffffff"
    border_color: str = "#e2e8f0"
    border_focus: str = "#2563eb"

    # Text
    text_primary: str = "#0f172a"
    text_secondary: str = "#475569"
    text_muted: str = "#94a3b8"
    text_on_primary: str = "#ffffff"
    text_on_dark: str = "#f1f5f9"

    # Dark mode overrides
    dark_bg_primary: str = "#0f172a"
    dark_bg_secondary: str = "#1e293b"
    dark_bg_tertiary: str = "#334155"
    dark_surface_card: str = "#1e293b"
    dark_border: str = "#334155"
    dark_text_primary: str = "#f1f5f9"
    dark_text_secondary: str = "#94a3b8"
    dark_text_muted: str = "#64748b"

    # Typography
    font_heading: str = "'Inter', system-ui, -apple-system, sans-serif"
    font_body: str = "'Inter', system-ui, -apple-system, sans-serif"
    font_mono: str = "'JetBrains Mono', 'Fira Code', monospace"

    # Spacing & rounding
    radius_sm: str = "0.375rem"
    radius_md: str = "0.5rem"
    radius_lg: str = "0.75rem"
    radius_xl: str = "1rem"
    shadow_sm: str = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    shadow_md: str = "0 4px 6px -1px rgb(0 0 0 / 0.1)"
    shadow_lg: str = "0 10px 15px -3px rgb(0 0 0 / 0.1)"

    # Gradient
    gradient_header: str = ""
    gradient_accent: str = ""

    # Chart palette (8 colors for data viz)
    chart_palette: list[str] = field(default_factory=lambda: [
        "#2563eb", "#7c3aed", "#06b6d4", "#10b981",
        "#f59e0b", "#ef4444", "#ec4899", "#8b5cf6",
    ])

    # Layout configuration -- drives dynamic page structure
    # header_style: "gradient" | "solid" | "transparent" | "glass"
    header_style: str = "gradient"
    # kpi_layout: "grid-compact" | "grid-wide" | "horizontal-scroll" | "masonry"
    kpi_layout: str = "grid-compact"
    # kpi_card_style: "flat" | "elevated" | "bordered" | "glass"
    kpi_card_style: str = "bordered"
    # summary_position: "top" | "sidebar" | "inline-header"
    summary_position: str = "top"
    # table_density: "compact" | "comfortable" | "spacious"
    table_density: str = "comfortable"
    # nav_style: "top-bar" | "sidebar" | "top-tabs"
    nav_style: str = "top-bar"
    # kpi_cols: grid column spec for KPI cards
    kpi_cols: str = "grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7"
    # summary_cols: grid column spec for summary metric cards
    summary_cols: str = "grid-cols-2 sm:grid-cols-4"
    # card_radius: border radius class for cards
    card_radius: str = "rounded-xl"
    # font_weight_heading: weight for title text
    font_weight_heading: str = "font-bold"
    # page_max_width: container max-width class
    page_max_width: str = "max-w-7xl"
    # accent_border: whether KPI cards have a colored top accent border
    accent_border: bool = False

    # Anti-patterns
    anti_patterns: list[str] = field(default_factory=list)


# ────────────────────────────────────────────────────────────────────
# Industry-specific design presets
# ────────────────────────────────────────────────────────────────────

_PRESETS: dict[str, dict] = {
    "healthcare": {
        "style": "clinical-trust",
        "primary": "#0891b2",
        "primary_light": "#22d3ee",
        "primary_dark": "#0e7490",
        "secondary": "#0d9488",
        "accent": "#06b6d4",
        "gradient_header": "linear-gradient(135deg, #0891b2 0%, #0d9488 100%)",
        "gradient_accent": "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
        "chart_palette": [
            "#0891b2", "#0d9488", "#06b6d4", "#14b8a6",
            "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899",
        ],
        "header_style": "solid",
        "kpi_layout": "grid-wide",
        "kpi_card_style": "elevated",
        "summary_position": "top",
        "table_density": "spacious",
        "kpi_cols": "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5",
        "summary_cols": "grid-cols-2 sm:grid-cols-4",
        "card_radius": "rounded-2xl",
        "font_weight_heading": "font-bold",
        "page_max_width": "max-w-7xl",
        "accent_border": True,
        "anti_patterns": [
            "Never use red as primary — red signals danger in medical contexts",
            "Avoid playful or cartoon-style icons",
            "No dark mode by default — clinical environments need high-visibility light mode",
        ],
    },
    "fintech": {
        "style": "financial-trust",
        "primary": "#1e40af",
        "primary_light": "#3b82f6",
        "primary_dark": "#1e3a8a",
        "secondary": "#059669",
        "accent": "#d97706",
        "gradient_header": "linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%)",
        "gradient_accent": "linear-gradient(135deg, #059669 0%, #10b981 100%)",
        "chart_palette": [
            "#1e40af", "#059669", "#d97706", "#dc2626",
            "#7c3aed", "#0891b2", "#ec4899", "#f59e0b",
        ],
        "header_style": "solid",
        "kpi_layout": "grid-compact",
        "kpi_card_style": "bordered",
        "summary_position": "sidebar",
        "table_density": "compact",
        "kpi_cols": "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6",
        "summary_cols": "grid-cols-1",
        "card_radius": "rounded-lg",
        "font_weight_heading": "font-semibold",
        "page_max_width": "max-w-screen-2xl",
        "accent_border": False,
        "anti_patterns": [
            "No AI purple/pink gradients — finance requires conservative colors",
            "No playful animations — every micro-interaction should feel precise",
            "Avoid bright neon colors — they undermine trust",
        ],
    },
    "ecommerce": {
        "style": "conversion-optimized",
        "primary": "#7c3aed",
        "primary_light": "#8b5cf6",
        "primary_dark": "#6d28d9",
        "secondary": "#2563eb",
        "accent": "#f59e0b",
        "gradient_header": "linear-gradient(135deg, #7c3aed 0%, #2563eb 100%)",
        "gradient_accent": "linear-gradient(135deg, #f59e0b 0%, #f97316 100%)",
        "chart_palette": [
            "#7c3aed", "#2563eb", "#f59e0b", "#10b981",
            "#ef4444", "#06b6d4", "#ec4899", "#8b5cf6",
        ],
        "header_style": "gradient",
        "kpi_layout": "horizontal-scroll",
        "kpi_card_style": "glass",
        "summary_position": "inline-header",
        "table_density": "comfortable",
        "kpi_cols": "flex overflow-x-auto gap-3 pb-2",
        "summary_cols": "grid-cols-2 sm:grid-cols-4",
        "card_radius": "rounded-2xl",
        "font_weight_heading": "font-extrabold",
        "page_max_width": "max-w-7xl",
        "accent_border": True,
        "anti_patterns": [
            "CTA must be above the fold and high-contrast",
            "Avoid small or low-contrast buttons — conversion killers",
        ],
    },
    "logistics": {
        "style": "operational-clarity",
        "primary": "#ea580c",
        "primary_light": "#f97316",
        "primary_dark": "#c2410c",
        "secondary": "#2563eb",
        "accent": "#0891b2",
        "gradient_header": "linear-gradient(135deg, #ea580c 0%, #dc2626 100%)",
        "gradient_accent": "linear-gradient(135deg, #2563eb 0%, #0891b2 100%)",
        "chart_palette": [
            "#ea580c", "#2563eb", "#0891b2", "#10b981",
            "#f59e0b", "#7c3aed", "#ef4444", "#ec4899",
        ],
        "header_style": "gradient",
        "kpi_layout": "grid-compact",
        "kpi_card_style": "flat",
        "summary_position": "top",
        "table_density": "compact",
        "kpi_cols": "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6",
        "summary_cols": "grid-cols-4",
        "card_radius": "rounded-lg",
        "page_max_width": "max-w-screen-2xl",
        "accent_border": True,
        "anti_patterns": [
            "Avoid overcrowded tables — use progressive disclosure",
            "Map visualizations must be high-contrast for outdoor/mobile use",
        ],
    },
    "iot_smart_city": {
        "style": "tech-dashboard",
        "primary": "#0891b2",
        "primary_light": "#22d3ee",
        "primary_dark": "#0e7490",
        "secondary": "#7c3aed",
        "accent": "#10b981",
        "gradient_header": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        "gradient_accent": "linear-gradient(135deg, #0891b2 0%, #06b6d4 100%)",
        "bg_primary": "#0f172a",
        "bg_secondary": "#1e293b",
        "bg_tertiary": "#334155",
        "surface_card": "#1e293b",
        "border_color": "#334155",
        "text_primary": "#f1f5f9",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",
        "chart_palette": [
            "#22d3ee", "#a78bfa", "#34d399", "#fbbf24",
            "#f87171", "#fb923c", "#c084fc", "#2dd4bf",
        ],
        "header_style": "glass",
        "kpi_layout": "masonry",
        "kpi_card_style": "glass",
        "summary_position": "inline-header",
        "table_density": "compact",
        "kpi_cols": "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5",
        "summary_cols": "grid-cols-2 sm:grid-cols-4",
        "card_radius": "rounded-xl",
        "font_weight_heading": "font-bold",
        "page_max_width": "max-w-screen-2xl",
        "accent_border": False,
        "anti_patterns": [
            "Light backgrounds waste screen real-estate on monitoring dashboards",
            "Avoid low-contrast text — operators need to read at a glance",
        ],
    },
    "legal": {
        "style": "professional-authoritative",
        "primary": "#1e3a5f",
        "primary_light": "#2563eb",
        "primary_dark": "#172554",
        "secondary": "#92400e",
        "accent": "#b45309",
        "gradient_header": "linear-gradient(135deg, #1e3a5f 0%, #172554 100%)",
        "gradient_accent": "linear-gradient(135deg, #92400e 0%, #b45309 100%)",
        "font_heading": "'Lora', 'Georgia', serif",
        "chart_palette": [
            "#1e3a5f", "#92400e", "#b45309", "#2563eb",
            "#059669", "#7c3aed", "#dc2626", "#0891b2",
        ],
        "header_style": "solid",
        "kpi_layout": "grid-wide",
        "kpi_card_style": "bordered",
        "summary_position": "top",
        "table_density": "spacious",
        "kpi_cols": "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
        "summary_cols": "grid-cols-2 sm:grid-cols-4",
        "card_radius": "rounded-lg",
        "font_weight_heading": "font-semibold",
        "page_max_width": "max-w-6xl",
        "accent_border": False,
        "radius_sm": "0.25rem",
        "radius_md": "0.375rem",
        "radius_lg": "0.5rem",
        "radius_xl": "0.75rem",
        "anti_patterns": [
            "Avoid sans-serif-only design — serif fonts convey authority",
            "No playful colors or animations",
            "No emojis as icons — use SVG: Heroicons/Lucide",
        ],
    },
    "education": {
        "style": "accessible-friendly",
        "primary": "#2563eb",
        "primary_light": "#60a5fa",
        "primary_dark": "#1d4ed8",
        "secondary": "#16a34a",
        "accent": "#f59e0b",
        "gradient_header": "linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)",
        "gradient_accent": "linear-gradient(135deg, #16a34a 0%, #059669 100%)",
        "chart_palette": [
            "#2563eb", "#16a34a", "#f59e0b", "#ef4444",
            "#7c3aed", "#0891b2", "#ec4899", "#8b5cf6",
        ],
        "header_style": "gradient",
        "kpi_layout": "grid-wide",
        "kpi_card_style": "elevated",
        "summary_position": "top",
        "table_density": "spacious",
        "kpi_cols": "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5",
        "summary_cols": "grid-cols-2 sm:grid-cols-4",
        "card_radius": "rounded-2xl",
        "font_weight_heading": "font-bold",
        "page_max_width": "max-w-7xl",
        "accent_border": True,
        "radius_xl": "1.25rem",
        "anti_patterns": [
            "Text contrast must exceed 4.5:1 — many students use low-quality displays",
            "Avoid auto-playing media",
        ],
    },
    "saas": {
        "style": "modern-saas",
        "primary": "#6366f1",
        "primary_light": "#818cf8",
        "primary_dark": "#4f46e5",
        "secondary": "#8b5cf6",
        "accent": "#06b6d4",
        "gradient_header": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
        "gradient_accent": "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
        "chart_palette": [
            "#6366f1", "#8b5cf6", "#06b6d4", "#10b981",
            "#f59e0b", "#ef4444", "#ec4899", "#f97316",
        ],
        "header_style": "transparent",
        "kpi_layout": "horizontal-scroll",
        "kpi_card_style": "elevated",
        "summary_position": "inline-header",
        "table_density": "comfortable",
        "kpi_cols": "flex overflow-x-auto gap-3 pb-2",
        "summary_cols": "grid-cols-2 sm:grid-cols-4",
        "card_radius": "rounded-2xl",
        "font_weight_heading": "font-extrabold",
        "page_max_width": "max-w-7xl",
        "accent_border": True,
        "anti_patterns": [
            "Avoid feature overload on first view — use progressive disclosure",
        ],
    },
    "ai_ml": {
        "style": "ai-native",
        "primary": "#7c3aed",
        "primary_light": "#a78bfa",
        "primary_dark": "#6d28d9",
        "secondary": "#2563eb",
        "accent": "#06b6d4",
        "gradient_header": "linear-gradient(135deg, #7c3aed 0%, #2563eb 100%)",
        "gradient_accent": "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
        "chart_palette": [
            "#7c3aed", "#2563eb", "#06b6d4", "#10b981",
            "#f59e0b", "#ef4444", "#ec4899", "#8b5cf6",
        ],
        "header_style": "glass",
        "kpi_layout": "masonry",
        "kpi_card_style": "glass",
        "summary_position": "sidebar",
        "table_density": "comfortable",
        "kpi_cols": "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5",
        "summary_cols": "grid-cols-1",
        "card_radius": "rounded-2xl",
        "font_weight_heading": "font-bold",
        "page_max_width": "max-w-7xl",
        "accent_border": True,
        "anti_patterns": [
            "Chat bubbles must render HTML/markdown from LLM responses",
            "Typing indicators should have subtle animation",
        ],
    },
    "real_estate": {
        "style": "premium-clean",
        "primary": "#0f766e",
        "primary_light": "#14b8a6",
        "primary_dark": "#115e59",
        "secondary": "#b45309",
        "accent": "#d97706",
        "gradient_header": "linear-gradient(135deg, #0f766e 0%, #115e59 100%)",
        "gradient_accent": "linear-gradient(135deg, #b45309 0%, #d97706 100%)",
        "chart_palette": [
            "#0f766e", "#b45309", "#d97706", "#2563eb",
            "#7c3aed", "#ef4444", "#ec4899", "#0891b2",
        ],
        "header_style": "transparent",
        "kpi_layout": "grid-wide",
        "kpi_card_style": "elevated",
        "summary_position": "top",
        "table_density": "spacious",
        "kpi_cols": "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
        "summary_cols": "grid-cols-2 sm:grid-cols-4",
        "card_radius": "rounded-2xl",
        "font_weight_heading": "font-semibold",
        "page_max_width": "max-w-6xl",
        "accent_border": False,
        "shadow_md": "0 8px 16px -4px rgb(0 0 0 / 0.08)",
        "shadow_lg": "0 20px 25px -5px rgb(0 0 0 / 0.1)",
        "anti_patterns": [
            "Property images must be high-resolution and prominent",
            "Avoid cluttered listing cards — clean layouts sell",
        ],
    },
}


class DesignSystem:
    """Analyzes project intent and generates a tailored design system."""

    def detect_domain(self, spec: IntentSpec) -> str:
        """Detect the industry domain from spec entities and description."""
        text = (
            spec.raw_intent.lower()
            + " "
            + " ".join(e.name.lower() for e in spec.entities)
            + " "
            + spec.description.lower()
        )

        scores: dict[str, int] = {}
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", text))
            if score > 0:
                scores[domain] = score

        if not scores:
            return "generic"

        return max(scores, key=scores.get)  # type: ignore[arg-type]

    def generate_tokens(self, spec: IntentSpec) -> DesignTokens:
        """Generate a complete design token set based on project domain."""
        domain = self.detect_domain(spec)
        tokens = DesignTokens(domain=domain)

        preset = _PRESETS.get(domain, {})
        for key, value in preset.items():
            if hasattr(tokens, key):
                setattr(tokens, key, value)

        if not tokens.gradient_header:
            tokens.gradient_header = (
                f"linear-gradient(135deg, {tokens.primary} 0%, {tokens.primary_dark} 100%)"
            )
        if not tokens.gradient_accent:
            tokens.gradient_accent = (
                f"linear-gradient(135deg, {tokens.accent} 0%, {tokens.primary_light} 100%)"
            )

        logger.info("Design system: domain=%s style=%s", domain, tokens.style)
        return tokens

    def generate_css_variables(self, tokens: DesignTokens) -> str:
        """Generate CSS custom properties from design tokens."""
        return f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  /* Design System: {tokens.domain} ({tokens.style}) */
  --color-primary: {tokens.primary};
  --color-primary-light: {tokens.primary_light};
  --color-primary-dark: {tokens.primary_dark};
  --color-secondary: {tokens.secondary};
  --color-secondary-light: {tokens.secondary_light};
  --color-accent: {tokens.accent};
  --color-success: {tokens.success};
  --color-warning: {tokens.warning};
  --color-danger: {tokens.danger};
  --color-info: {tokens.info};

  --bg-primary: {tokens.bg_primary};
  --bg-secondary: {tokens.bg_secondary};
  --bg-tertiary: {tokens.bg_tertiary};
  --surface-card: {tokens.surface_card};
  --surface-modal: {tokens.surface_modal};
  --border-color: {tokens.border_color};
  --border-focus: {tokens.border_focus};

  --text-primary: {tokens.text_primary};
  --text-secondary: {tokens.text_secondary};
  --text-muted: {tokens.text_muted};
  --text-on-primary: {tokens.text_on_primary};

  --font-heading: {tokens.font_heading};
  --font-body: {tokens.font_body};
  --font-mono: {tokens.font_mono};

  --radius-sm: {tokens.radius_sm};
  --radius-md: {tokens.radius_md};
  --radius-lg: {tokens.radius_lg};
  --radius-xl: {tokens.radius_xl};
  --shadow-sm: {tokens.shadow_sm};
  --shadow-md: {tokens.shadow_md};
  --shadow-lg: {tokens.shadow_lg};

  --gradient-header: {tokens.gradient_header};
  --gradient-accent: {tokens.gradient_accent};

  --chart-1: {tokens.chart_palette[0]};
  --chart-2: {tokens.chart_palette[1]};
  --chart-3: {tokens.chart_palette[2]};
  --chart-4: {tokens.chart_palette[3]};
  --chart-5: {tokens.chart_palette[4]};
  --chart-6: {tokens.chart_palette[5]};
  --chart-7: {tokens.chart_palette[6]};
  --chart-8: {tokens.chart_palette[7]};

  /* Layout tokens */
  --header-style: {tokens.header_style};
  --kpi-layout: {tokens.kpi_layout};
  --kpi-card-style: {tokens.kpi_card_style};
  --summary-position: {tokens.summary_position};
  --table-density: {tokens.table_density};
  --nav-style: {tokens.nav_style};
  --card-radius: {tokens.card_radius};
  --font-weight-heading: {tokens.font_weight_heading};
  --page-max-width: {tokens.page_max_width};
}}

/* Dark mode */
@media (prefers-color-scheme: dark) {{
  :root.dark, :root {{
    --bg-primary: {tokens.dark_bg_primary};
    --bg-secondary: {tokens.dark_bg_secondary};
    --bg-tertiary: {tokens.dark_bg_tertiary};
    --surface-card: {tokens.dark_surface_card};
    --surface-modal: {tokens.dark_surface_card};
    --border-color: {tokens.dark_border};
    --text-primary: {tokens.dark_text_primary};
    --text-secondary: {tokens.dark_text_secondary};
    --text-muted: {tokens.dark_text_muted};
  }}
}}

.dark {{
  --bg-primary: {tokens.dark_bg_primary};
  --bg-secondary: {tokens.dark_bg_secondary};
  --bg-tertiary: {tokens.dark_bg_tertiary};
  --surface-card: {tokens.dark_surface_card};
  --surface-modal: {tokens.dark_surface_card};
  --border-color: {tokens.dark_border};
  --text-primary: {tokens.dark_text_primary};
  --text-secondary: {tokens.dark_text_secondary};
  --text-muted: {tokens.dark_text_muted};
}}

/* Base application styles */
body {{
  font-family: var(--font-body);
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-heading);
}}

/* Focus ring for accessibility */
*:focus-visible {{
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
}}

/* Smooth transitions */
button, a, input, select, textarea {{
  transition: all 150ms ease;
}}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }}
}}

/* Loading skeleton animation */
@keyframes shimmer {{
  0% {{ background-position: -200% 0; }}
  100% {{ background-position: 200% 0; }}
}}

.skeleton {{
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--border-color) 50%, var(--bg-tertiary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-md);
}}

/* Toast notification animation */
@keyframes slideIn {{
  from {{ transform: translateX(100%); opacity: 0; }}
  to {{ transform: translateX(0); opacity: 1; }}
}}

.toast {{
  animation: slideIn 300ms ease-out;
}}
"""

    def generate_design_spec(self, spec: IntentSpec) -> dict[str, str]:
        """Generate all design system files for the frontend."""
        tokens = self.generate_tokens(spec)
        return {
            "frontend/src/styles/design-tokens.css": self.generate_css_variables(tokens),
            "frontend/src/styles/design-system.json": self._design_system_json(tokens),
        }

    def _design_system_json(self, tokens: DesignTokens) -> str:
        """Generate machine-readable design system metadata."""
        import json
        data = {
            "domain": tokens.domain,
            "style": tokens.style,
            "colors": {
                "primary": tokens.primary,
                "primaryLight": tokens.primary_light,
                "primaryDark": tokens.primary_dark,
                "secondary": tokens.secondary,
                "accent": tokens.accent,
                "success": tokens.success,
                "warning": tokens.warning,
                "danger": tokens.danger,
            },
            "typography": {
                "heading": tokens.font_heading,
                "body": tokens.font_body,
                "mono": tokens.font_mono,
            },
            "chartPalette": tokens.chart_palette,
            "layout": {
                "headerStyle": tokens.header_style,
                "kpiLayout": tokens.kpi_layout,
                "kpiCardStyle": tokens.kpi_card_style,
                "kpiCols": tokens.kpi_cols,
                "summaryPosition": tokens.summary_position,
                "summaryCols": tokens.summary_cols,
                "tableDensity": tokens.table_density,
                "navStyle": tokens.nav_style,
                "cardRadius": tokens.card_radius,
                "fontWeightHeading": tokens.font_weight_heading,
                "pageMaxWidth": tokens.page_max_width,
                "accentBorder": tokens.accent_border,
            },
            "antiPatterns": tokens.anti_patterns,
        }
        return json.dumps(data, indent=2) + "\n"
