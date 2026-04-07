"""Advanced Mock Data Engine -- Mockaroo/Datonaut-inspired dynamic data generation.

Replaces the fixed 12-record, linear seed data approach with a configurable,
statistically realistic data generation engine that supports:

    - Configurable record counts (12 to 10,000+)
    - Referential integrity across entities (foreign keys resolve to real IDs)
    - Temporal clustering (bursts, trends, seasonality — not just linear spread)
    - Statistical distributions (normal, zipf, uniform) for numeric fields
    - Uniqueness enforcement (emails, phones, serial numbers never duplicate)
    - Correlation patterns (status correlates with age, priority with severity)
    - Edge cases injection (nulls, empty strings, boundary values)
    - Localized data pools (expanded names, addresses, company names)
    - UUID/GUID generation for ID fields
    - Nested object and enum support
    - Deterministic output via seed-based PRNG (reproducible across runs)

Architecture inspired by Mockaroo's schema-driven approach and Datonaut's
statistical distribution modeling.
"""

from __future__ import annotations

import hashlib
import math
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from src.orchestrator.generators.domain_context import DomainContext
from src.orchestrator.intent_schema import EntitySpec, FieldSpec, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────

@dataclass
class MockDataConfig:
    """Configuration for mock data generation."""

    record_count: int = 12
    spread_days: int = 90
    temporal_pattern: str = "clustered"  # linear | clustered | trending | seasonal
    include_edge_cases: bool = True
    edge_case_ratio: float = 0.08  # 8% of records have edge-case values
    ensure_uniqueness: bool = True
    deterministic_seed: int = 42
    null_ratio: float = 0.05  # 5% chance of null for optional fields
    correlation_enabled: bool = True
    locale: str = "en_US"


@dataclass
class FieldProfile:
    """Statistical profile for a data field — drives realistic generation."""

    distribution: str = "uniform"  # uniform | normal | zipf | cyclic
    min_val: float = 0.0
    max_val: float = 100.0
    mean: float = 50.0
    stddev: float = 15.0
    cardinality: int = 0  # 0 = unlimited; >0 = pick from N unique values
    nullable: bool = False
    unique: bool = False


# ────────────────────────────────────────────────────────────────────
# Expanded data pools (Mockaroo-scale diversity)
# ────────────────────────────────────────────────────────────────────

_FIRST_NAMES = [
    "Alice", "Bob", "Carlos", "Diana", "Erik", "Fatima", "Grace", "Hassan",
    "Irene", "James", "Kira", "Liam", "Maya", "Noah", "Olivia", "Priya",
    "Quinn", "Rafael", "Suki", "Tariq", "Uma", "Viktor", "Wendy", "Xander",
    "Yuki", "Zara", "Amara", "Benjamin", "Chloe", "Darius", "Elena", "Felix",
    "Gabriella", "Hugo", "Isla", "Jasper", "Keiko", "Lorenzo", "Mira", "Nico",
    "Petra", "Rohan", "Sage", "Thalia", "Ulrich", "Valentina", "Wesley",
    "Xiomara", "Youssef", "Zelda",
]

_LAST_NAMES = [
    "Chen", "Smith", "Garcia", "Patel", "Kim", "Johnson", "Williams", "Brown",
    "Jones", "Davis", "Martinez", "Rodriguez", "Lopez", "Gonzalez", "Wilson",
    "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "White", "Harris",
    "Martin", "Thompson", "Young", "Lee", "Walker", "Hall", "Allen", "King",
    "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Mitchell",
    "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans",
    "Edwards", "Collins", "Stewart", "Sanchez", "Morris", "Rogers",
]

_COMPANY_NAMES = [
    "Apex Dynamics", "BlueStar Analytics", "CoreAxis Solutions", "DataVault Systems",
    "Evergreen Technologies", "Falcon Innovations", "GreenPath Energy",
    "HorizonTech Industries", "IntelliCore Systems", "JadeRock Enterprises",
    "Kinetic Solutions Group", "LunarBridge Capital", "Meridian Logistics",
    "NorthStar Digital", "Orion Manufacturing", "PinnacleWorks Global",
    "QuantumLeap AI", "RedCedar Analytics", "SilverLake Partners",
    "TerraFirma Infrastructure", "UnitedFlow Services", "VectorPoint Labs",
    "WaveForm Technologies", "XenonGrid Power", "ZenithCloud Solutions",
]

_STREET_NAMES = [
    "Main St", "Oak Ave", "Elm Blvd", "Park Dr", "River Rd", "Industrial Pkwy",
    "Harbor View", "Tech Campus Dr", "Central Plaza", "Lakeside Way",
    "Market St", "5th Avenue", "Broadway", "Commercial Blvd", "University Dr",
    "Innovation Way", "Maple Lane", "Cedar Ridge Rd", "Sunset Blvd",
    "Pacific Coast Hwy", "Constitution Ave", "Liberty St", "Commerce Dr",
    "Venture Way", "Enterprise Blvd", "Summit Rd", "Valley View Dr",
    "Highland Ave", "Meadow Lane", "Prospect St",
]

_CITIES = [
    "Austin, TX", "Boston, MA", "Chicago, IL", "Denver, CO", "Atlanta, GA",
    "San Francisco, CA", "Seattle, WA", "New York, NY", "Portland, OR",
    "Miami, FL", "Nashville, TN", "Dallas, TX", "Phoenix, AZ", "Charlotte, NC",
    "Minneapolis, MN", "Salt Lake City, UT", "Raleigh, NC", "Detroit, MI",
    "San Diego, CA", "Columbus, OH", "Philadelphia, PA", "Indianapolis, IN",
    "Las Vegas, NV", "Kansas City, MO", "Tampa, FL",
]

_DEPARTMENTS = [
    "Engineering", "Operations", "Finance", "Marketing", "Sales",
    "Human Resources", "Legal", "Product", "Customer Success",
    "Research & Development", "Quality Assurance", "Data Science",
    "Security", "Compliance", "Infrastructure",
]

_MEMO_SUBJECTS = [
    "Quarterly review update", "System maintenance scheduled",
    "New process implementation", "Risk assessment findings",
    "Performance optimization results", "Compliance audit preparation",
    "Resource allocation proposal", "Incident response summary",
    "Strategic initiative briefing", "Vendor evaluation report",
    "Security vulnerability remediation", "Customer feedback analysis",
    "Capacity planning forecast", "Training program rollout",
    "Budget reconciliation notes",
]


# ────────────────────────────────────────────────────────────────────
# Deterministic pseudo-random number generator (no external deps)
# ────────────────────────────────────────────────────────────────────

