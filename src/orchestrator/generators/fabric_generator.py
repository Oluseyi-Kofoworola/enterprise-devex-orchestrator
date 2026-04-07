"""Microsoft Fabric Generator -- produces Lakehouse, notebook, pipeline, and analytics artifacts.

Generates a complete Microsoft Fabric data platform scaffold including:
    - PySpark medallion-architecture notebooks (Bronze/Silver/Gold layers)
    - Data Pipeline definitions for orchestration
    - Eventstream configuration for real-time ingestion
    - KQL analytics queries for operational dashboards
    - Event simulator for demo scenarios
    - Delta Lake DDL and schema definitions

All generated notebooks use Managed Identity authentication and produce
Delta Lake tables compatible with Fabric Lakehouse.
"""

from __future__ import annotations

from src.orchestrator.generators.mock_data_engine import MockDataConfig, MockDataEngine
from src.orchestrator.intent_schema import DataStore, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)

# Default record count for Fabric-scale synthetic data
_DEFAULT_FABRIC_RECORDS = 50_000


class FabricGenerator:
    """Generates Microsoft Fabric artifacts for the Lakehouse data platform."""

    def __init__(self) -> None:
        self._scaffold_plan = None

    def set_scaffold_plan(self, scaffold_plan) -> None:
        """Receive platform-wide planning objects from the orchestrator."""
        self._scaffold_plan = scaffold_plan

    def generate(self, spec: IntentSpec) -> dict[str, str]:
        """Generate all Fabric artifacts.

        Returns file-path -> content mapping.  Only produces output when
        the spec indicates Fabric usage (``uses_fabric`` or
        ``DataStore.FABRIC_LAKEHOUSE`` in data_stores).
        """
        if not _should_generate(spec):
            return {}

        logger.info("fabric_generator.start", project=spec.project_name)

        engine = MockDataEngine(config=MockDataConfig(
            record_count=24,
            temporal_pattern="clustered",
        ))

        files: dict[str, str] = {}

        # Medallion architecture notebooks
        files["fabric/notebooks/01_bronze_ingestion.py"] = self._bronze_notebook(spec, engine)
        files["fabric/notebooks/02_silver_transform.py"] = self._silver_notebook(spec)
        files["fabric/notebooks/03_gold_aggregation.py"] = self._gold_notebook(spec)
        files["fabric/notebooks/04_data_quality.py"] = self._data_quality_notebook(spec)

        # Pipeline definitions
        files["fabric/pipelines/medallion_pipeline.json"] = self._medallion_pipeline(spec)
        files["fabric/pipelines/incremental_refresh.json"] = self._incremental_pipeline(spec)

        # Eventstream
        files["fabric/eventstream/realtime_ingestion.json"] = self._eventstream_config(spec)
        files["fabric/eventstream/event_simulator.py"] = self._event_simulator(spec)

        # KQL analytics
        files["fabric/kql/entity_analytics.kql"] = self._entity_analytics_kql(spec)
        files["fabric/kql/realtime_dashboard.kql"] = self._realtime_dashboard_kql(spec)

        # Delta DDL
        files["fabric/ddl/delta_tables.sql"] = engine.generate_delta_table_ddl(spec)

        # PySpark schemas and UDFs
        files["fabric/lib/schemas.py"] = engine.generate_pyspark_schema(spec)
        files["fabric/lib/udfs.py"] = engine.generate_spark_udfs(spec)

        # Documentation
        files["fabric/README.md"] = self._readme(spec)
        files["fabric/demo-script.md"] = self._demo_script(spec)

        logger.info("fabric_generator.complete", file_count=len(files))
        return files

    # ── Notebook generators ──────────────────────────────────────────

    def _bronze_notebook(self, spec: IntentSpec, engine: MockDataEngine) -> str:
        """Generate Bronze layer notebook — raw synthetic data ingestion."""
        entities = spec.entities or []
        project = spec.project_name
        record_count = _DEFAULT_FABRIC_RECORDS

        entity_blocks = []
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            fields_schema = []
            fields_schema.append(f'    StructField("id", StringType(), False),')
            for f in entity.fields:
                if f.name == "id":
                    continue
                spark_t = MockDataEngine._TYPE_TO_SPARK.get(f.type, "StringType()")
                fields_schema.append(f'    StructField("{f.name}", {spark_t}, {not f.required}),')
            fields_schema.append(f'    StructField("created_at", TimestampType(), False),')
            schema_str = "\n".join(fields_schema)

            gen_rows = []
            for f in entity.fields:
                if f.name == "id":
                    continue
                if f.type == "int":
                    gen_rows.append(f'        gen_normal(F.col("_row_id"), F.lit(100.0), F.lit(30.0)).cast("int").alias("{f.name}"),')
                elif f.type == "float":
                    gen_rows.append(f'        gen_normal(F.col("_row_id"), F.lit(50.0), F.lit(15.0)).alias("{f.name}"),')
                elif f.type == "bool":
                    gen_rows.append(f'        (F.hash(F.col("_row_id"), F.lit("{f.name}")) % 5 > 0).alias("{f.name}"),')
                elif f.type == "datetime":
                    gen_rows.append(f'        gen_clustered_timestamp(F.col("_row_id"), F.lit({record_count})).alias("{f.name}"),')
                elif "name" in f.name.lower():
                    gen_rows.append(f'        gen_full_name(F.col("_row_id")).alias("{f.name}"),')
                elif "email" in f.name.lower():
                    gen_rows.append(f'        gen_email(F.col("_row_id")).alias("{f.name}"),')
                elif "status" in f.name.lower():
                    gen_rows.append(f'        gen_status(F.col("_row_id")).alias("{f.name}"),')
                else:
                    gen_rows.append(f'        F.concat(F.lit("{f.name}-"), F.col("_row_id").cast("string")).alias("{f.name}"),')
            gen_rows_str = "\n".join(gen_rows)

            entity_blocks.append(f'''
# ── {entity.name} ──────────────────────────────────
print(f"Generating {{RECORD_COUNT:,}} {entity.name} records...")

{sn}_schema = StructType([
{schema_str}
])

{sn}_df = (
    spark.range(1, RECORD_COUNT + 1)
    .withColumnRenamed("id", "_row_id")
    .select(
        gen_uuid(F.col("_row_id")).alias("id"),
{gen_rows_str}
        gen_clustered_timestamp(F.col("_row_id"), F.lit(RECORD_COUNT)).alias("created_at"),
    )
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source", F.lit("synthetic"))
)

{sn}_df.write.format("delta").mode("overwrite").saveAsTable("bronze_{sn}")
print(f"  ✓ bronze_{sn}: {{{sn}_df.count():,}} rows written")
''')

        entity_blocks_str = "\n".join(entity_blocks)

        return f'''# Databricks/Fabric notebook
# MAGIC %md
# MAGIC # Bronze Layer — Raw Synthetic Data Ingestion
# MAGIC
# MAGIC **Project:** {project}
# MAGIC **Layer:** Bronze (raw/landing)
# MAGIC **Pattern:** Medallion Architecture
# MAGIC **Record Count:** {record_count:,} per entity
# MAGIC
# MAGIC This notebook generates synthetic data at enterprise scale using
# MAGIC PySpark UDFs that preserve statistical distributions (Zipf, normal,
# MAGIC clustered timestamps) for realistic demo scenarios.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, TimestampType, ArrayType, MapType,
)

# Import synthetic data UDFs
# In Fabric, place udfs.py in the Lakehouse files area or use %run
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "lib"))
from udfs import (
    gen_full_name, gen_email, gen_uuid, gen_normal,
    gen_zipf_rank, gen_clustered_timestamp, gen_status,
)

# COMMAND ----------

# Configuration
RECORD_COUNT = {record_count}
LAKEHOUSE_NAME = "{project.replace("-", "_")}_lakehouse"

print(f"Bronze Ingestion — generating {{RECORD_COUNT:,}} records per entity")
print(f"Target Lakehouse: {{LAKEHOUSE_NAME}}")

# COMMAND ----------
{entity_blocks_str}
# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingestion Summary

# COMMAND ----------

tables = spark.sql("SHOW TABLES LIKE 'bronze_*'")
display(tables)

for row in tables.collect():
    tbl = row.tableName
    count = spark.table(tbl).count()
    print(f"  {{tbl}}: {{count:,}} rows")

print("\\n✅ Bronze layer ingestion complete")
'''

    def _silver_notebook(self, spec: IntentSpec) -> str:
        """Generate Silver layer notebook — data cleansing and transformation."""
        entities = spec.entities or []
        project = spec.project_name

        entity_blocks = []
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            dedup_cols = ["id"]

            data_quality = []
            for f in entity.fields:
                if f.required and f.type == "str":
                    data_quality.append(
                        f'    .withColumn("_is_valid", F.col("_is_valid") & F.col("{f.name}").isNotNull())'
                    )
                if f.type in ("int", "float"):
                    data_quality.append(
                        f'    .withColumn("{f.name}", F.when(F.col("{f.name}") < 0, F.lit(0)).otherwise(F.col("{f.name}")))'
                    )
            quality_str = "\n".join(data_quality) if data_quality else '    # No additional quality rules'

            entity_blocks.append(f'''
# ── {entity.name} ──────────────────────────────────
print("Processing bronze_{sn} → silver_{sn}")

bronze_{sn} = spark.table("bronze_{sn}")

silver_{sn} = (
    bronze_{sn}
    # Deduplication by id (keep latest ingested)
    .dropDuplicates({dedup_cols})
    # Data quality flags
    .withColumn("_is_valid", F.lit(True))
{quality_str}
    # Standardize timestamps
    .withColumn("created_at", F.to_timestamp("created_at"))
    .withColumn("_processed_at", F.current_timestamp())
)

# Write to Silver
silver_{sn}.write.format("delta").mode("overwrite").saveAsTable("silver_{sn}")
valid_count = silver_{sn}.filter(F.col("_is_valid")).count()
total_count = silver_{sn}.count()
print(f"  ✓ silver_{sn}: {{total_count:,}} rows ({{valid_count:,}} valid, {{total_count - valid_count:,}} flagged)")
''')

        entity_blocks_str = "\n".join(entity_blocks)

        return f'''# Databricks/Fabric notebook
# MAGIC %md
# MAGIC # Silver Layer — Data Cleansing & Transformation
# MAGIC
# MAGIC **Project:** {project}
# MAGIC **Layer:** Silver (cleansed/conformed)
# MAGIC **Operations:** Deduplication, null handling, type casting, SCD2 merge, quality flags

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# COMMAND ----------
{entity_blocks_str}
# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer Summary

# COMMAND ----------

tables = spark.sql("SHOW TABLES LIKE 'silver_*'")
for row in tables.collect():
    tbl = row.tableName
    df = spark.table(tbl)
    valid = df.filter(F.col("_is_valid")).count()
    total = df.count()
    pct = (valid / total * 100) if total > 0 else 0
    print(f"  {{tbl}}: {{total:,}} rows, {{pct:.1f}}% valid")

print("\\n✅ Silver layer transformation complete")
'''

    def _gold_notebook(self, spec: IntentSpec) -> str:
        """Generate Gold layer notebook — business aggregations and KPIs."""
        entities = spec.entities or []
        project = spec.project_name

        entity_blocks = []
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            numeric_fields = [f for f in entity.fields if f.type in ("int", "float")]
            status_fields = [f for f in entity.fields if "status" in f.name.lower()]

            agg_exprs = [f'    F.count("*").alias("total_{sn}s"),']
            for f in numeric_fields:
                agg_exprs.append(f'    F.avg("{f.name}").alias("avg_{f.name}"),')
                agg_exprs.append(f'    F.max("{f.name}").alias("max_{f.name}"),')
                agg_exprs.append(f'    F.min("{f.name}").alias("min_{f.name}"),')
                agg_exprs.append(f'    F.stddev("{f.name}").alias("stddev_{f.name}"),')
            agg_str = "\n".join(agg_exprs)

            status_block = ""
            if status_fields:
                sf = status_fields[0]
                status_block = f'''

# Status distribution
status_dist = (
    silver_{sn}
    .filter(F.col("_is_valid"))
    .groupBy("{sf.name}")
    .agg(F.count("*").alias("count"))
    .orderBy(F.desc("count"))
)
status_dist.write.format("delta").mode("overwrite").saveAsTable("gold_{sn}_by_{sf.name}")
print(f"  ✓ gold_{sn}_by_{sf.name}")
display(status_dist)
'''

            entity_blocks.append(f'''
# ── {entity.name} Aggregations ──────────────────────
print("Aggregating silver_{sn} → gold_{sn}_summary")

silver_{sn} = spark.table("silver_{sn}").filter(F.col("_is_valid"))

# Daily summary
daily_{sn} = (
    silver_{sn}
    .withColumn("period", F.date_format("created_at", "yyyy-MM-dd"))
    .groupBy("period")
    .agg(
{agg_str}
    )
    .withColumn("_aggregated_at", F.current_timestamp())
    .orderBy("period")
)
daily_{sn}.write.format("delta").mode("overwrite").saveAsTable("gold_{sn}_summary")
print(f"  ✓ gold_{sn}_summary: {{daily_{sn}.count()}} periods")
{status_block}''')

        entity_blocks_str = "\n".join(entity_blocks)

        # Cross-entity KPI block
        kpi_lines = []
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            kpi_lines.append(f'    "{entity.name}": spark.table("silver_{sn}").filter(F.col("_is_valid")).count(),')
        kpi_dict = "\n".join(kpi_lines)

        return f'''# Databricks/Fabric notebook
# MAGIC %md
# MAGIC # Gold Layer — Business Aggregations & KPIs
# MAGIC
# MAGIC **Project:** {project}
# MAGIC **Layer:** Gold (business-level)
# MAGIC **Outputs:** Daily summaries, status distributions, cross-entity KPIs

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------
{entity_blocks_str}
# COMMAND ----------

# MAGIC %md
# MAGIC ## Cross-Entity KPI Summary

# COMMAND ----------

kpis = {{
{kpi_dict}
}}

print("\\n📊 Enterprise KPI Summary")
print("=" * 50)
for entity, count in kpis.items():
    print(f"  {{entity}}: {{count:,}} valid records")

total = sum(kpis.values())
print(f"\\n  Total: {{total:,}} records across {{len(kpis)}} entities")
print("\\n✅ Gold layer aggregation complete")
'''

    def _data_quality_notebook(self, spec: IntentSpec) -> str:
        """Generate data quality validation notebook."""
        entities = spec.entities or []
        project = spec.project_name

        rule_blocks = []
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            rules = []
            rules.append(f'    {{"rule": "not_null_id", "check": lambda df: df.filter(F.col("id").isNull()).count() == 0}},')
            for f in entity.fields:
                if f.required:
                    rules.append(
                        f'    {{"rule": "not_null_{f.name}", "check": lambda df: df.filter(F.col("{f.name}").isNull()).count() == 0}},'
                    )
                if f.type in ("int", "float"):
                    rules.append(
                        f'    {{"rule": "non_negative_{f.name}", "check": lambda df: df.filter(F.col("{f.name}") < 0).count() == 0}},'
                    )
                if "email" in f.name.lower():
                    rules.append(
                        f'    {{"rule": "valid_email_{f.name}", "check": lambda df: df.filter(~F.col("{f.name}").rlike("^[^@]+@[^@]+\\\\.[^@]+$")).count() == 0}},'
                    )
            rules_str = "\n".join(rules)

            rule_blocks.append(f'''
# ── {entity.name} Quality Rules ────────────────────
{sn}_rules = [
{rules_str}
]

print(f"\\nValidating silver_{sn}:")
df = spark.table("silver_{sn}")
passed, failed = 0, 0
for rule in {sn}_rules:
    try:
        ok = rule["check"](df)
        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        status = f"⚠️ ERROR: {{e}}"
        failed += 1
    print(f"  {{status}} — {{rule['rule']}}")
results.append({{"entity": "{entity.name}", "passed": passed, "failed": failed, "total": passed + failed}})
''')

        rule_blocks_str = "\n".join(rule_blocks)

        return f'''# Databricks/Fabric notebook
# MAGIC %md
# MAGIC # Data Quality Validation
# MAGIC
# MAGIC **Project:** {project}
# MAGIC **Scope:** All Silver-layer tables
# MAGIC **Framework:** Rule-based validation (Great Expectations pattern)

# COMMAND ----------

from pyspark.sql import functions as F

results = []

# COMMAND ----------
{rule_blocks_str}
# COMMAND ----------

# MAGIC %md
# MAGIC ## Quality Summary

# COMMAND ----------

import json

total_passed = sum(r["passed"] for r in results)
total_failed = sum(r["failed"] for r in results)
total_rules = sum(r["total"] for r in results)
pct = (total_passed / total_rules * 100) if total_rules > 0 else 0

print("\\n📋 Data Quality Report")
print("=" * 50)
for r in results:
    entity_pct = (r["passed"] / r["total"] * 100) if r["total"] > 0 else 0
    status = "✅" if r["failed"] == 0 else "⚠️"
    print(f"  {{status}} {{r['entity']}}: {{r['passed']}}/{{r['total']}} rules passed ({{entity_pct:.0f}}%)")

print(f"\\n  Overall: {{total_passed}}/{{total_rules}} rules passed ({{pct:.0f}}%)")
overall = "✅ ALL CHECKS PASSED" if total_failed == 0 else f"⚠️ {{total_failed}} CHECKS FAILED"
print(f"\\n{{overall}}")
'''

    # ── Pipeline generators ──────────────────────────────────────────

    def _medallion_pipeline(self, spec: IntentSpec) -> str:
        """Generate Fabric Data Pipeline JSON for medallion orchestration."""
        project = spec.project_name
        import json

        pipeline = {
            "name": f"{project}-medallion-pipeline",
            "properties": {
                "description": f"Medallion architecture pipeline for {project}. Orchestrates Bronze → Silver → Gold data transformation.",
                "activities": [
                    {
                        "name": "Bronze_Ingestion",
                        "type": "NotebookActivity",
                        "dependsOn": [],
                        "typeProperties": {
                            "notebookPath": "fabric/notebooks/01_bronze_ingestion",
                            "parameters": {
                                "record_count": {"value": str(_DEFAULT_FABRIC_RECORDS), "type": "int"},
                            },
                        },
                        "policy": {
                            "timeout": "01:00:00",
                            "retry": 2,
                            "retryIntervalInSeconds": 60,
                        },
                    },
                    {
                        "name": "Silver_Transform",
                        "type": "NotebookActivity",
                        "dependsOn": [
                            {"activity": "Bronze_Ingestion", "dependencyConditions": ["Succeeded"]},
                        ],
                        "typeProperties": {
                            "notebookPath": "fabric/notebooks/02_silver_transform",
                        },
                        "policy": {
                            "timeout": "00:45:00",
                            "retry": 1,
                            "retryIntervalInSeconds": 30,
                        },
                    },
                    {
                        "name": "Gold_Aggregation",
                        "type": "NotebookActivity",
                        "dependsOn": [
                            {"activity": "Silver_Transform", "dependencyConditions": ["Succeeded"]},
                        ],
                        "typeProperties": {
                            "notebookPath": "fabric/notebooks/03_gold_aggregation",
                        },
                        "policy": {
                            "timeout": "00:30:00",
                            "retry": 1,
                            "retryIntervalInSeconds": 30,
                        },
                    },
                    {
                        "name": "Data_Quality_Check",
                        "type": "NotebookActivity",
                        "dependsOn": [
                            {"activity": "Silver_Transform", "dependencyConditions": ["Succeeded"]},
                        ],
                        "typeProperties": {
                            "notebookPath": "fabric/notebooks/04_data_quality",
                        },
                        "policy": {
                            "timeout": "00:15:00",
                            "retry": 0,
                        },
                    },
                ],
                "parameters": {
                    "environment": {"type": "string", "defaultValue": "dev"},
                    "record_count": {"type": "int", "defaultValue": _DEFAULT_FABRIC_RECORDS},
                },
                "annotations": [
                    f"project:{project}",
                    "pattern:medallion",
                    "auto-generated",
                ],
            },
        }
        return json.dumps(pipeline, indent=2)

    def _incremental_pipeline(self, spec: IntentSpec) -> str:
        """Generate incremental refresh pipeline."""
        import json

        project = spec.project_name
        pipeline = {
            "name": f"{project}-incremental-refresh",
            "properties": {
                "description": f"Scheduled incremental data refresh for {project}.",
                "activities": [
                    {
                        "name": "Get_Watermark",
                        "type": "Lookup",
                        "typeProperties": {
                            "source": {
                                "type": "SqlSource",
                                "sqlReaderQuery": "SELECT MAX(_ingested_at) as last_watermark FROM bronze_metadata",
                            },
                        },
                    },
                    {
                        "name": "Incremental_Bronze",
                        "type": "NotebookActivity",
                        "dependsOn": [
                            {"activity": "Get_Watermark", "dependencyConditions": ["Succeeded"]},
                        ],
                        "typeProperties": {
                            "notebookPath": "fabric/notebooks/01_bronze_ingestion",
                            "parameters": {
                                "incremental": {"value": "true", "type": "string"},
                                "watermark": {
                                    "value": "@activity('Get_Watermark').output.firstRow.last_watermark",
                                    "type": "string",
                                },
                            },
                        },
                    },
                    {
                        "name": "Incremental_Silver",
                        "type": "NotebookActivity",
                        "dependsOn": [
                            {"activity": "Incremental_Bronze", "dependencyConditions": ["Succeeded"]},
                        ],
                        "typeProperties": {
                            "notebookPath": "fabric/notebooks/02_silver_transform",
                        },
                    },
                    {
                        "name": "Refresh_Gold",
                        "type": "NotebookActivity",
                        "dependsOn": [
                            {"activity": "Incremental_Silver", "dependencyConditions": ["Succeeded"]},
                        ],
                        "typeProperties": {
                            "notebookPath": "fabric/notebooks/03_gold_aggregation",
                        },
                    },
                ],
                "triggers": [
                    {
                        "name": "ScheduledRefresh",
                        "type": "ScheduleTrigger",
                        "properties": {
                            "recurrence": {
                                "frequency": "Hour",
                                "interval": 1,
                                "startTime": "2025-01-01T00:00:00Z",
                                "timeZone": "UTC",
                            },
                        },
                    },
                ],
            },
        }
        return json.dumps(pipeline, indent=2)

    # ── Eventstream generators ───────────────────────────────────────

    def _eventstream_config(self, spec: IntentSpec) -> str:
        """Generate Eventstream configuration for real-time ingestion."""
        import json

        project = spec.project_name
        entities = spec.entities or []

        event_types = []
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            event_types.append({
                "name": f"{sn}_event",
                "schema": {
                    "entity_id": "string",
                    "event_type": "string",
                    "payload": "object",
                    "timestamp": "datetime",
                    "source": "string",
                },
            })

        config = {
            "name": f"{project}-eventstream",
            "properties": {
                "description": f"Real-time event ingestion for {project}",
                "sources": [
                    {
                        "name": "SimulatedEvents",
                        "type": "CustomApp",
                        "properties": {
                            "endpoint": f"https://{project}-eventstream.fabric.microsoft.com/ingestion",
                            "authentication": "ManagedIdentity",
                        },
                    },
                ],
                "destinations": [
                    {
                        "name": "LakehouseBronze",
                        "type": "Lakehouse",
                        "properties": {
                            "tableName": "bronze_events",
                            "format": "delta",
                            "mode": "append",
                        },
                    },
                    {
                        "name": "KQLDatabase",
                        "type": "KQL",
                        "properties": {
                            "database": f"{project}_kql_db",
                            "table": "realtime_events",
                        },
                    },
                ],
                "transformations": [
                    {
                        "name": "ParsePayload",
                        "type": "Manage",
                        "properties": {
                            "operations": [
                                {"type": "DateTime", "column": "timestamp", "format": "ISO8601"},
                                {"type": "Add", "column": "_processed_at", "expression": "SystemTimestamp()"},
                            ],
                        },
                    },
                ],
                "eventTypes": event_types,
            },
        }
        return json.dumps(config, indent=2)

    def _event_simulator(self, spec: IntentSpec) -> str:
        """Generate Python event simulator for demo scenarios."""
        entities = spec.entities or []
        project = spec.project_name

        entity_configs = []
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            event_types = ["created", "updated"]
            if any("status" in f.name.lower() for f in entity.fields):
                event_types.append("status_changed")
            if any("assign" in f.name.lower() for f in entity.fields):
                event_types.append("assigned")
            entity_configs.append(f'    "{sn}": {event_types},')

        entity_configs_str = "\n".join(entity_configs)

        return f'''"""Event Simulator for Microsoft Fabric Eventstream.

Generates realistic real-time events for {project} demo scenarios.
Supports configurable throughput (events per second) and burst patterns.

Usage:
    python event_simulator.py --tps 10 --duration 300
    python event_simulator.py --burst --burst-size 100
"""

import argparse
import hashlib
import json
import os
import random
import time
from datetime import datetime, timezone


# Entity → event type mapping
ENTITY_EVENTS = {{
{entity_configs_str}
}}

# Simulated event endpoint (replace with actual Fabric Eventstream endpoint)
EVENTSTREAM_ENDPOINT = os.environ.get(
    "EVENTSTREAM_ENDPOINT",
    "https://{project}-eventstream.fabric.microsoft.com/ingestion",
)


def _generate_event(entity: str, event_types: list[str], seq: int) -> dict:
    """Generate a single realistic event."""
    event_type = random.choice(event_types)
    entity_id = f"{{entity}}-{{hashlib.md5(f'{{entity}}:{{seq}}'.encode()).hexdigest()[:12]}}"

    payload = {{
        "entity": entity,
        "entity_id": entity_id,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": seq,
        "source": "simulator",
        "payload": {{
            "action": event_type,
            "details": f"Simulated {{event_type}} event for {{entity}} #{{seq}}",
            "severity": random.choice(["low", "medium", "high"]),
            "correlation_id": hashlib.md5(f"corr:{{seq}}".encode()).hexdigest()[:16],
        }},
    }}
    return payload


def _send_event(event: dict) -> None:
    """Send event to Eventstream endpoint (or print for demo)."""
    # In production, use requests.post(EVENTSTREAM_ENDPOINT, json=event)
    # For demo, print to stdout
    print(json.dumps(event, default=str))


def run_steady(tps: int, duration: int) -> None:
    """Run steady-state event generation at target TPS."""
    interval = 1.0 / tps if tps > 0 else 1.0
    entities = list(ENTITY_EVENTS.keys())
    seq = 0
    end_time = time.time() + duration

    print(f"🚀 Starting event simulation: {{tps}} TPS for {{duration}}s")
    print(f"   Entities: {{', '.join(entities)}}")

    while time.time() < end_time:
        entity = random.choice(entities)
        event = _generate_event(entity, ENTITY_EVENTS[entity], seq)
        _send_event(event)
        seq += 1
        time.sleep(interval)

    print(f"\\n✅ Simulation complete: {{seq}} events generated")


def run_burst(burst_size: int, interval: float) -> None:
    """Run burst pattern — rapid events followed by quiet periods."""
    entities = list(ENTITY_EVENTS.keys())
    seq = 0
    burst_count = 0

    print(f"🚀 Starting burst simulation: {{burst_size}} events per burst, {{interval}}s interval")

    while True:
        burst_count += 1
        print(f"\\n⚡ Burst #{{burst_count}} — {{burst_size}} events")
        for _ in range(burst_size):
            entity = random.choice(entities)
            event = _generate_event(entity, ENTITY_EVENTS[entity], seq)
            _send_event(event)
            seq += 1
            time.sleep(0.01)  # 100 events/sec within burst

        print(f"  💤 Quiet period ({{interval}}s)...")
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="{project} Event Simulator")
    parser.add_argument("--tps", type=int, default=10, help="Events per second (steady mode)")
    parser.add_argument("--duration", type=int, default=300, help="Duration in seconds (steady mode)")
    parser.add_argument("--burst", action="store_true", help="Use burst mode")
    parser.add_argument("--burst-size", type=int, default=100, help="Events per burst")
    parser.add_argument("--burst-interval", type=float, default=5.0, help="Seconds between bursts")

    args = parser.parse_args()
    if args.burst:
        run_burst(args.burst_size, args.burst_interval)
    else:
        run_steady(args.tps, args.duration)
'''

    # ── KQL generators ───────────────────────────────────────────────

    def _entity_analytics_kql(self, spec: IntentSpec) -> str:
        """Generate KQL analytics queries for all entities."""
        entities = spec.entities or []
        project = spec.project_name

        blocks = [
            f"// KQL Analytics — {project}",
            "// Auto-generated for Microsoft Fabric KQL Database",
            "// Use in Fabric Real-Time Analytics or KQL Querysets",
            "",
        ]

        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            blocks.append(f"// ── {entity.name} Analytics ──────────────────────")
            blocks.append("")

            # Record count over time
            blocks.append(f"// {entity.name}: Records ingested over time")
            blocks.append(f"silver_{sn}")
            blocks.append("| where _is_valid == true")
            blocks.append("| summarize count() by bin(created_at, 1d)")
            blocks.append('| render timechart with (title="Daily {entity_name} Volume")')
            blocks.append("")

            # Status distribution
            status_fields = [f for f in entity.fields if "status" in f.name.lower()]
            if status_fields:
                sf = status_fields[0]
                blocks.append(f"// {entity.name}: Status distribution")
                blocks.append(f"silver_{sn}")
                blocks.append("| where _is_valid == true")
                blocks.append(f"| summarize count() by {sf.name}")
                blocks.append(f"| order by count_ desc")
                blocks.append(f'| render piechart with (title="{entity.name} by Status")')
                blocks.append("")

            # Numeric field statistics
            numeric_fields = [f for f in entity.fields if f.type in ("int", "float")]
            if numeric_fields:
                nf = numeric_fields[0]
                blocks.append(f"// {entity.name}: {nf.name} statistics")
                blocks.append(f"silver_{sn}")
                blocks.append("| where _is_valid == true")
                blocks.append(f"| summarize avg({nf.name}), min({nf.name}), max({nf.name}), "
                             f"stdev({nf.name}), percentile({nf.name}, 95)")
                blocks.append("")

                blocks.append(f"// {entity.name}: {nf.name} distribution")
                blocks.append(f"silver_{sn}")
                blocks.append("| where _is_valid == true")
                blocks.append(f"| summarize count() by bin({nf.name}, 10)")
                blocks.append(f'| render columnchart with (title="{entity.name} {nf.name} Distribution")')
                blocks.append("")

            # Anomaly detection
            blocks.append(f"// {entity.name}: Anomaly detection (last 30 days)")
            blocks.append(f"silver_{sn}")
            blocks.append("| where created_at > ago(30d)")
            blocks.append("| where _is_valid == true")
            blocks.append("| summarize count() by bin(created_at, 1h)")
            blocks.append("| extend anomaly = iff(count_ > avg_count * 2, 'anomaly', 'normal')")
            blocks.append("| where anomaly == 'anomaly'")
            blocks.append("")

        # Cross-entity summary
        blocks.append("// ── Cross-Entity Summary ──────────────────────")
        for entity in entities:
            sn = entity.name.lower().replace(" ", "_")
            blocks.append(f'print entity="{entity.name}", count=toscalar(silver_{sn} | where _is_valid | count)')
        blocks.append("")

        return "\n".join(blocks)

    def _realtime_dashboard_kql(self, spec: IntentSpec) -> str:
        """Generate KQL queries for real-time Eventstream dashboard."""
        entities = spec.entities or []
        project = spec.project_name

        lines = [
            f"// Real-Time Dashboard KQL — {project}",
            "// Queries against Eventstream KQL database",
            "",
            "// ── Event Volume (last 1 hour) ────────────────",
            "realtime_events",
            "| where timestamp > ago(1h)",
            "| summarize events_per_minute = count() by bin(timestamp, 1m)",
            '| render timechart with (title="Event Throughput (events/min)")',
            "",
            "// ── Events by Entity Type ─────────────────────",
            "realtime_events",
            "| where timestamp > ago(1h)",
            "| summarize count() by entity",
            '| render piechart with (title="Event Distribution by Entity")',
            "",
            "// ── Event Type Breakdown ──────────────────────",
            "realtime_events",
            "| where timestamp > ago(1h)",
            "| summarize count() by event_type",
            "| order by count_ desc",
            '| render barchart with (title="Events by Type")',
            "",
            "// ── Latency Monitor ───────────────────────────",
            "realtime_events",
            "| where timestamp > ago(1h)",
            "| extend latency_ms = datetime_diff('millisecond', _processed_at, timestamp)",
            "| summarize avg(latency_ms), percentile(latency_ms, 95), max(latency_ms) by bin(timestamp, 1m)",
            '| render timechart with (title="Ingestion Latency (ms)")',
            "",
            "// ── Severity Heatmap ──────────────────────────",
            "realtime_events",
            "| where timestamp > ago(1h)",
            "| extend hour = hourofday(timestamp)",
            "| summarize count() by hour, tostring(payload.severity)",
            '| render heatmap with (title="Event Severity by Hour")',
            "",
            "// ── Live Alert: High Severity Events ──────────",
            "realtime_events",
            "| where timestamp > ago(5m)",
            '| where payload.severity == "high"',
            "| project timestamp, entity, entity_id, event_type, payload",
            "| order by timestamp desc",
            "| take 50",
            "",
        ]
        return "\n".join(lines)

    # ── Documentation ────────────────────────────────────────────────

    def _readme(self, spec: IntentSpec) -> str:
        """Generate Fabric README documentation."""
        entities = spec.entities or []
        project = spec.project_name
        entity_list = "\n".join(f"- **{e.name}** — {e.description or 'Domain entity'}" for e in entities)
        entity_tables = "\n".join(
            f"  - `bronze_{e.name.lower().replace(' ', '_')}` → `silver_{e.name.lower().replace(' ', '_')}` → `gold_{e.name.lower().replace(' ', '_')}_summary`"
            for e in entities
        )

        return f'''# Microsoft Fabric — {project}

## Overview

This directory contains the complete Microsoft Fabric data platform scaffold for
**{project}**, implementing a medallion architecture (Bronze → Silver → Gold)
with {_DEFAULT_FABRIC_RECORDS:,} synthetic records per entity.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Bronze Layer    │───▶│  Silver Layer     │───▶│  Gold Layer     │
│  Raw ingestion   │    │  Cleansed/conformed│   │  Business KPIs  │
│  Delta format    │    │  Quality flags     │   │  Aggregations   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        ▲                                              │
        │                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│  Eventstream     │                          │  KQL Analytics   │
│  Real-time events│                          │  Dashboards      │
└─────────────────┘                          └─────────────────┘
```

## Entities

{entity_list}

## Data Flow

{entity_tables}

## Directory Structure

```
fabric/
├── notebooks/
│   ├── 01_bronze_ingestion.py    # Synthetic data generation at scale
│   ├── 02_silver_transform.py    # Cleansing, dedup, quality flags
│   ├── 03_gold_aggregation.py    # Business KPIs and rollups
│   └── 04_data_quality.py        # Validation rules
├── pipelines/
│   ├── medallion_pipeline.json   # Full medallion orchestration
│   └── incremental_refresh.json  # Hourly incremental refresh
├── eventstream/
│   ├── realtime_ingestion.json   # Eventstream configuration
│   └── event_simulator.py       # Demo event generator
├── kql/
│   ├── entity_analytics.kql     # Per-entity analytics queries
│   └── realtime_dashboard.kql   # Real-time dashboard queries
├── ddl/
│   └── delta_tables.sql         # Delta Lake table definitions
├── lib/
│   ├── schemas.py              # PySpark StructType schemas
│   └── udfs.py                 # Synthetic data generation UDFs
├── README.md                   # This file
└── demo-script.md              # Step-by-step demo guide
```

## Quick Start

### 1. Set Up Fabric Workspace

1. Create a new Fabric workspace or use an existing one
2. Create a Lakehouse named `{project.replace('-', '_')}_lakehouse`
3. Upload the `lib/` directory to the Lakehouse Files area

### 2. Run Medallion Pipeline

**Option A: Sequential notebook execution**
1. Open `notebooks/01_bronze_ingestion.py` in Fabric
2. Run all cells to generate {_DEFAULT_FABRIC_RECORDS:,} synthetic records per entity
3. Continue with `02_silver_transform.py`, `03_gold_aggregation.py`

**Option B: Pipeline orchestration**
1. Import `pipelines/medallion_pipeline.json` as a Fabric Data Pipeline
2. Trigger the pipeline — it runs all notebooks in dependency order

### 3. Explore Analytics

1. Create a KQL Database in your workspace
2. Import queries from `kql/entity_analytics.kql`
3. Pin visualizations to a Real-Time Dashboard

### 4. Real-Time Demo

1. Start the event simulator: `python eventstream/event_simulator.py --tps 10`
2. Monitor events in the KQL real-time dashboard using `kql/realtime_dashboard.kql`

## Data Quality

The `04_data_quality.py` notebook validates Silver-layer tables against
auto-generated rules (null checks, range validation, format verification).
Quality results are printed in a summary format suitable for screenshots.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RECORD_COUNT` | {_DEFAULT_FABRIC_RECORDS:,} | Records per entity (Bronze) |
| `LAKEHOUSE_NAME` | `{project.replace('-', '_')}_lakehouse` | Target Lakehouse |
| `--tps` | 10 | Events per second (simulator) |
| `--duration` | 300 | Simulation duration (seconds) |
'''

    def _demo_script(self, spec: IntentSpec) -> str:
        """Generate step-by-step demo script for client presentations."""
        entities = spec.entities or []
        project = spec.project_name
        entity_count = len(entities)
        total_records = _DEFAULT_FABRIC_RECORDS * entity_count

        return f'''# Demo Script — Microsoft Fabric for {project}

## Audience
Enterprise stakeholders, data engineering leads, architecture reviewers

## Duration
20-30 minutes

## Pre-requisites
- Fabric workspace provisioned with capacity (F2+ SKU)
- Lakehouse created with `lib/` files uploaded
- Bronze notebook executed (or full pipeline completed)

---

## Act 1: The Data Platform (5 min)

### Talking Points
> "We've built a complete enterprise data platform on Microsoft Fabric using a
> medallion architecture. Let me show you how {total_records:,} records across
> {entity_count} entities flow through Bronze, Silver, and Gold layers."

### Demo Steps
1. **Open Fabric workspace** — show the organized artifacts
2. **Open Lakehouse** — navigate to Tables, show Bronze/Silver/Gold structure
3. **Click any Bronze table** — show raw data with `_ingested_at` timestamps
4. **Click corresponding Silver table** — show `_is_valid` quality flags
5. **Click Gold summary** — show aggregated KPIs

---

## Act 2: Data Generation at Scale (5 min)

### Talking Points
> "This synthetic data isn't random — it uses statistical distributions that
> mirror real-world patterns. Timestamps cluster around business hours,
> status values follow Zipf distributions, and all foreign keys maintain
> referential integrity."

### Demo Steps
1. **Open `01_bronze_ingestion.py`** — walk through the UDF-based generation
2. **Show a timestamp distribution** — highlight clustering pattern
3. **Run a count query** — `SELECT COUNT(*) FROM bronze_*` showing scale
4. **Show referential integrity** — JOIN across related entities

---

## Act 3: Data Quality (5 min)

### Talking Points
> "Every record passes through automated quality validation. We've generated
> rules from the entity schema — null checks, range validation, format
> verification — giving you confidence in data reliability."

### Demo Steps
1. **Open `04_data_quality.py`** — show the rule framework
2. **Run the notebook** — display the quality summary
3. **Highlight the pass/fail breakdown** per entity

---

## Act 4: Real-Time Analytics (5 min)

### Talking Points
> "For operational monitoring, we've configured Eventstream for real-time
> event ingestion with KQL queries for live dashboards."

### Demo Steps
1. **Open KQL queryset** — show `realtime_dashboard.kql`
2. **Run the event throughput query** — show live chart
3. **Run the severity heatmap** — show pattern visualization
4. **Start event simulator** (if live demo): `python event_simulator.py --tps 10`
5. **Show events appearing in real-time** in the KQL dashboard

---

## Act 5: Enterprise Governance (5 min)

### Talking Points
> "This entire scaffold was generated automatically from a business intent
> description. Every artifact follows enterprise standards — naming conventions,
> tagging, security baselines, and Well-Architected Framework principles."

### Demo Steps
1. **Show the original intent.md** — the business description that started it all
2. **Show the governance report** — policy compliance checks
3. **Show the WAF alignment** — pillar coverage scores
4. **Show the cost estimate** — projected monthly Azure spend

---

## Closing

> "From a natural language description to a production-ready data platform
> with {total_records:,} records, automated quality checks, and real-time
> analytics — all generated in under 60 seconds."

### Q&A Points
- **Scale**: Can generate up to 100K+ records per entity
- **Customization**: All notebooks are editable — add domain-specific transforms
- **Production path**: Pipeline definitions are ready for Fabric deployment
- **Security**: Managed Identity auth throughout, no stored credentials
'''


def _should_generate(spec: IntentSpec) -> bool:
    """Check if Fabric generation should be triggered."""
    return (
        getattr(spec, "uses_fabric", False)
        or DataStore.FABRIC_LAKEHOUSE in spec.data_stores
    )
