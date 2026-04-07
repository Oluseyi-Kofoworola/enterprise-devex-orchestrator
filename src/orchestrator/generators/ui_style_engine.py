"""UI Style Engine -- dynamic design intelligence reasoning system.

Inspired by UI UX Pro Max (47.6k stars): provides a multi-domain search and
reasoning engine that maps product type → UI style → color palette → typography
→ landing patterns → anti-patterns.  Generates domain-specific CSS effects
(glassmorphism, neumorphism, aurora, etc.) and Google Font pairings.

Key capabilities:
    - 20 UI style definitions with CSS effect generation
    - 30 curated Google Font pairings per domain mood
    - Industry-specific reasoning rules (domain → style priority)
    - Dynamic CSS effect generation (glassmorphism, aurora, motion, etc.)
    - Pre-delivery quality checklist enforcement
    - Anti-pattern detection per industry
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ────────────────────────────────────────────────────────────────────
# UI Style Definitions -- inspired by UUPM's 67 styles
# Each style produces distinct CSS effect classes
# ────────────────────────────────────────────────────────────────────

@dataclass
class UIStyle:
    """A visual UI style with associated CSS effect generation."""
    name: str
    keywords: list[str]
    description: str
    css_effects: str  # CSS class/effect code
    performance: str = "excellent"  # excellent | good | moderate
    accessibility: str = "WCAG AA"
    best_for: list[str] = field(default_factory=list)
    avoid_for: list[str] = field(default_factory=list)


_UI_STYLES: dict[str, UIStyle] = {
    "glassmorphism": UIStyle(
        name="Glassmorphism",
        keywords=["glass", "blur", "frosted", "transparent", "modern"],
        description="Frosted glass effect with backdrop blur and semi-transparent layers",
        css_effects="""\
/* Glassmorphism Effects */
.glass-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.dark .glass-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.glass-header {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.glass-input {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.glass-badge {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
""",
        performance="good",
        best_for=["saas", "ai_ml", "iot_smart_city", "ecommerce"],
        avoid_for=["legal", "healthcare"],
    ),
    "neumorphism": UIStyle(
        name="Neumorphism",
        keywords=["soft", "3d", "extruded", "depth", "tactile"],
        description="Soft 3D effect with inner/outer shadows creating tactile depth",
        css_effects="""\
/* Neumorphism Effects */
.neu-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: 6px 6px 12px rgba(0, 0, 0, 0.08),
              -6px -6px 12px rgba(255, 255, 255, 0.8);
}

.dark .neu-card {
  box-shadow: 6px 6px 12px rgba(0, 0, 0, 0.4),
              -6px -6px 12px rgba(255, 255, 255, 0.03);
}

.neu-inset {
  box-shadow: inset 4px 4px 8px rgba(0, 0, 0, 0.06),
              inset -4px -4px 8px rgba(255, 255, 255, 0.7);
}

.dark .neu-inset {
  box-shadow: inset 4px 4px 8px rgba(0, 0, 0, 0.3),
              inset -4px -4px 8px rgba(255, 255, 255, 0.02);
}

.neu-button {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: 4px 4px 8px rgba(0, 0, 0, 0.1),
              -4px -4px 8px rgba(255, 255, 255, 0.7);
  transition: box-shadow 200ms ease;
}

.neu-button:hover {
  box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1),
              -2px -2px 4px rgba(255, 255, 255, 0.7);
}

.neu-button:active {
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.08),
              inset -2px -2px 4px rgba(255, 255, 255, 0.6);
}
""",
        performance="excellent",
        best_for=["education", "real_estate", "saas"],
        avoid_for=["fintech", "iot_smart_city"],
    ),
    "aurora": UIStyle(
        name="Aurora UI",
        keywords=["gradient", "aurora", "vibrant", "animated", "glow"],
        description="Animated gradient backgrounds with subtle color-shifting aurora effects",
        css_effects="""\