class _PRNG:
    """Simple multiplicative LCG for deterministic pseudo-random generation."""

    def __init__(self, seed: int = 42):
        self._state = seed & 0xFFFFFFFF

    def _next(self) -> int:
        self._state = (self._state * 1103515245 + 12345) & 0x7FFFFFFF
        return self._state

    def random(self) -> float:
        """Return float in [0.0, 1.0)."""
        return self._next() / 0x7FFFFFFF

    def randint(self, lo: int, hi: int) -> int:
        """Return int in [lo, hi] inclusive."""
        if lo >= hi:
            return lo
        return lo + (self._next() % (hi - lo + 1))

    def choice(self, seq: list) -> Any:
        if not seq:
            return None
        return seq[self._next() % len(seq)]

    def sample(self, seq: list, k: int) -> list:
        """Return k unique items from seq (without replacement)."""
        if k >= len(seq):
            return list(seq)
        pool = list(seq)
        result = []
        for _ in range(k):
            idx = self._next() % len(pool)
            result.append(pool.pop(idx))
        return result

    def gauss(self, mean: float, stddev: float) -> float:
        """Box-Muller transform for normal distribution."""
        u1 = max(1e-10, self.random())
        u2 = self.random()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mean + stddev * z

    def zipf_rank(self, n: int, s: float = 1.1) -> int:
        """Return rank from Zipf distribution (1-indexed, up to n)."""
        u = max(1e-10, self.random())
        return min(n, max(1, int(1.0 / (u ** (1.0 / s)))))


# ────────────────────────────────────────────────────────────────────
# Temporal pattern generators
# ────────────────────────────────────────────────────────────────────

