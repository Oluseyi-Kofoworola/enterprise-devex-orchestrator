"""Domain Context -- semantic domain model shared across generators.

Provides domain-specific terminology, realistic seed data pools,
UI copy, compliance notes, and organizational identity for each
detected DomainType. This is the single source of truth for all
domain-aware generation — no generator should hardcode domain
values directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.orchestrator.intent_schema import DomainType, IntentSpec


@dataclass(frozen=True)
class DomainContext:
    """Semantic domain model consumed by all generators."""

    domain_type: DomainType
    org_name: str
    email_domains: list[str]
    portal_urls: list[str]
    terminology: dict[str, list[str]]
    description_templates: list[str]
    vendors: list[str]
    source_systems: list[str]
    compliance_frameworks: list[str]
    # Seed data pools
    first_names: list[str] = field(default_factory=list)
    last_names: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    streets: list[str] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    priorities: list[str] = field(default_factory=list)
    # UI / docs copy
    ui_brand_label: str = "Enterprise Platform"
    docs_org_label: str = "the organization"
    support_email: str = "support@enterprise.com"


# -- Default pools shared across all domains --------------------------

_DEFAULT_FIRST_NAMES = [
    "Alice", "Bob", "Carlos", "Diana", "Erik", "Fatima",
    "Grace", "Hassan", "Irene", "James", "Kira", "Liam",
    "Maya", "Noah", "Olivia",
]
_DEFAULT_LAST_NAMES = [
    "Chen", "Smith", "Garcia", "Patel", "Kim", "Johnson",
    "Williams", "Brown", "Jones", "Davis",
]
_DEFAULT_STREETS = [
    "Main St", "Oak Ave", "Elm Blvd", "Park Dr", "River Rd",
    "Industrial Pkwy", "Harbor View", "Tech Campus", "Central Plaza",
    "Lakeside Way", "Market St", "5th Avenue", "Broadway",
    "Commercial Blvd", "University Dr",
]
_DEFAULT_CITIES = [
    "Downtown", "Midtown", "Uptown", "Eastside", "Westside",
    "Northgate", "Southpoint", "Harbor District", "Tech Quarter",
    "Old Town", "Financial District", "Arts District", "Riverside",
    "Airport Zone", "Civic Center",
]
_DEFAULT_STATUSES = [
    "pending", "in_progress", "completed", "active",
    "critical", "resolved",
]
_DEFAULT_PRIORITIES = [
    "critical", "high", "medium", "low",
]

# -- Domain-specific context builders --------------------------------

_DOMAIN_CONTEXTS: dict[DomainType, dict] = {
    DomainType.HEALTHCARE: {
        "org_name": "Regional Medical Center",
        "email_domains": ["hospital.org", "healthnet.org"],
        "portal_urls": ["https://portal.healthnet.org", "https://ehr.hospital.org"],
        "terminology": {
            "category": ["cardiology", "orthopedics", "neurology", "oncology",
                          "pediatrics", "emergency", "radiology", "pathology",
                          "dermatology", "psychiatry", "internal-medicine", "surgery"],
            "type": ["outpatient", "inpatient", "emergency", "telehealth",
                      "lab-test", "imaging", "procedure", "consultation",
                      "follow-up", "screening"],
            "gender": ["male", "female", "non-binary", "prefer-not-to-say"],
            "preferred_language": ["English", "Spanish", "Mandarin", "Arabic",
                                    "French", "Korean", "Vietnamese", "Portuguese"],
        },
        "description_templates": [
            "Patient presented with {} symptoms. Vitals recorded and assessment completed.",
            "Scheduled {} procedure for department review. Pre-op checklist in progress.",
            "Follow-up visit for {} treatment plan. Patient reports improvement.",
            "Emergency admission for {}. Triage assessment completed, priority assigned.",
            "Lab results for {} panel received. Physician review pending.",
        ],
        "vendors": ["Epic Systems", "Cerner", "Meditech", "Allscripts",
                     "GE Healthcare", "Philips Health", "Siemens Healthineers",
                     "McKesson", "Cardinal Health", "Stryker"],
        "source_systems": ["EHR", "PACS", "LIS", "RIS", "pharmacy-system",
                            "nurse-call", "patient-portal", "scheduling-system"],
        "compliance_frameworks": ["HIPAA", "HITECH", "SOC 2", "Joint Commission"],
        "cities": ["Mercy Campus", "St. Joseph Wing", "West Medical Tower",
                   "Ambulatory Center", "Rehabilitation Unit", "Trauma Center",
                   "Women's Health Pavilion", "Children's Hospital", "Cancer Center",
                   "Heart Institute", "Emergency Department", "Behavioral Health"],
        "statuses": ["pending", "in_progress", "completed", "scheduled",
                     "cancelled", "no_show"],
        "categories": ["cardiology", "orthopedics", "neurology", "oncology",
                        "pediatrics", "emergency", "radiology", "internal-medicine"],
        "ui_brand_label": "HealthNet Clinical Platform",
        "docs_org_label": "the medical center",
        "support_email": "support@healthnet.org",
    },
    DomainType.LEGAL: {
        "org_name": "Enterprise Legal Services",
        "email_domains": ["legalops.com", "counsel.enterprise.com"],
        "portal_urls": ["https://contracts.legalops.com", "https://review.counsel.enterprise.com"],
        "terminology": {
            "category": ["employment", "NDA", "vendor-agreement", "lease",
                          "licensing", "partnership", "services-agreement",
                          "master-services", "amendment", "addendum",
                          "settlement", "acquisition"],
            "type": ["new-contract", "renewal", "amendment", "termination",
                      "review", "redline", "negotiation", "execution"],
            "risk_level": ["low", "moderate", "high", "critical"],
        },
        "description_templates": [
            "Contract submitted for {} review. Clause analysis in progress.",
            "Redline comparison completed for {} agreement. Changes flagged for counsel.",
            "Legal hold placed on {} documentation. Retention policy applied.",
            "Amendment drafted for {} terms. Awaiting counterparty review.",
            "Compliance review for {} regulatory requirements completed.",
        ],
        "vendors": ["DocuSign", "Ironclad", "ContractPodAi", "Icertis",
                     "Agiloft", "Juro", "LinkSquares", "LawGeex"],
        "source_systems": ["CLM", "e-signature", "document-management",
                            "matter-management", "billing-system", "docket"],
        "compliance_frameworks": ["SOC 2", "GDPR", "CCPA", "SEC regulations"],
        "statuses": ["draft", "under_review", "approved", "executed",
                     "expired", "terminated"],
        "categories": ["employment", "NDA", "vendor-agreement", "lease",
                        "licensing", "partnership", "services-agreement", "amendment"],
        "ui_brand_label": "Legal Contract Platform",
        "docs_org_label": "the legal department",
        "support_email": "legal-support@enterprise.com",
    },
    DomainType.DOCUMENT_PROCESSING: {
        "org_name": "Document Intelligence Hub",
        "email_domains": ["docops.enterprise.com"],
        "portal_urls": ["https://docs.enterprise.com", "https://intake.docops.enterprise.com"],
        "terminology": {
            "category": ["invoice", "receipt", "tax-form", "id-document",
                          "contract", "purchase-order", "insurance-claim",
                          "medical-record", "shipping-label", "bank-statement",
                          "utility-bill", "passport"],
            "type": ["scan", "upload", "fax", "email-attachment",
                      "api-ingest", "batch-import"],
        },
        "description_templates": [
            "Document received via {} channel. OCR processing initiated.",
            "Extraction complete for {} document type. Confidence score above threshold.",
            "Validation failed for {} — manual review queued.",
            "Batch of {} documents processed. Summary report generated.",
            "Classification model assigned {} category. Ready for downstream routing.",
        ],
        "vendors": ["ABBYY", "Kofax", "UiPath", "Hyperscience",
                     "Rossum", "Instabase", "Eigen Technologies"],
        "source_systems": ["scanner", "email-inbox", "fax-gateway",
                            "API-endpoint", "file-share", "mobile-capture"],
        "compliance_frameworks": ["SOC 2", "GDPR", "CCPA", "PCI DSS"],
        "statuses": ["received", "processing", "extracted", "validated",
                     "failed", "archived"],
        "categories": ["invoice", "receipt", "tax-form", "id-document",
                        "contract", "purchase-order", "insurance-claim", "bank-statement"],
        "ui_brand_label": "Document Intelligence Hub",
        "docs_org_label": "the document processing team",
        "support_email": "doc-support@enterprise.com",
    },
    DomainType.CYBERSECURITY: {
        "org_name": "Security Operations Center",
        "email_domains": ["soc.enterprise.com", "security.enterprise.com"],
        "portal_urls": ["https://soc.enterprise.com", "https://siem.enterprise.com"],
        "terminology": {
            "category": ["malware", "phishing", "ransomware", "data-exfiltration",
                          "unauthorized-access", "DDoS", "insider-threat",
                          "supply-chain", "zero-day", "credential-theft",
                          "lateral-movement", "privilege-escalation"],
            "type": ["alert", "incident", "investigation", "hunt",
                      "vulnerability-scan", "penetration-test", "audit"],
            "severity": ["critical", "high", "medium", "low", "informational"],
        },
        "description_templates": [
            "SIEM alert triggered for {} activity. Analyst investigation initiated.",
            "Threat intelligence feed flagged {} indicators. IOC enrichment in progress.",
            "Incident response playbook activated for {}. Containment measures applied.",
            "Vulnerability scan detected {} findings across production assets.",
            "Forensic analysis of {} event completed. Evidence preserved.",
        ],
        "vendors": ["CrowdStrike", "Palo Alto Networks", "Splunk",
                     "SentinelOne", "Fortinet", "Rapid7", "Tenable",
                     "Qualys", "Carbon Black", "Darktrace"],
        "source_systems": ["SIEM", "EDR", "firewall", "IDS/IPS",
                            "vulnerability-scanner", "threat-intel-feed",
                            "email-gateway", "WAF", "CASB"],
        "compliance_frameworks": ["NIST CSF", "ISO 27001", "SOC 2",
                                   "CIS Controls", "PCI DSS", "MITRE ATT&CK"],
        "statuses": ["new", "triaging", "investigating", "contained",
                     "remediated", "closed", "false_positive"],
        "categories": ["malware", "phishing", "ransomware", "data-exfiltration",
                        "unauthorized-access", "DDoS", "insider-threat", "zero-day"],
        "priorities": ["P1-critical", "P2-high", "P3-medium", "P4-low"],
        "ui_brand_label": "Security Operations Platform",
        "docs_org_label": "the security operations center",
        "support_email": "soc@enterprise.com",
    },
    DomainType.IOT_SMART_CITY: {
        "org_name": "Smart City Operations",
        "email_domains": ["smartcity.gov", "iot.cityops.gov"],
        "portal_urls": ["https://portal.smartcity.gov", "https://dashboard.cityops.gov"],
        "terminology": {
            "category": ["traffic", "energy", "water", "waste",
                          "air-quality", "noise", "lighting", "parking",
                          "public-safety", "transportation", "infrastructure", "environment"],
            "type": ["sensor-reading", "alert", "maintenance", "inspection",
                      "calibration", "firmware-update", "provisioning"],
        },
        "description_templates": [
            "Sensor cluster in {} sector reporting anomalous readings. Threshold exceeded.",
            "Scheduled maintenance for {} infrastructure. Field crew dispatched.",
            "Environmental monitoring in {} zone shows improvement. Alert cleared.",
            "Traffic flow optimization for {} corridor activated. Adaptive signals engaged.",
            "Asset health score for {} equipment degraded. Preventive action recommended.",
        ],
        "vendors": ["Siemens", "GE Digital", "Honeywell", "Schneider Electric",
                     "ABB", "Cisco Systems", "Itron", "Sensus", "Trimble",
                     "Telensa", "Silver Spring", "Eaton"],
        "source_systems": ["IoT-gateway", "SCADA", "GIS", "fleet-tracker",
                            "weather-station", "traffic-controller", "smart-meter"],
        "compliance_frameworks": ["NIST", "ISO 27001", "FedRAMP", "CJIS"],
        "cities": ["Downtown", "Midtown", "Uptown", "Eastside", "Westside",
                   "Northgate", "Southpoint", "Harbor District", "Tech Quarter",
                   "Old Town", "Financial District", "Arts District"],
        "categories": ["traffic", "energy", "water", "waste",
                        "air-quality", "noise", "lighting", "parking"],
        "ui_brand_label": "Smart City Operations Center",
        "docs_org_label": "the city operations department",
        "support_email": "support@smartcity.gov",
    },
    DomainType.LOGISTICS: {
        "org_name": "Global Logistics Network",
        "email_domains": ["logistics.enterprise.com", "ops.supplychain.com"],
        "portal_urls": ["https://track.logistics.enterprise.com", "https://ops.supplychain.com"],
        "terminology": {
            "category": ["ground-freight", "air-freight", "ocean-freight",
                          "last-mile", "cold-chain", "hazmat", "oversized",
                          "express", "economy", "intermodal", "drayage", "LTL"],
            "type": ["pickup", "in-transit", "customs-clearance", "delivery",
                      "return", "exception", "consolidation", "deconsolidation"],
        },
        "description_templates": [
            "Shipment {} cleared customs. Last-mile carrier assigned.",
            "Route optimization for {} corridor complete. ETA updated.",
            "Exception flagged on {} shipment — temperature deviation logged.",
            "Warehouse {} inventory reconciliation completed. Discrepancies resolved.",
            "Carrier performance report for {} lane generated. SLA compliance at 94%.",
        ],
        "vendors": ["FedEx", "UPS", "DHL", "Maersk", "XPO Logistics",
                     "C.H. Robinson", "Kuehne+Nagel", "DB Schenker",
                     "Flexport", "project44"],
        "source_systems": ["TMS", "WMS", "GPS-tracker", "EDI-gateway",
                            "carrier-API", "customs-portal", "IoT-sensor"],
        "compliance_frameworks": ["C-TPAT", "AEO", "IATA", "IMO", "FDA (food)"],
        "statuses": ["booked", "picked_up", "in_transit", "at_customs",
                     "out_for_delivery", "delivered", "exception"],
        "categories": ["ground-freight", "air-freight", "ocean-freight",
                        "last-mile", "cold-chain", "express", "economy", "intermodal"],
        "ui_brand_label": "Logistics Command Center",
        "docs_org_label": "the logistics operations team",
        "support_email": "ops@logistics.enterprise.com",
    },
    DomainType.RETAIL: {
        "org_name": "Retail Operations",
        "email_domains": ["retail.enterprise.com", "store.enterprise.com"],
        "portal_urls": ["https://admin.retail.enterprise.com", "https://pos.enterprise.com"],
        "terminology": {
            "category": ["electronics", "apparel", "grocery", "home-goods",
                          "beauty", "sporting-goods", "toys", "automotive",
                          "pharmacy", "garden", "seasonal", "clearance"],
            "type": ["in-store", "online", "curbside-pickup", "ship-to-store",
                      "same-day-delivery", "subscription", "pre-order", "return"],
        },
        "description_templates": [
            "Promotion '{}' activated across all channels. Inventory reserved.",
            "Order {} fulfilled from nearest distribution center. Shipping label generated.",
            "Customer segment '{}' campaign launched. A/B testing in progress.",
            "Inventory reorder triggered for {} SKUs. Purchase order created.",
            "Returns processing for {} batch completed. Restocking decisions applied.",
        ],
        "vendors": ["Shopify", "Salesforce Commerce", "SAP Commerce",
                     "Oracle Retail", "Manhattan Associates", "Blue Yonder",
                     "Adyen", "Stripe", "Square"],
        "source_systems": ["POS", "e-commerce-platform", "OMS", "WMS",
                            "CRM", "loyalty-system", "pricing-engine"],
        "compliance_frameworks": ["PCI DSS", "GDPR", "CCPA", "SOC 2"],
        "statuses": ["pending", "confirmed", "processing", "shipped",
                     "delivered", "returned", "cancelled"],
        "categories": ["electronics", "apparel", "grocery", "home-goods",
                        "beauty", "sporting-goods", "toys", "automotive"],
        "ui_brand_label": "Retail Operations Platform",
        "docs_org_label": "the retail operations team",
        "support_email": "ops@retail.enterprise.com",
    },
    DomainType.MANUFACTURING: {
        "org_name": "Manufacturing Operations",
        "email_domains": ["mfg.enterprise.com", "factory.enterprise.com"],
        "portal_urls": ["https://mes.mfg.enterprise.com", "https://ops.factory.enterprise.com"],
        "terminology": {
            "category": ["assembly", "machining", "welding", "painting",
                          "quality-inspection", "packaging", "testing",
                          "material-handling", "maintenance", "tooling",
                          "CNC", "injection-molding"],
            "type": ["production-run", "rework", "scrap", "maintenance",
                      "changeover", "quality-hold", "first-article-inspection"],
        },
        "description_templates": [
            "Production line {} — shift output at 94% of target. OEE stable.",
            "Quality hold on batch {} — dimensional inspection deviation detected.",
            "Preventive maintenance scheduled for {} equipment. Parts ordered.",
            "Work order {} completed ahead of schedule. Yield above target.",
            "Material shortage for {} BOM. Alternate supplier sourcing initiated.",
        ],
        "vendors": ["Siemens", "Rockwell Automation", "ABB", "Fanuc",
                     "KUKA", "Dassault Systèmes", "PTC", "Hexagon"],
        "source_systems": ["MES", "ERP", "PLC", "SCADA", "QMS",
                            "CMMS", "CAD/CAM", "SPC"],
        "compliance_frameworks": ["ISO 9001", "ISO 14001", "IATF 16949",
                                   "AS9100", "OSHA"],
        "statuses": ["scheduled", "in_progress", "completed", "on_hold",
                     "rework", "scrapped"],
        "categories": ["assembly", "machining", "welding", "painting",
                        "quality-inspection", "packaging", "testing", "maintenance"],
        "ui_brand_label": "Manufacturing Execution Platform",
        "docs_org_label": "the manufacturing operations team",
        "support_email": "ops@mfg.enterprise.com",
    },
    DomainType.AGRICULTURE: {
        "org_name": "AgriTech Operations",
        "email_domains": ["agritech.enterprise.com", "farm.enterprise.com"],
        "portal_urls": ["https://dashboard.agritech.enterprise.com"],
        "terminology": {
            "category": ["wheat", "corn", "soybean", "rice", "cotton",
                          "cattle", "poultry", "dairy", "vegetables",
                          "fruit", "organic", "greenhouse"],
            "type": ["planting", "irrigation", "fertilizing", "harvesting",
                      "pest-control", "soil-analysis", "weather-monitoring"],
        },
        "description_templates": [
            "Field {} — soil moisture at optimal level. Irrigation schedule updated.",
            "Crop health assessment for {} completed. NDVI analysis normal.",
            "Pest detection alert in {} zone. Treatment recommendation generated.",
            "Harvest forecast for {} updated. Yield estimate revised upward.",
            "Weather advisory for {} region. Frost protection measures activated.",
        ],
        "vendors": ["John Deere", "Climate Corp", "Trimble Ag",
                     "AGCO", "Bayer CropScience", "Syngenta",
                     "FarmLogs", "Granular"],
        "source_systems": ["precision-ag-platform", "weather-station",
                            "soil-sensor", "drone", "satellite-imagery",
                            "GPS-guidance", "irrigation-controller"],
        "compliance_frameworks": ["USDA GAP", "GlobalG.A.P.", "organic certification",
                                   "FDA FSMA"],
        "statuses": ["planned", "in_progress", "completed", "delayed",
                     "weather_hold", "harvested"],
        "categories": ["wheat", "corn", "soybean", "rice", "cotton",
                        "cattle", "poultry", "dairy"],
        "ui_brand_label": "AgriTech Intelligence Platform",
        "docs_org_label": "the agricultural operations team",
        "support_email": "support@agritech.enterprise.com",
    },
    DomainType.GOVERNMENT: {
        "org_name": "Municipal Government Services",
        "email_domains": ["city.gov", "municipal.gov"],
        "portal_urls": ["https://portal.city.gov", "https://services.municipal.gov"],
        "terminology": {
            "category": ["building-permit", "business-license", "zoning",
                          "code-enforcement", "public-works", "parks",
                          "utilities", "transportation", "public-safety",
                          "health-services", "planning", "finance"],
            "type": ["application", "inspection", "hearing", "approval",
                      "renewal", "complaint", "request", "appeal"],
        },
        "description_templates": [
            "Permit application for {} submitted. Initial review assigned.",
            "Code enforcement inspection at {} completed. Violations documented.",
            "Public works request for {} neighborhood scheduled. Crew assigned.",
            "Citizen complaint regarding {} logged. Response SLA: 48 hours.",
            "Budget allocation for {} department approved. Procurement authorized.",
        ],
        "vendors": ["Tyler Technologies", "Accela", "CityGov",
                     "OpenGov", "Granicus", "Socrata", "Esri"],
        "source_systems": ["311-system", "GIS", "permitting-portal",
                            "court-management", "fleet-system", "HRIS"],
        "compliance_frameworks": ["FedRAMP", "CJIS", "Section 508",
                                   "ADA", "FOIA"],
        "statuses": ["submitted", "under_review", "approved", "denied",
                     "pending_inspection", "completed"],
        "categories": ["building-permit", "business-license", "zoning",
                        "code-enforcement", "public-works", "parks",
                        "utilities", "transportation"],
        "ui_brand_label": "Municipal Services Portal",
        "docs_org_label": "the municipal government",
        "support_email": "help@city.gov",
    },
    DomainType.FINANCE: {
        "org_name": "Financial Services Platform",
        "email_domains": ["finserv.enterprise.com", "banking.enterprise.com"],
        "portal_urls": ["https://portal.finserv.enterprise.com", "https://trading.enterprise.com"],
        "terminology": {
            "category": ["equity", "fixed-income", "derivatives", "forex",
                          "commodities", "structured-products", "money-market",
                          "mutual-fund", "ETF", "insurance", "lending", "payments"],
            "type": ["trade", "settlement", "reconciliation", "audit",
                      "compliance-check", "risk-assessment", "valuation"],
        },
        "description_templates": [
            "Transaction {} processed. Settlement T+2 scheduled.",
            "Risk assessment for {} portfolio completed. VaR within limits.",
            "AML screening flagged {} transaction. Enhanced due diligence initiated.",
            "Reconciliation for {} account completed. No discrepancies found.",
            "Regulatory report for {} period generated. Submission deadline met.",
        ],
        "vendors": ["Bloomberg", "Refinitiv", "FIS", "Fiserv",
                     "SS&C Technologies", "Broadridge", "Temenos",
                     "Finastra", "Murex", "Moody's Analytics"],
        "source_systems": ["core-banking", "trading-platform", "risk-engine",
                            "payment-gateway", "AML-system", "KYC-platform",
                            "market-data-feed", "settlement-engine"],
        "compliance_frameworks": ["SOX", "Basel III", "MiFID II",
                                   "PCI DSS", "GDPR", "SOC 2"],
        "statuses": ["pending", "processing", "settled", "failed",
                     "reversed", "under_review"],
        "categories": ["equity", "fixed-income", "derivatives", "forex",
                        "commodities", "structured-products", "money-market", "payments"],
        "priorities": ["urgent", "high", "normal", "low"],
        "ui_brand_label": "Financial Services Platform",
        "docs_org_label": "the financial services division",
        "support_email": "support@finserv.enterprise.com",
    },
}

# Default / generic context
_GENERIC_CONTEXT: dict = {
    "org_name": "Enterprise Operations",
    "email_domains": ["enterprise.com", "ops.enterprise.com"],
    "portal_urls": ["https://portal.enterprise.com"],
    "terminology": {
        "category": ["infrastructure", "safety", "environmental", "maintenance",
                      "security", "utilities", "transportation", "administration",
                      "compliance", "operations"],
        "type": ["electrical", "mechanical", "structural", "software",
                  "network", "hydraulic", "thermal", "environmental"],
    },
    "description_templates": [
        "Operation {} initiated. Standard procedures apply.",
        "Scheduled maintenance for {} sector. Team assigned.",
        "Automated detection: {} anomaly identified. Investigation in progress.",
        "Follow-up inspection after {} activity completed. Status updated.",
        "Resource allocation for {} project finalized. Budget confirmed.",
    ],
    "vendors": ["Siemens", "GE Digital", "Honeywell", "Schneider Electric",
                "ABB", "Cisco Systems", "Itron", "Sensus", "Trimble",
                "Telensa", "Silver Spring", "Eaton", "Emerson",
                "Rockwell", "Yokogawa"],
    "source_systems": ["IoT-sensor", "citizen-report", "automated-scan",
                        "field-inspection", "dispatch-system", "API-integration",
                        "manual-entry", "SCADA", "mobile-app", "web-portal"],
    "compliance_frameworks": ["SOC 2", "ISO 27001"],
}


def build_domain_context(spec: IntentSpec) -> DomainContext:
    """Build a DomainContext from the IntentSpec's detected domain."""
    domain = spec.domain_type
    ctx = _DOMAIN_CONTEXTS.get(domain, _GENERIC_CONTEXT)

    return DomainContext(
        domain_type=domain,
        org_name=ctx.get("org_name", _GENERIC_CONTEXT["org_name"]),
        email_domains=ctx.get("email_domains", _GENERIC_CONTEXT["email_domains"]),
        portal_urls=ctx.get("portal_urls", _GENERIC_CONTEXT["portal_urls"]),
        terminology=ctx.get("terminology", _GENERIC_CONTEXT["terminology"]),
        description_templates=ctx.get("description_templates", _GENERIC_CONTEXT["description_templates"]),
        vendors=ctx.get("vendors", _GENERIC_CONTEXT["vendors"]),
        source_systems=ctx.get("source_systems", _GENERIC_CONTEXT["source_systems"]),
        compliance_frameworks=ctx.get("compliance_frameworks", _GENERIC_CONTEXT["compliance_frameworks"]),
        first_names=_DEFAULT_FIRST_NAMES,
        last_names=_DEFAULT_LAST_NAMES,
        cities=ctx.get("cities", _DEFAULT_CITIES),
        streets=_DEFAULT_STREETS,
        statuses=ctx.get("statuses", _DEFAULT_STATUSES),
        categories=ctx.get("categories", []),
        priorities=ctx.get("priorities", _DEFAULT_PRIORITIES),
        ui_brand_label=ctx.get("ui_brand_label", "Enterprise Platform"),
        docs_org_label=ctx.get("docs_org_label", "the organization"),
        support_email=ctx.get("support_email", "support@enterprise.com"),
    )