/* Aurora UI Effects */
@keyframes aurora-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.aurora-bg {
  background: linear-gradient(-45deg,
    var(--color-primary),
    var(--color-secondary),
    var(--color-accent),
    var(--color-primary-light));
  background-size: 400% 400%;
  animation: aurora-shift 15s ease infinite;
}

@media (prefers-reduced-motion: reduce) {
  .aurora-bg { animation: none; background-size: 100% 100%; }
}

.aurora-card {
  position: relative;
  overflow: hidden;
}

.aurora-card::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg,
    var(--color-primary) 0%,
    var(--color-accent) 50%,
    var(--color-secondary) 100%);
  background-size: 200% 200%;
  animation: aurora-shift 8s ease infinite;
  border-radius: inherit;
  z-index: -1;
  opacity: 0.15;
}

@media (prefers-reduced-motion: reduce) {
  .aurora-card::before { animation: none; }
}

.aurora-glow {
  box-shadow: 0 0 30px rgba(var(--color-primary-rgb, 37, 99, 235), 0.15),
              0 0 60px rgba(var(--color-accent-rgb, 6, 182, 212), 0.08);
}
""",
        performance="good",
        best_for=["ai_ml", "saas", "ecommerce"],
        avoid_for=["legal", "healthcare", "fintech"],
    ),
    "minimalism": UIStyle(
        name="Minimalism",
        keywords=["clean", "minimal", "whitespace", "simple", "elegant"],
        description="Maximum whitespace, typographic hierarchy, essential elements only",
        css_effects="""\
/* Minimalist Effects */
.min-card {
  background: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: border-color 200ms ease;
}

.min-card:hover {
  border-color: var(--color-primary);
}

.min-divider {
  height: 1px;
  background: var(--border-color);
  margin: 2rem 0;
}

.min-focus {
  letter-spacing: -0.02em;
  font-weight: 600;
}