def _timestamps_linear(count: int, spread_days: int, rng: _PRNG) -> list[str]:
    """Evenly spaced timestamps (original behavior)."""
    now = datetime.now(timezone.utc)
    timestamps = []
    for i in range(count):
        offset = spread_days - i * (spread_days // max(count, 1))
        offset = max(1, offset)
        hour = 6 + (i * 3) % 16
        minute = (i * 17) % 60
        dt = now - timedelta(days=offset, hours=24 - hour, minutes=60 - minute)
        timestamps.append(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return timestamps


def _timestamps_clustered(count: int, spread_days: int, rng: _PRNG) -> list[str]:
    """Cluster timestamps around 3-5 hotspots (simulates incident bursts)."""
    now = datetime.now(timezone.utc)
    num_clusters = min(5, max(2, count // 4))
    cluster_centers = sorted([rng.randint(2, spread_days - 2) for _ in range(num_clusters)])
    timestamps = []
    for i in range(count):
        center = cluster_centers[i % num_clusters]
        spread = rng.gauss(0, spread_days / (num_clusters * 3))
        day_offset = max(1, min(spread_days, int(center + spread)))
        hour = rng.randint(6, 22)
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        dt = now - timedelta(days=day_offset, hours=24 - hour, minutes=60 - minute, seconds=second)
        timestamps.append(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    timestamps.sort()
    return timestamps


def _timestamps_trending(count: int, spread_days: int, rng: _PRNG) -> list[str]:
    """More recent records are denser (exponential growth pattern)."""
    now = datetime.now(timezone.utc)
    timestamps = []
    for i in range(count):
        # Exponential decay -- more records near present
        t = (i / max(count - 1, 1))
        day_offset = int(spread_days * (1 - t ** 2))
        day_offset = max(0, min(spread_days, day_offset))
        hour = rng.randint(7, 21)
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        dt = now - timedelta(days=day_offset, hours=24 - hour, minutes=minute, seconds=second)
        timestamps.append(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    timestamps.sort()
    return timestamps


def _timestamps_seasonal(count: int, spread_days: int, rng: _PRNG) -> list[str]:
    """Sinusoidal pattern -- simulates business-hours / weekday clustering."""
    now = datetime.now(timezone.utc)
    timestamps = []
    for i in range(count):
        base_offset = spread_days - i * (spread_days // max(count, 1))
        base_offset = max(0, base_offset)
        # Add sinusoidal jitter: peaks at start/middle/end of week
        wave = math.sin(2 * math.pi * i / 7) * (spread_days / 10)
        day_offset = max(0, min(spread_days, int(base_offset + wave)))
        # Business hours: 8-18 with higher probability
        hour = int(rng.gauss(13, 3))
        hour = max(7, min(21, hour))
        minute = rng.randint(0, 59)
        dt = now - timedelta(days=day_offset, hours=24 - hour, minutes=minute)
        timestamps.append(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    timestamps.sort()
    return timestamps


_TIMESTAMP_GENERATORS = {
    "linear": _timestamps_linear,
    "clustered": _timestamps_clustered,
    "trending": _timestamps_trending,
    "seasonal": _timestamps_seasonal,
}


# ────────────────────────────────────────────────────────────────────
# Advanced value generators (by field pattern)
# ────────────────────────────────────────────────────────────────────

class MockValueGenerator:
    """Generates realistic field values with statistical distributions."""

    def __init__(
        self,
        rng: _PRNG,
        domain_ctx: DomainContext | None = None,
        config: MockDataConfig | None = None,
    ):
        self._rng = rng
        self._ctx = domain_ctx
        self._cfg = config or MockDataConfig()
        self._used_emails: set[str] = set()
        self._used_phones: set[str] = set()
        self._used_serials: set[str] = set()
        self._used_uuids: set[str] = set()
        self._entity_ids: dict[str, list[str]] = {}  # entity_name -> list of generated IDs

    def register_entity_ids(self, entity_name: str, ids: list[str]) -> None:
        """Register generated IDs for cross-entity referential integrity."""
        self._entity_ids[entity_name.lower()] = ids

    def generate_id(self, entity_name: str, row: int, use_uuid: bool = False) -> str:
        """Generate a unique ID for an entity record."""
        sn = entity_name.lower().replace(" ", "_")
        abbr = sn[:3].upper()
        if use_uuid:
            uid = str(uuid.UUID(int=self._rng._next() | (row << 32)))
            return uid
        return f"{sn}-{row:03d}"

    def generate(
        self,
        field_spec: FieldSpec,
        entity_name: str,
        row: int,
        total_rows: int,
        timestamps: list[str] | None = None,
    ) -> str:
        """Generate a single field value -- the main entry point."""
        name = field_spec.name
        ftype = field_spec.type

        # Edge cases: inject nulls for optional fields
        # List and dict fields get empty collections instead of None
        # to avoid Pydantic validation errors in response schemas
        if (self._cfg.include_edge_cases
                and not field_spec.required
                and self._rng.random() < self._cfg.null_ratio):
            if ftype in ("list", "list[str]", "list[int]", "list[float]"):
                return "[]"
            if ftype == "dict":
                return "{}"
            return "None"

        # Delegate to type-specific generators
        if ftype == "float":
            return self._gen_float(name, entity_name, row, total_rows)
        if ftype == "int":
            return self._gen_int(name, entity_name, row, total_rows)
        if ftype == "bool":
            return self._gen_bool(name, row, total_rows)
        if ftype == "datetime":
            if timestamps and row - 1 < len(timestamps):
                return f'"{timestamps[row - 1]}"'
            return f'"{_timestamps_linear(total_rows, 90, self._rng)[row - 1]}"'
        if ftype in ("list", "list[str]"):
            return self._gen_list_str(name, entity_name, row)
        if ftype == "list[int]":
            count = self._rng.randint(1, 4)
            vals = [str(self._rng.randint(1, 100)) for _ in range(count)]
            return f'[{", ".join(vals)}]'
        if ftype == "list[float]":
            count = self._rng.randint(1, 4)
            vals = [f"{self._rng.random() * 100:.1f}" for _ in range(count)]
            return f'[{", ".join(vals)}]'
        if ftype == "dict":
            return self._gen_dict(name, entity_name, row)

        # String type (default)
        return self._gen_string(name, entity_name, row, total_rows, timestamps)

    # ── String generation ───────────────────────────────────────────

    def _gen_string(
        self,
        name: str,
        entity_name: str,
        row: int,
        total_rows: int,
        timestamps: list[str] | None = None,
    ) -> str:
        ename_lower = entity_name.lower()
        ctx = self._ctx

        _first = ctx.first_names if ctx and ctx.first_names else _FIRST_NAMES
        _last = ctx.last_names if ctx and ctx.last_names else _LAST_NAMES
        _streets = ctx.streets if ctx and ctx.streets else _STREET_NAMES
        _cities = ctx.cities if ctx and ctx.cities else _CITIES
        _email_domain = ctx.email_domains[0] if ctx and ctx.email_domains else "enterprise.com"
        _portal = ctx.portal_urls[0] if ctx and ctx.portal_urls else "https://portal.enterprise.com"
        _vendors = ctx.vendors if ctx else _COMPANY_NAMES
        _sources = ctx.source_systems if ctx else ["API", "web-portal", "mobile-app", "batch-import"]
        _statuses = ctx.statuses if ctx and ctx.statuses else ["pending", "in_progress", "completed", "active", "critical", "resolved"]
        _categories = ctx.categories if ctx and ctx.categories else ["general", "maintenance", "operations", "planning"]
        _priorities = ctx.priorities if ctx and ctx.priorities else ["critical", "high", "medium", "low"]
        _terminology = ctx.terminology if ctx else {}
        _desc_templates = ctx.description_templates if ctx else [
            "Operation {} initiated. Standard procedures apply.",
            "Scheduled activity for {} completed successfully.",
            "Follow-up inspection after {} event. Status updated.",
        ]

        # === Field name pattern matching (expanded from original 40+ to 60+) ===

        # Status / state -- use Zipf distribution (most records are "active/completed")
        if name == "status" or name.endswith("_status") or name == "state":
            if self._cfg.correlation_enabled and total_rows > 6:
                # Zipf: "completed" is most common, "critical" is rare
                rank = self._rng.zipf_rank(len(_statuses))
                return f'"{_statuses[min(rank - 1, len(_statuses) - 1)]}"'
            return f'"{self._rng.choice(_statuses)}"'

        # ID and foreign key fields
        if name == "id":
            return f'"{self.generate_id(entity_name, row)}"'
        if name.endswith("_id"):
            ref_entity = name[:-3].lower()
            # Foreign key: reference actual IDs if available
            if ref_entity in self._entity_ids and self._entity_ids[ref_entity]:
                ref_id = self._rng.choice(self._entity_ids[ref_entity])
                return f'"{ref_id}"'
            ref_abbr = ref_entity[:3].upper() if ref_entity else "REF"
            return f'"{ref_abbr}-{self._rng.randint(1, max(total_rows, 20)):03d}"'

        # UUID / GUID fields
        if name in ("uuid", "guid", "external_id", "correlation_id", "trace_id", "request_id", "session_id"):
            uid = str(uuid.UUID(int=self._rng._next() | (row << 48)))
            return f'"{uid}"'

        # Priority / severity -- Zipf (most are medium/low)
        if name in ("priority", "severity", "urgency"):
            rank = self._rng.zipf_rank(len(_priorities))
            return f'"{_priorities[min(rank - 1, len(_priorities) - 1)]}"'

        # Level / tier
        if name in ("level", "tier", "grade"):
            grades = ["platinum", "gold", "silver", "bronze"]
            rank = self._rng.zipf_rank(len(grades))
            return f'"{grades[min(rank - 1, len(grades) - 1)]}"'

        # Type / category -- use domain terminology
        if name in ("type", "category", "kind", "class") or name.endswith("_type") or name.endswith("_category"):
            pool = _terminology.get(name, _categories)
            return f'"{self._rng.choice(pool)}"'

        # Name / title -- rich compound names
        if name in ("name", "title", "label", "subject"):
            descriptors = [
                "Urgent", "Routine", "Critical", "Scheduled", "Priority",
                "Emergency", "Standard", "Compliance", "Strategic", "Preventive",
                "Assessment", "Quarterly", "Annual", "Ad-hoc", "Follow-up",
            ]
            subjects = _MEMO_SUBJECTS
            d = self._rng.choice(descriptors)
            s = self._rng.choice(subjects)
            return f'"{d}: {s}"'

        # Description / summary
        if name in ("description", "summary", "details", "notes", "comment", "remarks", "body"):
            t = self._rng.choice(_desc_templates)
            fill = self._rng.choice(_cities if _cities else ["the facility"])
            return f'"{t.format(fill)}"'

        # Reason / cause
        if name in ("reason", "cause", "justification", "rationale"):
            reasons = [
                "Equipment failure requiring immediate attention",
                "Scheduled upgrade per maintenance calendar",
                "Safety compliance requirement identified",
                "Performance degradation detected by monitoring",
                "Customer-reported issue verified by field team",
                "Regulatory audit finding — remediation required",
                "Capacity threshold exceeded during peak hours",
                "Vendor-recommended preventive maintenance",
                "Cost optimization opportunity identified",
                "End-of-life replacement per lifecycle policy",
            ]
            return f'"{self._rng.choice(reasons)}"'

        # Email -- unique enforcement
        if name in ("email", "contact_email", "user_email") or name.endswith("_email"):
            for _ in range(50):  # try to find unique
                fn = self._rng.choice(_first).lower()
                ln = self._rng.choice(_last).lower()
                suffix = f"{self._rng.randint(1, 999)}" if row > len(_first) else ""
                email = f"{fn}.{ln}{suffix}@{_email_domain}"
                if email not in self._used_emails or not self._cfg.ensure_uniqueness:
                    self._used_emails.add(email)
                    return f'"{email}"'
            fallback = f"user{row}@{_email_domain}"
            self._used_emails.add(fallback)
            return f'"{fallback}"'

        # First / last name
        if name in ("first_name", "given_name"):
            return f'"{self._rng.choice(_first)}"'
        if name in ("last_name", "family_name", "surname"):
            return f'"{self._rng.choice(_last)}"'

        # Full name fields
        if name.endswith("_name") or name in (
            "reporter_name", "assigned_to", "operator", "technician",
            "requester", "agent_name", "user_name", "created_by",
            "updated_by", "reviewer", "approver", "owner",
        ):
            fn = self._rng.choice(_first)
            ln = self._rng.choice(_last)
            return f'"{fn} {ln}"'

        # Phone -- unique enforcement
        if name in ("phone", "phone_number", "contact_phone") or name.endswith("_phone"):
            for _ in range(50):
                area = self._rng.randint(200, 999)
                mid = self._rng.randint(100, 999)
                last = self._rng.randint(1000, 9999)
                phone = f"+1-{area}-{mid}-{last}"
                if phone not in self._used_phones or not self._cfg.ensure_uniqueness:
                    self._used_phones.add(phone)
                    return f'"{phone}"'
            return f'"+1-555-{row:03d}-{1000 + row:04d}"'

        # Address / location
        if name in ("location", "address", "place", "site") or "location" in name or "address" in name:
            num = self._rng.randint(100, 9999)
            street = self._rng.choice(_streets)
            city = self._rng.choice(_cities)
            return f'"{num} {street}, {city}"'

        # URL fields
        if name in ("url", "link", "website", "homepage") or name.endswith("_url"):
            return f'"{_portal}/{ename_lower}/{row:04d}"'

        # IP address
        if name in ("ip", "ip_address", "client_ip", "source_ip"):
            a = 10
            b = self._rng.randint(0, 255)
            c = self._rng.randint(0, 255)
            d = self._rng.randint(1, 254)
            return f'"{a}.{b}.{c}.{d}"'

        # Version
        if name in ("version", "revision", "api_version"):
            major = self._rng.randint(1, 5)
            minor = self._rng.randint(0, 20)
            patch = self._rng.randint(0, 30)
            return f'"v{major}.{minor}.{patch}"'

        # Serial / code -- unique enforcement
        if name.startswith("serial") or name.endswith("_number") or name == "code":
            abbr = ename_lower[:3].upper()
            for _ in range(50):
                serial = f"{abbr}-{self._rng.randint(10000, 99999)}"
                if serial not in self._used_serials or not self._cfg.ensure_uniqueness:
                    self._used_serials.add(serial)
                    return f'"{serial}"'
            return f'"{abbr}-{row:05d}"'

        # Color
        if name in ("color", "colour"):
            colors = [
                "red", "blue", "green", "orange", "purple", "teal",
                "indigo", "amber", "emerald", "slate",
            ]
            return f'"{self._rng.choice(colors)}"'

        # Tags
        if name in ("tag", "tags", "labels"):
            tag_pool = ["urgent", "follow-up", "reviewed", "automated",
                        "manual", "flagged", "archived", "escalated"]
            n = self._rng.randint(1, 3)
            tags = self._rng.sample(tag_pool, n)
            return f'"{", ".join(tags)}"'

        # Role / permission
        if name in ("role", "permission") or name.endswith("_role"):
            roles = [
                "operator", "supervisor", "technician", "analyst", "manager",
                "administrator", "auditor", "engineer", "coordinator", "director",
                "specialist", "lead", "intern", "consultant", "architect",
            ]
            return f'"{self._rng.choice(roles)}"'

        # Source / origin
        if name in ("source", "origin", "provider", "channel"):
            return f'"{self._rng.choice(_sources)}"'

        # Target / destination
        if name in ("target", "destination"):
            return f'"{self._rng.choice(_cities)}"'

        # Currency
        if name in ("currency", "currency_code"):
            currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]
            return f'"{self._rng.choice(currencies)}"'

        # Country
        if name in ("country", "country_code"):
            countries = ["US", "GB", "DE", "JP", "CA", "AU", "FR", "IN", "BR", "KR"]
            return f'"{self._rng.choice(countries)}"'

        # Region / zone
        if name in ("region", "zone", "area", "district", "sector"):
            return f'"{self._rng.choice(_cities)}"'

        # Department / team
        if name in ("department", "team", "division", "unit", "group") or name.endswith("_team") or name.endswith("_department"):
            return f'"{self._rng.choice(_DEPARTMENTS)}"'

        # Company / organization
        if name in ("company", "organization", "org", "employer", "client"):
            return f'"{self._rng.choice(_COMPANY_NAMES)}"'

        # Date/timestamp strings
        if "date" in name or "timestamp" in name or name in ("created", "updated") or name.endswith("_date") or name.endswith("_at"):
            if timestamps and row - 1 < len(timestamps):
                return f'"{timestamps[row - 1]}"'
            ts = _timestamps_linear(total_rows, 90, self._rng)
            return f'"{ts[min(row - 1, len(ts) - 1)]}"'

        # Amount / price / cost (string representation)
        if "amount" in name or "price" in name or "cost" in name or name in ("fee", "total", "balance", "revenue"):
            val = abs(self._rng.gauss(5000, 3000))
            return f'"{val:.2f}"'

        # Transcript / notes
        if "transcript" in name or "notes" in name or "log" in name:
            notes = [
                "Initial assessment complete. Dispatching repair crew.",
                "On-site inspection confirmed. Severity upgraded to high.",
                "Monitoring active. No further escalation needed at this time.",
                "Parts ordered from vendor. Estimated arrival in 48 hours.",
                "Resolved via remote diagnostics. System restored to operational status.",
                "Awaiting follow-up confirmation. Case remains open per protocol.",
                "Cross-department coordination meeting scheduled for tomorrow.",
                "Final review submitted. Pending supervisor approval.",
                "Emergency protocol activated. All available units notified.",
                "Routine check passed. Next scheduled review in 30 days.",
            ]
            return f'"{self._rng.choice(notes)}"'

        # Vendor / manufacturer
        if "manufacturer" in name or "vendor" in name or "brand" in name or "supplier" in name:
            return f'"{self._rng.choice(_vendors)}"'

        # Method
        if name in ("method", "approach", "technique", "strategy", "protocol"):
            methods = [
                "standard-procedure", "automated-workflow", "manual-review",
                "risk-based-approach", "cost-optimized", "fast-track",
                "compliance-driven", "data-driven", "hybrid-approach",
            ]
            return f'"{self._rng.choice(methods)}"'

        # Boolean-as-string
        if name.startswith("is_") or name.startswith("has_") or name.startswith("can_"):
            return f'"{"true" if self._rng.random() > 0.4 else "false"}"'

        # Enum-like fields detected by common suffixes
        if name.endswith("_mode") or name.endswith("_format") or name.endswith("_protocol"):
            modes = ["standard", "enhanced", "legacy", "experimental", "optimized"]
            return f'"{self._rng.choice(modes)}"'

        # Firmware version
        if "firmware" in name:
            major = self._rng.randint(1, 4)
            minor = self._rng.randint(0, 12)
            patch = self._rng.randint(0, 50)
            return f'"fw-{major}.{minor}.{patch}"'

        # Zone / area code
        if name.endswith("_code") or name == "code":
            prefixes = ["ZN", "AR", "SC", "DT", "NW", "SE", "HB", "IN", "PK", "RV"]
            return f'"{self._rng.choice(prefixes)}-{self._rng.randint(100, 999)}"'

        # License plate
        if "license" in name or "plate" in name or "registration" in name:
            letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
            l1 = letters[self._rng.randint(0, len(letters) - 1)]
            l2 = letters[self._rng.randint(0, len(letters) - 1)]
            l3 = letters[self._rng.randint(0, len(letters) - 1)]
            return f'"{l1}{l2}{l3}-{self._rng.randint(1000, 9999)}"'

        # Protocol
        if name == "protocol" or name.endswith("_protocol"):
            protocols = ["MQTT", "HTTP", "CoAP", "AMQP", "Modbus", "BACnet", "OPC-UA", "Zigbee", "LoRaWAN", "BLE"]
            return f'"{self._rng.choice(protocols)}"'

        # Unit of measurement
        if "unit" in name:
            units = ["celsius", "fahrenheit", "psi", "kPa", "lux", "dB", "ppm", "mg/L", "kWh", "m/s", "mph", "gallons", "liters"]
            return f'"{self._rng.choice(units)}"'

        # Model / make (hardware)
        if name in ("model", "make", "device_model", "hardware_model", "sensor_model"):
            models = ["SensorPro-X1", "IoTEdge-3000", "SmartNode-V2", "EnviroMon-500", "FlowMaster-200",
                      "ThermoGuard-Elite", "AirWatch-Pro", "GridSense-7", "AquaScan-100", "TrafficEye-4K"]
            return f'"{self._rng.choice(models)}"'

        # AI prediction / suggestion fields
        if name.startswith("ai_") or "prediction" in name or "recommendation" in name:
            predictions = [
                "Predictive analysis indicates normal operating conditions for next 72 hours",
                "Anomaly detected — recommend preventive maintenance within 14 days",
                "Pattern suggests increased load during peak hours — consider scaling",
                "Performance trending downward — schedule inspection before next cycle",
                "All parameters within expected ranges — no action required",
                "Historical pattern match: similar conditions resolved with firmware update",
                "Risk assessment: low probability of failure in current operating window",
                "Recommend replacing component based on wear pattern analysis",
                "Seasonal adjustment suggested based on 12-month trend analysis",
                "Optimization opportunity: adjusting threshold could reduce false alarms by 30%",
            ]
            return f'"{self._rng.choice(predictions)}"'

        # Generic fallback -- contextual
        return f'"{ename_lower}-{name}-{row:03d}"'

    # ── Numeric generation ──────────────────────────────────────────

    def _gen_float(self, name: str, entity_name: str, row: int, total_rows: int) -> str:
        # Confidence / score / health -- beta-like distribution (0.3 to 1.0)
        if "confidence" in name or "score" in name or "health" in name or "accuracy" in name:
            val = 0.3 + abs(self._rng.gauss(0.35, 0.15))
            return f"{min(1.0, val):.2f}"

        # Latitude / longitude -- realistic coordinates
        if "latitude" in name or "lat" in name:
            return f"{self._rng.gauss(37.5, 3.0):.4f}"
        if "longitude" in name or "lon" in name or "lng" in name:
            return f"{self._rng.gauss(-95.0, 10.0):.4f}"

        # Cost / price / amount -- log-normal distribution (skewed toward smaller)
        if any(k in name for k in ("cost", "price", "amount", "budget", "damage", "revenue")):
            val = abs(self._rng.gauss(5000, 8000))
            return f"{max(10.0, val):.2f}"

        # Duration / time
        if any(k in name for k in ("time", "minutes", "duration", "hours")):
            val = abs(self._rng.gauss(30, 25))
            return f"{max(0.5, val):.1f}"

        # Percentage / rate -- normal around 60
        if any(k in name for k in ("pct", "percent", "rate", "ratio", "progress",
                                    "completion", "utilization", "efficiency", "coverage")):
            val = self._rng.gauss(62, 20)
            return f"{max(0.0, min(100.0, val)):.1f}"

        # Temperature (IoT)
        if "temperature" in name or "temp" in name:
            return f"{self._rng.gauss(22.0, 8.0):.1f}"

        # Battery level (0-100%)
        if "battery" in name:
            val = self._rng.gauss(72.0, 18.0)
            return f"{max(5.0, min(100.0, val)):.1f}"

        # Speed (mph/kph)
        if "speed" in name:
            val = abs(self._rng.gauss(35.0, 20.0))
            return f"{min(120.0, val):.1f}"

        # Noise level (dB)
        if "noise" in name or name == "decibel" or "_db" in name:
            val = self._rng.gauss(55.0, 18.0)
            return f"{max(20.0, min(130.0, val)):.1f}"

        # Air quality index (0-500 EPA scale)
        if "air_quality" in name or "aqi" in name:
            val = abs(self._rng.gauss(65.0, 40.0))
            return f"{min(500.0, val):.0f}"

        # Signal strength (dBm, typically -30 to -90)
        if "signal" in name or "rssi" in name:
            val = self._rng.gauss(-60.0, 15.0)
            return f"{max(-95.0, min(-20.0, val)):.0f}"

        # Humidity (0-100%)
        if "humidity" in name:
            val = self._rng.gauss(55.0, 15.0)
            return f"{max(10.0, min(100.0, val)):.1f}"

        # Pressure (hPa, atmospheric)
        if "pressure" in name:
            val = self._rng.gauss(1013.0, 10.0)
            return f"{val:.1f}"

        # Power consumption (watts/kW)
        if "power" in name or "watt" in name or "energy" in name:
            val = abs(self._rng.gauss(150.0, 80.0))
            return f"{val:.1f}"

        # Flow rate
        if "flow" in name:
            val = abs(self._rng.gauss(25.0, 12.0))
            return f"{val:.2f}"

        # Weight / mass
        if "weight" in name or "mass" in name:
            return f"{abs(self._rng.gauss(50.0, 30.0)):.2f}"

        # Generic float
        val = abs(self._rng.gauss(100, 80))
        return f"{val:.2f}"

    def _gen_int(self, name: str, entity_name: str, row: int, total_rows: int) -> str:
        # Population / affected
        if "population" in name or "affected" in name or "users" in name:
            val = abs(int(self._rng.gauss(2000, 3000)))
            return str(max(1, val))

        # Count / capacity / quantity
        if any(k in name for k in ("count", "capacity", "quantity", "size", "length")):
            return str(abs(int(self._rng.gauss(50, 40))) + 1)

        # Year / lifespan / age
        if name in ("year", "lifespan", "age") or name.endswith("_year") or name.endswith("_years"):
            return str(self._rng.randint(1, 30))

        # Port numbers
        if name in ("port", "port_number"):
            ports = [80, 443, 3000, 5432, 6379, 8000, 8080, 8443, 9090, 27017]
            return str(self._rng.choice(ports))

        # Floor / story
        if "floor" in name or "story" in name or "level" in name:
            return str(self._rng.randint(1, 15))

        # Occupancy / passenger count
        if "occupancy" in name or "passenger" in name or "riders" in name:
            return str(abs(int(self._rng.gauss(25, 15))) + 1)

        # Stops / stations
        if "stop" in name or "station" in name:
            return str(self._rng.randint(3, 30))

        # Retry count
        if "retry" in name or "attempt" in name:
            # Zipf: most have 0-1 retries
            return str(max(0, self._rng.zipf_rank(5) - 1))

        # Page count
        if "page" in name:
            return str(self._rng.randint(1, 200))

        # Rating / score (1-5 or 1-10)
        if "rating" in name or "score" in name or "stars" in name:
            return str(self._rng.randint(1, 5))

        # Generic int -- uniform
        return str(self._rng.randint(1, 500))

    def _gen_bool(self, name: str, row: int, total_rows: int) -> str:
        # Active / enabled -- mostly true
        if name.startswith("is_active") or name.startswith("is_enabled") or name == "active":
            return "True" if self._rng.random() > 0.15 else "False"
        # Error / flagged -- mostly false
        if "error" in name or "flagged" in name or "blocked" in name:
            return "True" if self._rng.random() > 0.85 else "False"
        # Generic bool
        return "True" if self._rng.random() > 0.4 else "False"

    def _gen_list_str(self, name: str, entity_name: str, row: int) -> str:
        count = self._rng.randint(1, 4)
        # Tag lists
        if "tag" in name or "label" in name:
            pool = ["urgent", "follow-up", "reviewed", "automated", "flagged", "escalated", "archived"]
            items = self._rng.sample(pool, min(count, len(pool)))
            return f'[{", ".join(f"{chr(34)}{t}{chr(34)}" for t in items)}]'
        # Reference lists
        refs = [f'"{entity_name.lower()}-ref-{self._rng.randint(1, 100):03d}"' for _ in range(count)]
        return f'[{", ".join(refs)}]'

    def _gen_dict(self, name: str, entity_name: str, row: int) -> str:
        # Metadata / config fields get sample content
        if "metadata" in name or "config" in name or "properties" in name or "attributes" in name:
            return f'{{"source": "auto-generated", "version": "{self._rng.randint(1, 5)}"}}'
        return "{}"


# ────────────────────────────────────────────────────────────────────
# Main engine: orchestrates multi-entity generation
# ────────────────────────────────────────────────────────────────────

class MockDataEngine:
    """High-level engine that generates complete seed datasets.

    Replaces _dynamic_seed_data() in app_generator.py with a richer,
    statistically aware, referentially-intact data generation pipeline.
    """

    def __init__(
        self,
        config: MockDataConfig | None = None,
        domain_ctx: DomainContext | None = None,
    ):
        self.config = config or MockDataConfig()
        self.domain_ctx = domain_ctx
        self._rng = _PRNG(self.config.deterministic_seed)
        self._gen = MockValueGenerator(self._rng, domain_ctx, self.config)

    def generate_dataset(self, spec: IntentSpec) -> dict[str, list[dict[str, Any]]]:
        """Generate complete dataset for all entities in the spec.

        Returns entity_name -> list of record dicts.
        Processes entities in order so foreign keys can reference earlier entities.
        """
        dataset: dict[str, list[dict[str, Any]]] = {}
        count = self.config.record_count

        # Generate timestamps for this dataset
        ts_gen = _TIMESTAMP_GENERATORS.get(
            self.config.temporal_pattern,
            _timestamps_clustered,
        )
        timestamps = ts_gen(count, self.config.spread_days, self._rng)

        for entity in spec.entities:
            sn = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', entity.name).lower().replace(" ", "_")

            # Generate IDs first for referential integrity
            ids = [self._gen.generate_id(entity.name, r + 1) for r in range(count)]
            self._gen.register_entity_ids(sn, ids)

            records: list[dict[str, Any]] = []
            for row in range(1, count + 1):
                record: dict[str, Any] = {"id": ids[row - 1]}
                for f in entity.fields:
                    if f.name == "id":
                        continue
                    if f.name == "created_at":
                        continue
                    val_str = self._gen.generate(f, entity.name, row, count, timestamps)
                    record[f.name] = val_str
                record["created_at"] = timestamps[row - 1] if row - 1 < len(timestamps) else timestamps[-1]
                records.append(record)

            dataset[sn] = records

        return dataset

    def generate_seed_python(self, spec: IntentSpec) -> str:
        """Generate Python seed_data.py file content with advanced mock data."""
        dataset = self.generate_dataset(spec)

        # Collect all timestamp strings produced during generation so we can
        # store them as day-offsets.  At import time the generated module will
        # recompute fresh ISO strings relative to datetime.now().
        _gen_now = datetime.now(timezone.utc)

        def _iso_to_offset(iso_str: str) -> int | None:
            """Convert an ISO timestamp to a day-offset from generation time."""
            try:
                dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
                return int((_gen_now - dt).total_seconds())
            except (ValueError, TypeError):
                return None

        def _is_date_key(key: str) -> bool:
            return (
                key == "created_at"
                or key.endswith("_at")
                or key.endswith("_date")
                or "date" in key
                or "timestamp" in key
            )

        lines = [
            '"""Seed data — auto-generated with advanced mock data engine.',
            '',
            'Features: statistical distributions, referential integrity,',
            f'temporal clustering ({self.config.temporal_pattern}), uniqueness enforcement.',
            f'Records per entity: {self.config.record_count}',
            '',
            'Dates are computed dynamically at import time so the dashboard',
            'always shows recent, realistic timestamps for demo purposes.',
            '"""',
            '',
            'from __future__ import annotations',
            '',
            'from datetime import datetime, timedelta, timezone',
            '',
            '',
            '# ── Dynamic timestamp computation ─────────────────────────────',
            '# Each date field stores a seconds-offset from "now".  At import',
            '# time we resolve offsets into fresh ISO-8601 strings.',
            '',
            '_NOW = datetime.now(timezone.utc)',
            '',
            '',
            'def _ts(seconds_ago: int) -> str:',
            '    """Return an ISO-8601 timestamp *seconds_ago* before module load."""',
            '    return (_NOW - timedelta(seconds=seconds_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")',
            '',
            '',
        ]

        lines.append('_SEED: dict[str, list[dict]] = {')

        for entity_name, records in dataset.items():
            lines.append(f'    "{entity_name}": [')
            for rec in records:
                parts = []
                for key, val in rec.items():
                    if isinstance(val, str) and not val.startswith('"') and not val.startswith("'"):
                        # Check if this is a date field with an ISO timestamp value
                        if _is_date_key(key):
                            offset = _iso_to_offset(val)
                            if offset is not None:
                                parts.append(f'"{key}": _ts({offset})')
                                continue
                        if key == "created_at" or key == "id":
                            parts.append(f'"{key}": "{val}"')
                        else:
                            parts.append(f'"{key}": {val}')
                    else:
                        # Check quoted string date fields too
                        raw = val
                        if isinstance(raw, str) and raw.startswith('"') and raw.endswith('"'):
                            raw = raw[1:-1]
                        if _is_date_key(key) and isinstance(raw, str):
                            offset = _iso_to_offset(raw)
                            if offset is not None:
                                parts.append(f'"{key}": _ts({offset})')
                                continue
                        parts.append(f'"{key}": {val}')
                lines.append(f'        {{{", ".join(parts)}}},')
            lines.append('    ],')

        lines.append('}')
        lines.append('')
        lines.append('')
        lines.append('def get_seed_data(entity_name: str) -> list[dict]:')
        lines.append('    """Return seed records for the given entity type."""')
        lines.append('    return _SEED.get(entity_name, [])')
        lines.append('')

        return "\n".join(lines)

    def generate_seed_typescript(self, spec: IntentSpec) -> str:
        """Generate TypeScript seed data for frontend mock/demo data."""
        dataset = self.generate_dataset(spec)

        lines = [
            '// Seed data — auto-generated with advanced mock data engine',
            f'// Temporal pattern: {self.config.temporal_pattern} | Records: {self.config.record_count}',
            '',
        ]

        for entity_name, records in dataset.items():
            type_name = "".join(w.capitalize() for w in entity_name.split("_"))
            lines.append(f'export const {entity_name}Data: {type_name}[] = [')
            for rec in records:
                parts = []
                for key, val in rec.items():
                    if isinstance(val, str) and not val.startswith('"'):
                        parts.append(f'  {key}: "{val}"')
                    else:
                        parts.append(f'  {key}: {val}')
                lines.append('  {')
                for p in parts:
                    lines.append(f'  {p},')
                lines.append('  },')
            lines.append('];')
            lines.append('')

        return "\n".join(lines)

    def get_statistics(self, spec: IntentSpec) -> dict[str, Any]:
        """Generate statistics about the mock dataset for documentation."""
        dataset = self.generate_dataset(spec)
        stats: dict[str, Any] = {
            "total_records": sum(len(recs) for recs in dataset.values()),
            "entities": len(dataset),
            "records_per_entity": self.config.record_count,
            "temporal_pattern": self.config.temporal_pattern,
            "referential_integrity": bool(self._gen._entity_ids),
            "unique_emails": len(self._gen._used_emails),
            "unique_phones": len(self._gen._used_phones),
        }
        return stats

    # ────────────────────────────────────────────────────────────────────
    # PySpark / Microsoft Fabric integration
    # ────────────────────────────────────────────────────────────────────

    _TYPE_TO_SPARK = {
        "str": "StringType()",
        "int": "IntegerType()",
        "float": "DoubleType()",
        "bool": "BooleanType()",
        "datetime": "TimestampType()",
        "list[str]": "ArrayType(StringType())",
        "dict": "MapType(StringType(), StringType())",
    }

    def generate_pyspark_schema(self, spec: IntentSpec) -> str:
        """Generate PySpark StructType schema definitions for all entities."""
        lines = [
            "from pyspark.sql.types import (",
            "    StructType, StructField, StringType, IntegerType,",
            "    DoubleType, BooleanType, TimestampType, ArrayType, MapType,",
            ")",
            "",
        ]
        for entity in spec.entities:
            var = entity.name.lower().replace(" ", "_")
            lines.append(f"{var}_schema = StructType([")
            lines.append('    StructField("id", StringType(), False),')
            for f in entity.fields:
                if f.name == "id":
                    continue
                spark_type = self._TYPE_TO_SPARK.get(f.type, "StringType()")
                nullable = "True" if not f.required else "False"
                lines.append(f'    StructField("{f.name}", {spark_type}, {nullable}),')
            lines.append('    StructField("created_at", TimestampType(), False),')
            lines.append("])")
            lines.append("")
        return "\n".join(lines)

    def generate_spark_udfs(self, spec: IntentSpec) -> str:
        """Generate PySpark UDF library preserving statistical distributions at Spark scale."""
        lines = [
            "\"\"\"PySpark UDFs for synthetic data generation at scale.",
            "",
            "Preserves the same statistical distributions (Zipf, normal, clustered",
            "timestamps) used in seed data, but implemented as Spark UDFs for",
            "parallel execution across executors.",
            "\"\"\"",
            "",
            "import math",
            "import hashlib",
            "import random",
            "from datetime import datetime, timedelta",
            "from pyspark.sql import functions as F",
            "from pyspark.sql.types import StringType, IntegerType, DoubleType, TimestampType",
            "",
            "",
            "# Deterministic hash-based value generation",
            "def _hash_seed(entity: str, field: str, row_id: int) -> int:",
            '    h = hashlib.md5(f"{entity}:{field}:{row_id}".encode()).hexdigest()',
            "    return int(h[:8], 16)",
            "",
            "",
            "# --- Name generators ---",
            "",
            "_FIRST_NAMES = " + repr(_FIRST_NAMES[:30]) + "",
            "_LAST_NAMES = " + repr(_LAST_NAMES[:30]) + "",
            "_COMPANIES = " + repr(_COMPANY_NAMES[:15]) + "",
            "",
            "",
            "@F.udf(StringType())",
            "def gen_full_name(row_id):",
            '    h = _hash_seed("name", "full", row_id)',
            "    first = _FIRST_NAMES[h % len(_FIRST_NAMES)]",
            "    last = _LAST_NAMES[(h >> 8) % len(_LAST_NAMES)]",
            '    return f"{first} {last}"',
            "",
            "",
            "@F.udf(StringType())",
            "def gen_email(row_id):",
            '    h = _hash_seed("email", "addr", row_id)',
            "    first = _FIRST_NAMES[h % len(_FIRST_NAMES)].lower()",
            "    last = _LAST_NAMES[(h >> 8) % len(_LAST_NAMES)].lower()",
            '    domains = ["company.com", "enterprise.io", "corp.net", "org.co"]',
            "    domain = domains[(h >> 16) % len(domains)]",
            '    return f"{first}.{last}{row_id}@{domain}"',
            "",
            "",
            "@F.udf(StringType())",
            "def gen_uuid(row_id):",
            '    h = _hash_seed("uuid", "id", row_id)',
            '    return f"{h:08x}-{(h>>4)&0xFFFF:04x}-4{(h>>8)&0xFFF:03x}-{0x8000|((h>>12)&0x3FFF):04x}-{h&0xFFFFFFFFFFFF:012x}"',
            "",
            "",
            "# --- Numeric generators with distributions ---",
            "",
            "@F.udf(DoubleType())",
            "def gen_normal(row_id, mean, stddev):",
            '    h = _hash_seed("normal", "val", row_id)',
            "    # Box-Muller approximation from hash",
            "    u1 = max(1e-10, (h & 0xFFFF) / 0xFFFF)",
            "    u2 = ((h >> 16) & 0xFFFF) / 0xFFFF",
            "    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)",
            "    return float(mean + stddev * z)",
            "",
            "",
            "@F.udf(IntegerType())",
            "def gen_zipf_rank(row_id, n):",
            '    h = _hash_seed("zipf", "rank", row_id)',
            "    u = max(1e-10, (h & 0xFFFF) / 0xFFFF)",
            "    return min(n, max(1, int(1.0 / (u ** (1.0 / 1.1)))))",
            "",
            "",
            "# --- Timestamp generator with clustering ---",
            "",
            "@F.udf(TimestampType())",
            "def gen_clustered_timestamp(row_id, total_rows):",
            "    base = datetime(2025, 1, 1)",
            "    spread_days = 90",
            '    h = _hash_seed("ts", "cluster", row_id)',
            "    # Create 3-4 clusters",
            "    n_clusters = 3",
            "    cluster_idx = h % n_clusters",
            "    center_day = (cluster_idx + 1) * spread_days // (n_clusters + 1)",
            "    offset = int(((h >> 8) & 0xFF) / 255.0 * 10) - 5",
            "    day = max(0, min(spread_days, center_day + offset))",
            "    hour = (h >> 16) % 24",
            "    minute = (h >> 20) % 60",
            "    return base + timedelta(days=day, hours=hour, minutes=minute)",
            "",
            "",
            "# --- Status generators ---",
            "",
            "_STATUS_POOLS = {",
            '    "default": ["active", "inactive", "pending", "completed", "archived"],',
            '    "ticket": ["open", "in_progress", "resolved", "closed"],',
            '    "order": ["placed", "processing", "shipped", "delivered", "cancelled"],',
            "}",
            "",
            "",
            "@F.udf(StringType())",
            'def gen_status(row_id, pool_name="default"):',
            "    pool = _STATUS_POOLS.get(pool_name, _STATUS_POOLS['default'])",
            "    # Zipf-like: first statuses are more common",
            '    h = _hash_seed("status", pool_name, row_id)',
            "    u = max(1e-10, (h & 0xFFFF) / 0xFFFF)",
            "    idx = min(len(pool) - 1, int(1.0 / (u ** 0.7)) - 1)",
            "    return pool[max(0, idx)]",
            "",
        ]
        return "\n".join(lines)

    def generate_delta_table_ddl(self, spec: IntentSpec) -> str:
        """Generate Delta Lake CREATE TABLE statements for all entities."""
        _type_map = {
            "str": "STRING",
            "int": "INT",
            "float": "DOUBLE",
            "bool": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "list[str]": "ARRAY<STRING>",
            "dict": "MAP<STRING, STRING>",
        }
        lines = ["-- Delta Lake DDL -- auto-generated for Microsoft Fabric Lakehouse", ""]
        for entity in spec.entities:
            table = entity.name.lower().replace(" ", "_")
            lines.append(f"CREATE TABLE IF NOT EXISTS bronze_{table} (")
            lines.append("    id STRING NOT NULL,")
            for f in entity.fields:
                if f.name == "id":
                    continue
                dt = _type_map.get(f.type, "STRING")
                null = "" if f.required else ""
                lines.append(f"    {f.name} {dt}{null},")
            lines.append("    created_at TIMESTAMP NOT NULL,")
            lines.append("    _ingested_at TIMESTAMP DEFAULT current_timestamp(),")
            lines.append("    _source STRING DEFAULT 'synthetic'")
            lines.append(") USING DELTA")
            lines.append(f"COMMENT 'Bronze layer: raw {entity.name} data'")
            lines.append(f"TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true');")
            lines.append("")
            # Silver table
            lines.append(f"CREATE TABLE IF NOT EXISTS silver_{table} (")
            lines.append("    id STRING NOT NULL,")
            for f in entity.fields:
                if f.name == "id":
                    continue
                dt = _type_map.get(f.type, "STRING")
                lines.append(f"    {f.name} {dt},")
            lines.append("    created_at TIMESTAMP NOT NULL,")
            lines.append("    _is_valid BOOLEAN DEFAULT true,")
            lines.append("    _processed_at TIMESTAMP DEFAULT current_timestamp()")
            lines.append(") USING DELTA")
            lines.append(f"COMMENT 'Silver layer: cleansed {entity.name} data'")
            lines.append(f"TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true');")
            lines.append("")
            # Gold aggregate table
            lines.append(f"CREATE TABLE IF NOT EXISTS gold_{table}_summary (")
            lines.append("    period STRING NOT NULL,")
            lines.append(f"    total_{table}s INT,")
            # Add domain-relevant summary columns
            for f in entity.fields:
                if f.type in ("int", "float"):
                    lines.append(f"    avg_{f.name} DOUBLE,")
                    lines.append(f"    max_{f.name} DOUBLE,")
            lines.append("    _aggregated_at TIMESTAMP DEFAULT current_timestamp()")
            lines.append(") USING DELTA")
            lines.append(f"COMMENT 'Gold layer: {entity.name} aggregations';")
            lines.append("")
        return "\n".join(lines)
