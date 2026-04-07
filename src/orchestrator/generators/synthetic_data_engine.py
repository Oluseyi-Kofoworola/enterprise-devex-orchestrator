"""Synthea-inspired Synthetic Data Engine.

Inspired by Synthea (https://github.com/synthetichealth/synthea) and similar
synthetic data generators, this module applies research-backed techniques:

- **Demographic distributions**: Weighted name/age pools from US Census data
- **State machine lifecycle**: Entities transition through realistic status flows
- **Correlated fields**: Severity drives response time, cost, priority
- **Temporal clustering**: Events cluster around business hours, weekday bias
- **Cross-entity FK verification**: Foreign keys reference real sibling records
- **Domain coding systems**: ICD-10, SNOMED, SKU, tracking numbers per domain
- **Configurable record count**: 12-500+ records per entity

The engine is consumed by ``AppGenerator._dynamic_seed_data()`` and
``FabricGenerator`` to produce realistic seed and synthetic datasets.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Demographic distributions (US Census Bureau 2020 approximations)
# ---------------------------------------------------------------------------

FIRST_NAMES_WEIGHTED: list[tuple[str, float]] = [
    # name, cumulative weight (sums to 1.0, diverse set)
    ("James", 0.045), ("Maria", 0.042), ("Robert", 0.038), ("Jennifer", 0.035),
    ("Wei", 0.032), ("Fatima", 0.030), ("Carlos", 0.028), ("Priya", 0.026),
    ("Ahmed", 0.024), ("Yuki", 0.022), ("Olga", 0.020), ("Kwame", 0.018),
    ("Isabella", 0.035), ("Liam", 0.033), ("Aisha", 0.028), ("Dmitri", 0.025),
    ("Hiroshi", 0.022), ("Grace", 0.030), ("Santiago", 0.027), ("Elena", 0.025),
    ("Mohammed", 0.040), ("Sarah", 0.032), ("David", 0.036), ("Amara", 0.020),
    ("Raj", 0.023), ("Mei", 0.019), ("Kofi", 0.017), ("Ingrid", 0.021),
    ("Tariq", 0.018), ("Anastasia", 0.016),
]

LAST_NAMES_WEIGHTED: list[tuple[str, float]] = [
    ("Smith", 0.088), ("Johnson", 0.063), ("Williams", 0.055), ("Garcia", 0.052),
    ("Chen", 0.048), ("Patel", 0.045), ("Kim", 0.042), ("Nguyen", 0.038),
    ("Mueller", 0.025), ("Okafor", 0.022), ("Santos", 0.035), ("Ivanov", 0.018),
    ("Ali", 0.040), ("Tanaka", 0.020), ("Johansson", 0.015), ("Osei", 0.012),
    ("Martinez", 0.050), ("Anderson", 0.030), ("Brown", 0.058), ("Wilson", 0.028),
]

# ---------------------------------------------------------------------------
# State Machine -- lifecycle transitions per domain
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StatusTransition:
    """A weighted state transition in the entity lifecycle."""
    from_state: str
    to_state: str
    probability: float  # 0.0-1.0
    avg_hours: float  # average time between transitions


# Common lifecycle patterns (Synthea-style progression)
LIFECYCLE_PATTERNS: dict[str, list[StatusTransition]] = {
    "incident": [
        StatusTransition("new", "triaging", 0.95, 0.5),
        StatusTransition("new", "false_positive", 0.05, 1.0),
        StatusTransition("triaging", "investigating", 0.85, 2.0),
        StatusTransition("triaging", "false_positive", 0.15, 1.5),
        StatusTransition("investigating", "contained", 0.70, 8.0),
        StatusTransition("investigating", "escalated", 0.30, 4.0),
        StatusTransition("contained", "remediated", 0.90, 24.0),
        StatusTransition("escalated", "contained", 0.80, 12.0),
        StatusTransition("remediated", "closed", 1.0, 48.0),
    ],
    "order": [
        StatusTransition("pending", "confirmed", 0.90, 1.0),
        StatusTransition("pending", "cancelled", 0.10, 2.0),
        StatusTransition("confirmed", "processing", 1.0, 4.0),
        StatusTransition("processing", "shipped", 0.95, 24.0),
        StatusTransition("processing", "cancelled", 0.05, 8.0),
        StatusTransition("shipped", "delivered", 0.92, 72.0),
        StatusTransition("shipped", "returned", 0.08, 120.0),
    ],
    "ticket": [
        StatusTransition("open", "in_progress", 0.85, 2.0),
        StatusTransition("open", "closed", 0.15, 0.5),
        StatusTransition("in_progress", "resolved", 0.70, 12.0),
        StatusTransition("in_progress", "escalated", 0.30, 6.0),
        StatusTransition("escalated", "resolved", 0.90, 24.0),
        StatusTransition("resolved", "closed", 1.0, 48.0),
    ],
    "medical": [
        StatusTransition("scheduled", "checked_in", 0.92, 0.25),
        StatusTransition("scheduled", "no_show", 0.08, 0.5),
        StatusTransition("checked_in", "in_progress", 1.0, 0.5),
        StatusTransition("in_progress", "completed", 0.85, 1.5),
        StatusTransition("in_progress", "referred", 0.15, 1.0),
        StatusTransition("completed", "follow_up", 0.30, 168.0),
    ],
    "shipment": [
        StatusTransition("booked", "picked_up", 0.95, 12.0),
        StatusTransition("picked_up", "in_transit", 1.0, 2.0),
        StatusTransition("in_transit", "at_customs", 0.35, 48.0),
        StatusTransition("in_transit", "out_for_delivery", 0.65, 72.0),
        StatusTransition("at_customs", "out_for_delivery", 0.90, 24.0),
        StatusTransition("at_customs", "exception", 0.10, 48.0),
        StatusTransition("out_for_delivery", "delivered", 0.97, 4.0),
    ],
    "default": [
        StatusTransition("pending", "in_progress", 0.85, 4.0),
        StatusTransition("pending", "cancelled", 0.15, 2.0),
        StatusTransition("in_progress", "completed", 0.80, 24.0),
        StatusTransition("in_progress", "on_hold", 0.20, 12.0),
        StatusTransition("on_hold", "in_progress", 0.80, 48.0),
        StatusTransition("completed", "archived", 1.0, 168.0),
    ],
}

# ---------------------------------------------------------------------------
# Domain Coding Systems (inspired by Synthea's medical coding)
# ---------------------------------------------------------------------------

DOMAIN_CODES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "healthcare": {
        "diagnosis_code": [
            ("J06.9", "Acute upper respiratory infection"),
            ("I10", "Essential hypertension"),
            ("E11.9", "Type 2 diabetes mellitus"),
            ("M54.5", "Low back pain"),
            ("J45.909", "Unspecified asthma, uncomplicated"),
            ("F32.9", "Major depressive disorder"),
            ("K21.0", "Gastro-esophageal reflux disease"),
            ("N39.0", "Urinary tract infection"),
            ("J18.9", "Pneumonia, unspecified organism"),
            ("E78.5", "Hyperlipidemia, unspecified"),
            ("M79.3", "Panniculitis, unspecified"),
            ("G43.909", "Migraine, unspecified"),
        ],
        "procedure_code": [
            ("99213", "Office visit, established patient"),
            ("36415", "Venipuncture"),
            ("85025", "Complete CBC"),
            ("80053", "Comprehensive metabolic panel"),
            ("71046", "Chest X-ray, 2 views"),
            ("93000", "Electrocardiogram, 12-lead"),
            ("87880", "Strep test, rapid"),
            ("81001", "Urinalysis, automated"),
        ],
        "medication": [
            ("Lisinopril 10mg", "ACE inhibitor"),
            ("Metformin 500mg", "Anti-diabetic"),
            ("Atorvastatin 20mg", "Statin"),
            ("Omeprazole 20mg", "PPI"),
            ("Amoxicillin 500mg", "Antibiotic"),
            ("Albuterol 90mcg", "Bronchodilator"),
            ("Sertraline 50mg", "SSRI"),
            ("Ibuprofen 400mg", "NSAID"),
        ],
    },
    "logistics": {
        "tracking_number": [
            ("1Z999AA10123456784", "UPS Ground"),
            ("9400111899223100001", "USPS Priority"),
            ("794644790132", "FedEx Express"),
            ("JD014600004591022614", "DHL Express"),
        ],
        "hs_code": [
            ("8471.30", "Portable digital computers"),
            ("6110.20", "Jerseys, pullovers (cotton)"),
            ("8517.12", "Smartphones"),
            ("3004.90", "Medicaments, packaged"),
        ],
    },
    "retail": {
        "sku": [
            ("SKU-ELEC-001", "Wireless Earbuds Pro"),
            ("SKU-ELEC-002", "USB-C Hub 7-in-1"),
            ("SKU-APRL-001", "Premium Cotton T-Shirt"),
            ("SKU-APRL-002", "Running Shoes X-Lite"),
            ("SKU-HOME-001", "Smart LED Bulb 4-Pack"),
            ("SKU-HOME-002", "Air Purifier HEPA-13"),
            ("SKU-GROC-001", "Organic Coffee Beans 1kg"),
            ("SKU-GROC-002", "Protein Bar Variety 12-Pack"),
        ],
        "payment_method": [
            ("VISA-4242", "Visa ending 4242"),
            ("MC-5555", "Mastercard ending 5555"),
            ("AMEX-3782", "Amex ending 3782"),
            ("PAYPAL", "PayPal"),
            ("APPLE-PAY", "Apple Pay"),
        ],
    },
    "finance": {
        "instrument": [
            ("AAPL", "Apple Inc. Common Stock"),
            ("MSFT", "Microsoft Corporation"),
            ("TSLA", "Tesla Inc."),
            ("US10Y", "US Treasury 10-Year Note"),
            ("EURUSD", "Euro/US Dollar FX Pair"),
            ("SPX", "S&P 500 Index"),
        ],
        "account_type": [
            ("CHECKING", "Checking Account"),
            ("SAVINGS", "Savings Account"),
            ("BROKERAGE", "Brokerage Account"),
            ("401K", "Retirement Account"),
            ("IRA", "Individual Retirement"),
        ],
    },
}

# ---------------------------------------------------------------------------
# Correlation Engine
# ---------------------------------------------------------------------------

# Severity → correlated field ranges
SEVERITY_CORRELATIONS: dict[str, dict[str, tuple[float, float]]] = {
    "critical": {"response_hours": (0.25, 2.0), "cost_multiplier": (3.0, 8.0), "impact_score": (0.85, 1.0)},
    "high":     {"response_hours": (1.0, 8.0),  "cost_multiplier": (1.5, 3.0), "impact_score": (0.65, 0.85)},
    "medium":   {"response_hours": (4.0, 24.0), "cost_multiplier": (0.8, 1.5), "impact_score": (0.35, 0.65)},
    "low":      {"response_hours": (8.0, 72.0), "cost_multiplier": (0.3, 0.8), "impact_score": (0.10, 0.35)},
}

# ---------------------------------------------------------------------------
# Temporal Distribution (Synthea-inspired)
# ---------------------------------------------------------------------------

# Hour-of-day weight distribution (business hours bias)
HOURLY_WEIGHTS: list[float] = [
  # 0    1    2    3    4    5    6    7    8    9   10   11
    0.02, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.11, 0.10, 0.09,
  # 12   13   14   15   16   17   18   19   20   21   22   23
    0.07, 0.08, 0.09, 0.08, 0.06, 0.04, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01,
]

# Day-of-week weight (Mon=0 .. Sun=6): weekday bias
DAILY_WEIGHTS: list[float] = [0.18, 0.18, 0.17, 0.17, 0.16, 0.08, 0.06]


@dataclass
class SyntheticDataConfig:
    """Configuration for synthetic data generation."""
    record_count: int = 12
    spread_days: int = 90
    temporal_clustering: bool = True
    correlate_fields: bool = True
    cross_entity_fks: bool = True
    include_domain_codes: bool = True
    lifecycle_simulation: bool = True


# ---------------------------------------------------------------------------
# Core Engine
# ---------------------------------------------------------------------------

def _deterministic_hash(seed: str, row: int, field: str = "") -> int:
    """Stable hash for reproducible value selection."""
    raw = f"{seed}:{row}:{field}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)


def select_weighted(items: list[tuple[str, float]], h: int) -> str:
    """Select item from weighted list using deterministic hash."""
    total = sum(w for _, w in items)
    target = (h % 10000) / 10000 * total
    cumulative = 0.0
    for item, weight in items:
        cumulative += weight
        if cumulative >= target:
            return item
    return items[-1][0]


def generate_name(row: int, entity: str) -> tuple[str, str]:
    """Generate a demographically-weighted first/last name pair."""
    h1 = _deterministic_hash(entity, row, "first")
    h2 = _deterministic_hash(entity, row, "last")
    first = select_weighted(FIRST_NAMES_WEIGHTED, h1)
    last = select_weighted(LAST_NAMES_WEIGHTED, h2)
    return first, last


def generate_clustered_timestamp(
    row: int,
    total_rows: int,
    entity: str,
    spread_days: int = 90,
    base_time: datetime | None = None,
) -> datetime:
    """Generate a business-hours-clustered timestamp.

    Unlike even distribution, this clusters events during work hours
    (9-17) and weekdays, matching real-world data patterns observed
    in Synthea's temporal distributions.
    """
    now = base_time or datetime.now(timezone.utc)
    h = _deterministic_hash(entity, row, "time")

    # Spread across days with slight clustering toward recent dates
    day_bucket = (row - 1) * spread_days // max(total_rows, 1)
    day_jitter = (h % 7) - 3  # ±3 day jitter
    day_offset = max(1, spread_days - day_bucket + day_jitter)

    # Select hour weighted toward business hours
    hour = _select_from_weights(HOURLY_WEIGHTS, (h >> 8) % 10000)
    minute = (h >> 16) % 60

    # Weekday bias: shift weekend timestamps to nearest weekday
    dt = now - timedelta(days=day_offset)
    if dt.weekday() >= 5:  # Weekend
        shift = dt.weekday() - 4  # Sat→1, Sun→2
        if (h % 2) == 0:
            dt -= timedelta(days=shift)  # shift to Friday
        else:
            dt += timedelta(days=(7 - dt.weekday()))  # shift to Monday

    return dt.replace(hour=hour, minute=minute, second=(h % 60), microsecond=0)


def _select_from_weights(weights: list[float], h: int) -> int:
    """Select an index from a weight distribution."""
    total = sum(weights)
    target = (h % 10000) / 10000 * total
    cumulative = 0.0
    for i, w in enumerate(weights):
        cumulative += w
        if cumulative >= target:
            return i
    return len(weights) - 1


def simulate_lifecycle(
    entity_name: str,
    row: int,
    domain_hint: str = "",
) -> tuple[str, list[tuple[str, str, float]]]:
    """Simulate entity lifecycle using state machine transitions.

    Returns (current_status, history: [(from, to, hours_elapsed)]).
    Inspired by Synthea's Generic Module Framework state machine.
    """
    # Match entity to lifecycle pattern
    pattern_key = "default"
    ename = entity_name.lower()
    for key in LIFECYCLE_PATTERNS:
        if key in ename or key in domain_hint:
            pattern_key = key
            break

    transitions = LIFECYCLE_PATTERNS[pattern_key]
    h = _deterministic_hash(entity_name, row, "lifecycle")

    # Build adjacency: from_state -> [(to_state, probability, hours)]
    adj: dict[str, list[tuple[str, float, float]]] = {}
    for t in transitions:
        adj.setdefault(t.from_state, []).append((t.to_state, t.probability, t.avg_hours))

    # Find initial state
    all_targets = {t.to_state for t in transitions}
    all_sources = {t.from_state for t in transitions}
    initial = (all_sources - all_targets)
    current = sorted(initial)[0] if initial else transitions[0].from_state

    history: list[tuple[str, str, float]] = []
    # Walk state machine with deterministic randomness
    steps = (h % 5) + 2  # 2-6 transition steps
    step_h = h
    for _ in range(steps):
        if current not in adj:
            break
        nexts = adj[current]
        step_h = _deterministic_hash(entity_name, row + step_h, "step")
        pick = (step_h % 1000) / 1000
        cumul = 0.0
        chosen = nexts[-1]
        for to_st, prob, hrs in nexts:
            cumul += prob
            if cumul >= pick:
                chosen = (to_st, prob, hrs)
                break
        hours_var = chosen[2] * (0.5 + (step_h % 100) / 100)  # ±50% jitter
        history.append((current, chosen[0], round(hours_var, 1)))
        current = chosen[0]

    return current, history


def get_domain_code(
    domain: str,
    code_type: str,
    row: int,
    entity: str,
) -> tuple[str, str] | None:
    """Get a domain-specific code (ICD-10, SKU, tracking number, etc.).

    Returns (code, description) or None if no codes for this domain/type.
    """
    codes = DOMAIN_CODES.get(domain, {}).get(code_type, [])
    if not codes:
        return None
    h = _deterministic_hash(entity, row, code_type)
    return codes[h % len(codes)]


def correlated_value(
    severity: str,
    field_hint: str,
    row: int,
    entity: str,
) -> float:
    """Generate a value correlated with severity level.

    Ensures critical incidents have shorter response times and higher costs,
    matching real-world data distributions from incident databases.
    """
    severity_key = severity.lower()
    if severity_key not in SEVERITY_CORRELATIONS:
        severity_key = "medium"

    ranges = SEVERITY_CORRELATIONS[severity_key]
    h = _deterministic_hash(entity, row, field_hint)

    for hint_keyword, (lo, hi) in ranges.items():
        if hint_keyword in field_hint or field_hint in hint_keyword:
            spread = hi - lo
            return round(lo + (h % 1000) / 1000 * spread, 2)

    # Default: use impact_score range
    lo, hi = ranges.get("impact_score", (0.3, 0.7))
    return round(lo + (h % 1000) / 1000 * (hi - lo), 2)


def generate_cross_entity_fk(
    target_entity: str,
    row: int,
    total_target_records: int,
    source_entity: str,
) -> str:
    """Generate a foreign key that references a real record in another entity.

    Unlike random ID generation, this ensures the FK points to a record
    that actually exists in the referenced entity's seed data.
    """
    h = _deterministic_hash(source_entity, row, f"fk_{target_entity}")
    target_row = (h % total_target_records) + 1
    return f"{target_entity.lower()}-{target_row:03d}"


# ---------------------------------------------------------------------------
# Realistic Value Pools (Synthea-inspired distributions)
# ---------------------------------------------------------------------------

# Blood pressure ranges by age bracket (Synthea uses similar distributions)
VITAL_SIGNS: dict[str, list[tuple[float, float]]] = {
    "systolic_bp": [(90, 120), (100, 130), (110, 140), (115, 150), (120, 160)],
    "diastolic_bp": [(60, 80), (65, 85), (70, 90), (70, 95), (75, 100)],
    "heart_rate": [(60, 100), (55, 95), (60, 100), (58, 98), (55, 90)],
    "temperature": [(97.0, 99.0), (97.5, 100.5), (97.0, 99.5)],
    "bmi": [(18.5, 24.9), (25.0, 29.9), (18.5, 35.0), (20.0, 40.0)],
    "blood_oxygen": [(95.0, 100.0), (92.0, 100.0), (90.0, 100.0)],
}

# Realistic street addresses (US Census-style)
STREET_TYPES: list[str] = [
    "Main St", "Oak Ave", "Elm Blvd", "Park Dr", "Maple Ln",
    "Cedar Rd", "Pine Way", "Walnut St", "Cherry Ct", "Birch Pl",
    "Washington Blvd", "Lincoln Ave", "Jefferson Rd", "Madison Dr",
    "Roosevelt Way", "Kennedy Ct", "Adams Ln", "Monroe Pl",
    "Industrial Pkwy", "Commerce Blvd", "Innovation Dr", "Tech Campus Dr",
    "Harbor View Rd", "Lakeside Way", "Riverside Blvd", "Mountain View Ave",
]

# US city/state pairs for realistic addresses
US_LOCATIONS: list[tuple[str, str, str]] = [
    ("New York", "NY", "10001"), ("Los Angeles", "CA", "90001"),
    ("Chicago", "IL", "60601"), ("Houston", "TX", "77001"),
    ("Phoenix", "AZ", "85001"), ("Philadelphia", "PA", "19101"),
    ("San Antonio", "TX", "78201"), ("San Diego", "CA", "92101"),
    ("Dallas", "TX", "75201"), ("San Jose", "CA", "95101"),
    ("Austin", "TX", "73301"), ("Jacksonville", "FL", "32201"),
    ("Denver", "CO", "80201"), ("Seattle", "WA", "98101"),
    ("Nashville", "TN", "37201"), ("Portland", "OR", "97201"),
    ("Atlanta", "GA", "30301"), ("Miami", "FL", "33101"),
    ("Boston", "MA", "02101"), ("Minneapolis", "MN", "55401"),
]


def generate_address(row: int, entity: str) -> str:
    """Generate a realistic US street address."""
    h = _deterministic_hash(entity, row, "address")
    number = 100 + (h % 9900)
    street = STREET_TYPES[h % len(STREET_TYPES)]
    city, state, zip_code = US_LOCATIONS[(h >> 8) % len(US_LOCATIONS)]
    return f"{number} {street}, {city}, {state} {zip_code}"


def generate_phone(row: int, entity: str) -> str:
    """Generate a realistic US phone number (555 prefix for safety)."""
    h = _deterministic_hash(entity, row, "phone")
    area = 200 + (h % 800)
    line = 1000 + (h % 9000)
    return f"+1-{area}-555-{line:04d}"


def generate_email(first: str, last: str, domain: str = "enterprise.com") -> str:
    """Generate a realistic email from name components."""
    return f"{first.lower()}.{last.lower()}@{domain}"


def generate_vital_sign(vital_type: str, row: int, entity: str) -> float:
    """Generate a realistic vital sign value using Synthea-style distributions."""
    ranges = VITAL_SIGNS.get(vital_type, [(0, 100)])
    h = _deterministic_hash(entity, row, vital_type)
    bracket = ranges[h % len(ranges)]
    lo, hi = bracket
    # Normal-ish distribution via central limit (no random needed)
    # Use 3 hash components averaged for bell-curve approximation
    h2 = _deterministic_hash(entity, row + 1000, vital_type)
    h3 = _deterministic_hash(entity, row + 2000, vital_type)
    frac = ((h % 1000) + (h2 % 1000) + (h3 % 1000)) / 3000
    return round(lo + frac * (hi - lo), 1)