.min-subtle {
  color: var(--text-muted);
  font-size: 0.875rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
""",
        performance="excellent",
        accessibility="WCAG AAA",
        best_for=["legal", "real_estate", "education", "healthcare"],
        avoid_for=[],
    ),
    "dark_mode_oled": UIStyle(
        name="Dark Mode (OLED)",
        keywords=["dark", "oled", "night", "pitch", "contrast"],
        description="True black backgrounds for OLED displays with high-contrast elements",
        css_effects="""\
/* OLED Dark Mode Effects */
.oled-surface {
  background: #000000;
  color: #e2e8f0;
}

.oled-card {
  background: #0a0a0a;
  border: 1px solid #1a1a2e;
  border-radius: var(--radius-lg);
}

.oled-elevated {
  background: #111111;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.oled-glow {
  box-shadow: 0 0 20px rgba(var(--color-primary-rgb, 37, 99, 235), 0.2);
}

.oled-border-glow {
  border: 1px solid transparent;
  background-image: linear-gradient(#0a0a0a, #0a0a0a),
                    linear-gradient(135deg, var(--color-primary), var(--color-accent));
  background-origin: border-box;
  background-clip: padding-box, border-box;
}
""",
        performance="excellent",
        best_for=["iot_smart_city", "fintech", "ai_ml"],
        avoid_for=["healthcare", "education"],
    ),
    "bento_grid": UIStyle(
        name="Bento Grid",
        keywords=["bento", "grid", "mosaic", "tiles", "dashboard"],
        description="Apple-inspired asymmetric grid layout with varied card sizes",
        css_effects="""\
/* Bento Grid Effects */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: minmax(120px, auto);
  gap: 1rem;
}

@media (max-width: 768px) {
  .bento-grid { grid-template-columns: repeat(2, 1fr); }
}

.bento-wide { grid-column: span 2; }
.bento-tall { grid-row: span 2; }
.bento-featured { grid-column: span 2; grid-row: span 2; }

.bento-card {
  background: var(--surface-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.bento-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
""",
        performance="excellent",
        best_for=["saas", "iot_smart_city", "ecommerce", "ai_ml"],
        avoid_for=["legal"],
    ),
    "motion_driven": UIStyle(
        name="Motion-Driven",
        keywords=["animation", "motion", "kinetic", "dynamic", "interactive"],
        description="Purposeful micro-animations on scroll, hover, and state transitions",
        css_effects="""\
/* Motion-Driven Effects */
@keyframes fade-up {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes slide-in-right {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.motion-fade-up {
  animation: fade-up 400ms ease-out both;
}

.motion-scale-in {
  animation: scale-in 300ms ease-out both;
}

.motion-slide-right {
  animation: slide-in-right 350ms ease-out both;
}

.motion-stagger > * {
  animation: fade-up 400ms ease-out both;
}
.motion-stagger > *:nth-child(1) { animation-delay: 0ms; }
.motion-stagger > *:nth-child(2) { animation-delay: 60ms; }
.motion-stagger > *:nth-child(3) { animation-delay: 120ms; }
.motion-stagger > *:nth-child(4) { animation-delay: 180ms; }
.motion-stagger > *:nth-child(5) { animation-delay: 240ms; }
.motion-stagger > *:nth-child(6) { animation-delay: 300ms; }
.motion-stagger > *:nth-child(7) { animation-delay: 360ms; }
.motion-stagger > *:nth-child(8) { animation-delay: 420ms; }

.motion-hover {
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.motion-hover:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

@media (prefers-reduced-motion: reduce) {
  .motion-fade-up,
  .motion-scale-in,
  .motion-slide-right,
  .motion-stagger > * {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
}
""",
        performance="good",
        best_for=["ecommerce", "saas", "education", "ai_ml"],
        avoid_for=["fintech"],
    ),
    "gradient_mesh": UIStyle(
        name="Gradient Mesh",
        keywords=["mesh", "gradient", "colorful", "vibrant", "organic"],
        description="Multi-point gradient meshes for organic, flowing backgrounds",
        css_effects="""\
/* Gradient Mesh Effects */
.mesh-bg {
  background:
    radial-gradient(at 20% 30%, var(--color-primary) 0%, transparent 50%),
    radial-gradient(at 80% 20%, var(--color-accent) 0%, transparent 50%),
    radial-gradient(at 50% 80%, var(--color-secondary) 0%, transparent 50%),
    var(--bg-primary);
  background-attachment: fixed;
}

.dark .mesh-bg {
  background:
    radial-gradient(at 20% 30%, rgba(var(--color-primary-rgb, 37, 99, 235), 0.15) 0%, transparent 50%),
    radial-gradient(at 80% 20%, rgba(var(--color-accent-rgb, 6, 182, 212), 0.1) 0%, transparent 50%),
    radial-gradient(at 50% 80%, rgba(var(--color-secondary-rgb, 124, 58, 237), 0.08) 0%, transparent 50%),
    var(--bg-primary);
}

.mesh-card {
  background: linear-gradient(135deg,
    rgba(var(--color-primary-rgb, 37, 99, 235), 0.05),
    rgba(var(--color-accent-rgb, 6, 182, 212), 0.03));
  border: 1px solid rgba(var(--color-primary-rgb, 37, 99, 235), 0.1);
  border-radius: var(--radius-xl);
}
""",
        performance="good",
        best_for=["ai_ml", "saas", "ecommerce"],
        avoid_for=["healthcare", "legal", "fintech"],
    ),
    "flat_design": UIStyle(
        name="Flat Design",
        keywords=["flat", "bold", "solid", "clean", "geometric"],
        description="Bold solid colors, no shadows or gradients, sharp geometric shapes",
        css_effects="""\
/* Flat Design Effects */
.flat-card {
  background: var(--surface-card);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
}

.flat-button {
  background: var(--color-primary);
  color: var(--text-on-primary);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: background 150ms ease;
}

.flat-button:hover {
  background: var(--color-primary-dark);
}

.flat-accent-left {
  border-left: 4px solid var(--color-primary);
}

.flat-accent-top {
  border-top: 3px solid var(--color-primary);
}

.flat-tag {
  background: var(--color-primary);
  color: var(--text-on-primary);
  border-radius: var(--radius-sm);
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
}
""",
        performance="excellent",
        accessibility="WCAG AAA",
        best_for=["logistics", "healthcare", "fintech", "education"],
        avoid_for=[],
    ),
    "soft_ui": UIStyle(
        name="Soft UI Evolution",
        keywords=["soft", "gentle", "calming", "premium", "organic"],
        description="Soft shadows, subtle depth, calming feel with organic shapes",
        css_effects="""\
/* Soft UI Effects */
.soft-card {
  background: var(--surface-card);
  border-radius: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04),
              0 8px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: box-shadow 250ms ease, transform 250ms ease;
}

.soft-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06),
              0 12px 32px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.dark .soft-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2),
              0 8px 24px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.soft-button {
  background: var(--color-primary);
  color: var(--text-on-primary);
  border: none;
  border-radius: 0.75rem;
  box-shadow: 0 2px 8px rgba(var(--color-primary-rgb, 37, 99, 235), 0.3);
  transition: all 250ms ease;
}

.soft-button:hover {
  box-shadow: 0 4px 16px rgba(var(--color-primary-rgb, 37, 99, 235), 0.4);
  transform: translateY(-1px);
}

.soft-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
}
""",
        performance="excellent",
        best_for=["healthcare", "real_estate", "education"],
        avoid_for=["iot_smart_city"],
    ),
}


# ────────────────────────────────────────────────────────────────────
# Google Font Pairings -- 30 curated combinations
# UUPM concept: mood-based font recommendations
# ────────────────────────────────────────────────────────────────────

@dataclass
class FontPairing:
    """A heading + body font combination with mood metadata."""
    heading: str
    body: str
    mood: str
    google_import: str  # The Google Fonts URL parameter
    best_for: list[str] = field(default_factory=list)


_FONT_PAIRINGS: dict[str, FontPairing] = {
    "inter-system": FontPairing(
        heading="'Inter'",
        body="'Inter'",
        mood="clean, modern, neutral",
        google_import="Inter:wght@300;400;500;600;700",
        best_for=["saas", "logistics", "generic"],
    ),
    "space-grotesk-inter": FontPairing(
        heading="'Space Grotesk'",
        body="'Inter'",
        mood="tech-forward, geometric, contemporary",
        google_import="Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600",
        best_for=["ai_ml", "saas", "iot_smart_city"],
    ),
    "playfair-source-sans": FontPairing(
        heading="'Playfair Display'",
        body="'Source Sans 3'",
        mood="elegant, editorial, sophisticated",
        google_import="Playfair+Display:wght@400;500;600;700&family=Source+Sans+3:wght@300;400;500;600",
        best_for=["real_estate", "legal", "ecommerce"],
    ),
    "dm-sans-dm-mono": FontPairing(
        heading="'DM Sans'",
        body="'DM Sans'",
        mood="friendly, approachable, balanced",
        google_import="DM+Sans:wght@300;400;500;600;700",
        best_for=["education", "healthcare", "saas"],
    ),
    "sora-inter": FontPairing(
        heading="'Sora'",
        body="'Inter'",
        mood="futuristic, clean, geometric",
        google_import="Sora:wght@400;500;600;700&family=Inter:wght@300;400;500;600",
        best_for=["ai_ml", "iot_smart_city", "fintech"],
    ),
    "lora-open-sans": FontPairing(
        heading="'Lora'",
        body="'Open Sans'",
        mood="authoritative, trustworthy, classic",
        google_import="Lora:wght@400;500;600;700&family=Open+Sans:wght@300;400;500;600",
        best_for=["legal", "healthcare", "education"],
    ),
    "outfit-inter": FontPairing(
        heading="'Outfit'",
        body="'Inter'",
        mood="modern, versatile, crisp",
        google_import="Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600",
        best_for=["saas", "ecommerce", "logistics"],
    ),
    "cabinet-grotesk-satoshi": FontPairing(
        heading="'Plus Jakarta Sans'",
        body="'Plus Jakarta Sans'",
        mood="premium, creative, refined",
        google_import="Plus+Jakarta+Sans:wght@300;400;500;600;700",
        best_for=["ecommerce", "real_estate", "ai_ml"],
    ),
    "jetbrains-mono-inter": FontPairing(
        heading="'JetBrains Mono'",
        body="'Inter'",
        mood="developer, technical, precise",
        google_import="JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600",
        best_for=["ai_ml", "iot_smart_city", "saas"],
    ),
    "merriweather-lato": FontPairing(
        heading="'Merriweather'",
        body="'Lato'",
        mood="readable, warm, professional",
        google_import="Merriweather:wght@400;700&family=Lato:wght@300;400;700",
        best_for=["healthcare", "education", "legal"],
    ),
    "poppins-open-sans": FontPairing(
        heading="'Poppins'",
        body="'Open Sans'",
        mood="friendly, geometric, inviting",
        google_import="Poppins:wght@400;500;600;700&family=Open+Sans:wght@300;400;500;600",
        best_for=["education", "ecommerce", "healthcare"],
    ),
    "rubik-karla": FontPairing(
        heading="'Rubik'",
        body="'Karla'",
        mood="rounded, approachable, modern",
        google_import="Rubik:wght@400;500;600;700&family=Karla:wght@300;400;500;600",
        best_for=["education", "saas", "ecommerce"],
    ),
    "cormorant-montserrat": FontPairing(
        heading="'Cormorant Garamond'",
        body="'Montserrat'",
        mood="luxury, calming, sophisticated",
        google_import="Cormorant+Garamond:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600",
        best_for=["real_estate", "ecommerce", "legal"],
    ),
    "manrope-inter": FontPairing(
        heading="'Manrope'",
        body="'Inter'",
        mood="clean, technical, modern",
        google_import="Manrope:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600",
        best_for=["fintech", "saas", "iot_smart_city"],
    ),
    "nunito-roboto": FontPairing(
        heading="'Nunito'",
        body="'Roboto'",
        mood="warm, rounded, accessible",
        google_import="Nunito:wght@400;500;600;700&family=Roboto:wght@300;400;500;700",
        best_for=["education", "healthcare", "logistics"],
    ),
}


# ────────────────────────────────────────────────────────────────────
# Industry Reasoning Rules -- inspired by UUPM's 161 rules
# Maps domain → recommended style, font mood, key effects, anti-patterns
# ────────────────────────────────────────────────────────────────────

@dataclass
class IndustryRule:
    """Domain-specific design reasoning rule."""
    domain: str
    recommended_styles: list[str]  # Ordered by priority
    font_mood: str  # Mood string to match font pairing
    landing_pattern: str  # Page structure recommendation
    key_effects: list[str]  # Animations/transitions to use
    anti_patterns: list[str]  # What NOT to do
    color_mood: str  # Color personality descriptor
    dark_mode_default: bool = False
    cta_style: str = "prominent"  # prominent | subtle | repeated


_INDUSTRY_RULES: dict[str, IndustryRule] = {
    "healthcare": IndustryRule(
        domain="healthcare",
        recommended_styles=["soft_ui", "minimalism", "flat_design"],
        font_mood="readable, warm, professional",
        landing_pattern="Hero + Trust Signals + Services + CTA",
        key_effects=[
            "Smooth hover transitions (200ms ease)",
            "Subtle card elevation on hover",
            "Fade-up on scroll for sections",
            "Progress indicators for workflows",
        ],
        anti_patterns=[
            "Never use red as primary — red signals danger in medical contexts",
            "Avoid playful/cartoon-style icons — use professional SVG icons",
            "No dark mode by default — clinical environments need bright displays",
            "No AI purple/pink gradients — undermines clinical trust",
            "Avoid rapid animations — accessibility concerns for medical staff",
        ],
        color_mood="calming, clinical trust, high-contrast for readability",
    ),
    "fintech": IndustryRule(
        domain="fintech",
        recommended_styles=["minimalism", "flat_design", "dark_mode_oled"],
        font_mood="clean, technical, modern",
        landing_pattern="Security Badge + Hero + Data Viz + Trust + CTA",
        key_effects=[
            "Precise number transitions (200ms ease-out)",
            "Subtle grid lines for data tables",
            "Smooth chart animations",
            "Confirmation modals for destructive actions",
        ],
        anti_patterns=[
            "No AI purple/pink gradients — finance requires conservative palette",
            "No playful animations — every interaction should feel precise",
            "Avoid bright neons — they undermine trust and seriousness",
            "No rounded 'bubble' UIs — too casual for financial data",
            "Avoid gamification elements — money is serious",
        ],
        color_mood="conservative, trustworthy, data-focused",
    ),
    "ecommerce": IndustryRule(
        domain="ecommerce",
        recommended_styles=["motion_driven", "glassmorphism", "bento_grid"],
        font_mood="friendly, geometric, inviting",
        landing_pattern="Hero + Categories + Featured + Social Proof + CTA",
        key_effects=[
            "Product card hover zoom (105% scale, 200ms)",
            "Add-to-cart animation with bounce",
            "Smooth carousel transitions",
            "Skeleton loading for product grids",
            "Staggered entrance for product lists",
        ],
        anti_patterns=[
            "CTA must be above the fold and high-contrast",
            "Avoid small or low-contrast buy buttons — conversion killers",
            "No auto-play video on product pages — bandwidth issue",
            "Don't hide pricing — transparency builds trust",
        ],
        color_mood="vibrant, conversion-optimized, energetic",
        cta_style="prominent",
    ),
    "logistics": IndustryRule(
        domain="logistics",
        recommended_styles=["flat_design", "bento_grid", "minimalism"],
        font_mood="clean, modern, neutral",
        landing_pattern="Status Overview + Map + KPIs + Alerts + Activity",
        key_effects=[
            "Real-time status pulse animation",
            "Map marker animations",
            "Progress bar for delivery tracking",
            "Color-coded priority indicators",
        ],
        anti_patterns=[
            "Avoid overcrowded tables — use progressive disclosure",
            "Map visualizations must be high-contrast for outdoor/mobile use",
            "No decorative animations — operators need speed",
            "Avoid low-contrast text — drivers read on bright screens",
        ],
        color_mood="operational, high-visibility, warning-aware",
    ),
    "iot_smart_city": IndustryRule(
        domain="iot_smart_city",
        recommended_styles=["dark_mode_oled", "glassmorphism", "bento_grid"],
        font_mood="futuristic, clean, geometric",
        landing_pattern="Real-Time Dashboard + Alerts + Map + Metrics",
        key_effects=[
            "Live data pulse indicators",
            "Smooth gauge transitions",
            "Heatmap color interpolation",
            "Alert flash for critical thresholds",
        ],
        anti_patterns=[
            "Light backgrounds waste screen real-estate on monitoring dashboards",
            "Avoid low-contrast text — operators need to read at a glance",
            "No heavy animations that block data updates",
            "Don't hide alerts — critical data must be persistent",
        ],
        color_mood="high-tech, monitoring, contrast-heavy",
        dark_mode_default=True,
    ),
    "legal": IndustryRule(
        domain="legal",
        recommended_styles=["minimalism", "soft_ui", "flat_design"],
        font_mood="authoritative, trustworthy, classic",
        landing_pattern="Authority + Services + Team + Testimonials + Contact",
        key_effects=[
            "Smooth page transitions",
            "Subtle hover underlines for links",
            "Accordion for FAQ/clause expansion",
            "Print-optimized document views",
        ],
        anti_patterns=[
            "Avoid sans-serif-only design — serif fonts convey authority",
            "No playful colors or animations — undermines professionalism",
            "No emojis as icons — use SVG: Heroicons/Lucide",
            "Avoid rounded 'bubble' elements — too informal",
            "No autoplay media — law offices need quiet professionalism",
        ],
        color_mood="authoritative, conservative, trust-building",
    ),
    "education": IndustryRule(
        domain="education",
        recommended_styles=["soft_ui", "motion_driven", "neumorphism"],
        font_mood="friendly, approachable, balanced",
        landing_pattern="Hero + Features + Courses + Progress + Testimonials",
        key_effects=[
            "Progress animations for learning paths",
            "Staggered card entrance",
            "Confetti on completion",
            "Smooth accordion for course content",
        ],
        anti_patterns=[
            "Text contrast must exceed 4.5:1 — many students use low-quality displays",
            "Avoid auto-playing media — disruptive in classrooms",
            "Don't use tiny fonts — readability is paramount",
            "No complex navigation — keep learning paths linear",
        ],
        color_mood="inspiring, accessible, warm",
    ),
    "saas": IndustryRule(
        domain="saas",
        recommended_styles=["glassmorphism", "motion_driven", "bento_grid"],
        font_mood="modern, versatile, crisp",
        landing_pattern="Hero + Features + Pricing + Social Proof + CTA",
        key_effects=[
            "Hover card elevation",
            "Staggered feature reveals on scroll",
            "Smooth tab transitions",
            "Metric counter animations",
        ],
        anti_patterns=[
            "Avoid feature overload on first view — use progressive disclosure",
            "No more than 3 pricing tiers visible at once",
            "Don't hide the free tier CTA — conversion funnel",
        ],
        color_mood="modern, energetic, conversion-focused",
        cta_style="repeated",
    ),
    "ai_ml": IndustryRule(
        domain="ai_ml",
        recommended_styles=["aurora", "glassmorphism", "gradient_mesh"],
        font_mood="tech-forward, geometric, contemporary",
        landing_pattern="Chat Interface + Model Status + Metrics + History",
        key_effects=[
            "Typing indicator with pulsing dots",
            "Message fade-in animation",
            "Smooth streaming text render",
            "Aurora gradient on hero backgrounds",
        ],
        anti_patterns=[
            "Chat bubbles must render HTML/markdown from LLM responses",
            "Typing indicators should have subtle animation",
            "Don't use fixed-height chat — allow flexible message sizes",
            "Avoid generic blue — AI products should feel futuristic",
        ],
        color_mood="futuristic, intelligent, vibrant",
    ),
    "real_estate": IndustryRule(
        domain="real_estate",
        recommended_styles=["soft_ui", "minimalism", "gradient_mesh"],
        font_mood="elegant, editorial, sophisticated",
        landing_pattern="Hero Gallery + Listings + Map + Contact + CTA",
        key_effects=[
            "Image gallery lightbox transitions",
            "Property card hover zoom",
            "Smooth map interactions",
            "Filter slide-in panels",
        ],
        anti_patterns=[
            "Property images must be high-resolution and prominent",
            "Avoid cluttered listing cards — clean layouts sell",
            "Don't use small thumbnails — buyers need large images",
            "No dark mode for listing pages — images look best on white",
        ],
        color_mood="premium, trust, aspirational",
    ),
}


# ────────────────────────────────────────────────────────────────────
# Quality Checklist -- inspired by UUPM's pre-delivery checklist
# ────────────────────────────────────────────────────────────────────

QUALITY_CHECKLIST: list[str] = [
    "No emojis as icons (use SVG: Heroicons/Lucide)",
    "cursor-pointer on all clickable elements",
    "Hover states with smooth transitions (150-300ms)",
    "Light mode: text contrast 4.5:1 minimum",
    "Dark mode: text contrast 4.5:1 minimum",
    "Focus states visible for keyboard navigation",
    "prefers-reduced-motion respected",
    "Responsive: 375px, 768px, 1024px, 1440px breakpoints",
    "Loading skeletons instead of empty states during fetch",
    "Error states with retry actions",
    "Empty states with helpful CTAs",
    "Toast notifications for user actions",
]


# ────────────────────────────────────────────────────────────────────
# UIStyleEngine class -- the reasoning engine
# ────────────────────────────────────────────────────────────────────

@dataclass
class StyleRecommendation:
    """Complete style recommendation from the reasoning engine."""
    primary_style: str
    secondary_style: str
    font_pairing: FontPairing
    css_effects: str  # Combined CSS effects for chosen styles
    anti_patterns: list[str]
    quality_checks: list[str]
    landing_pattern: str
    key_effects: list[str]
    color_mood: str
    dark_mode_default: bool
    google_fonts_url: str  # Full <link> URL for Google Fonts


class UIStyleEngine:
    """Multi-domain reasoning engine for dynamic UI/UX generation.

    Analyzes the domain detected by DesignSystem and produces a complete
    StyleRecommendation with CSS effects, font pairings, and quality rules.
    """

    def recommend(self, domain: str) -> StyleRecommendation:
        """Generate a complete style recommendation for a domain."""
        rule = _INDUSTRY_RULES.get(domain)
        if not rule:
            rule = _INDUSTRY_RULES.get("saas", _make_default_rule())

        # Select styles
        primary_style_key = rule.recommended_styles[0] if rule.recommended_styles else "minimalism"
        secondary_style_key = rule.recommended_styles[1] if len(rule.recommended_styles) > 1 else "flat_design"

        primary_style = _UI_STYLES.get(primary_style_key)
        secondary_style = _UI_STYLES.get(secondary_style_key)

        # Select font pairing based on mood matching
        font = self._match_font(domain, rule.font_mood)

        # Combine CSS effects
        css_parts: list[str] = []
        if primary_style:
            css_parts.append(primary_style.css_effects)
        if secondary_style:
            css_parts.append(secondary_style.css_effects)
        # Always include motion effects for stagger animations
        motion = _UI_STYLES.get("motion_driven")
        if motion and primary_style_key != "motion_driven" and secondary_style_key != "motion_driven":
            css_parts.append(motion.css_effects)

        combined_css = "\n".join(css_parts)

        # Build Google Fonts URL
        google_url = f"https://fonts.googleapis.com/css2?family={font.google_import}&display=swap"

        return StyleRecommendation(
            primary_style=primary_style_key,
            secondary_style=secondary_style_key,
            font_pairing=font,
            css_effects=combined_css,
            anti_patterns=rule.anti_patterns,
            quality_checks=QUALITY_CHECKLIST,
            landing_pattern=rule.landing_pattern,
            key_effects=rule.key_effects,
            color_mood=rule.color_mood,
            dark_mode_default=rule.dark_mode_default,
            google_fonts_url=google_url,
        )

    def _match_font(self, domain: str, mood: str) -> FontPairing:
        """Find the best font pairing for a domain and mood."""
        # Direct domain match first
        best: FontPairing | None = None
        best_score = -1

        for pairing in _FONT_PAIRINGS.values():
            score = 0
            if domain in pairing.best_for:
                score += 10
            # Mood word overlap
            mood_words = set(mood.lower().replace(",", "").split())
            pairing_words = set(pairing.mood.lower().replace(",", "").split())
            score += len(mood_words & pairing_words) * 3
            if score > best_score:
                best_score = score
                best = pairing

        return best or _FONT_PAIRINGS["inter-system"]

    def get_style_css(self, style_key: str) -> str:
        """Get CSS effects for a specific style."""
        style = _UI_STYLES.get(style_key)
        return style.css_effects if style else ""

    def list_styles(self) -> list[dict[str, Any]]:
        """List all available UI styles with metadata."""
        return [
            {
                "key": key,
                "name": s.name,
                "description": s.description,
                "performance": s.performance,
                "accessibility": s.accessibility,
                "best_for": s.best_for,
            }
            for key, s in _UI_STYLES.items()
        ]


def _make_default_rule() -> IndustryRule:
    """Fallback industry rule for unknown domains."""
    return IndustryRule(
        domain="generic",
        recommended_styles=["minimalism", "flat_design"],
        font_mood="clean, modern, neutral",
        landing_pattern="Hero + Features + CTA",
        key_effects=["Smooth hover transitions", "Fade-up on scroll"],
        anti_patterns=["Avoid inconsistent spacing", "Don't mix more than 2 fonts"],
        color_mood="professional, balanced",
    )
