"""Tests for FabricGenerator -- Microsoft Fabric data platform scaffolding."""

from __future__ import annotations

from src.orchestrator.generators.fabric_generator import FabricGenerator
from src.orchestrator.intent_schema import (
    AppType,
    AuthModel,
    ComplianceFramework,
    DataStore,
    EntitySpec,
    FieldSpec,
    IntentSpec,
    NetworkingModel,
    ObservabilityRequirements,
    SecurityRequirements,
)


def _make_fabric_spec() -> IntentSpec:
    return IntentSpec(
        project_name="fabric-test",
        app_type=AppType.API,
        description="A test project with Fabric integration",
        raw_intent="Build a data platform with Fabric lakehouse",
        data_stores=[DataStore.FABRIC_LAKEHOUSE],
        uses_fabric=True,
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.GENERAL,
            data_classification="internal",
        ),
        observability=ObservabilityRequirements(),
        networking=NetworkingModel.PUBLIC_RESTRICTED,
        entities=[
            EntitySpec(
                name="Order",
                fields=[
                    FieldSpec(name="order_number", type="str", description="Unique order number"),
                    FieldSpec(name="customer_id", type="str", description="Customer reference"),
                    FieldSpec(name="total_amount", type="float", description="Total order amount"),
                    FieldSpec(name="status", type="str", description="Order status"),
                    FieldSpec(name="created_at", type="datetime", description="When created"),
                ],
            ),
            EntitySpec(
                name="Product",
                fields=[
                    FieldSpec(name="sku", type="str", description="Product SKU"),
                    FieldSpec(name="name", type="str", description="Product name"),
                    FieldSpec(name="price", type="float", description="Unit price"),
                    FieldSpec(name="category", type="str", description="Category"),
                ],
            ),
        ],
    )


def _make_non_fabric_spec() -> IntentSpec:
    return IntentSpec(
        project_name="no-fabric",
        app_type=AppType.API,
        description="A test project without Fabric",
        raw_intent="Build a simple api",
        data_stores=[DataStore.COSMOS_DB],
        uses_fabric=False,
        security=SecurityRequirements(
            auth_model=AuthModel.MANAGED_IDENTITY,
            compliance_framework=ComplianceFramework.GENERAL,
            data_classification="internal",
        ),
        observability=ObservabilityRequirements(),
        networking=NetworkingModel.PUBLIC_RESTRICTED,
        entities=[
            EntitySpec(
                name="Item",
                fields=[FieldSpec(name="name", type="str", description="Name")],
            ),
        ],
    )


class TestFabricGenerator:
    def test_generate_produces_files_for_fabric_spec(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        assert len(files) > 0

    def test_generate_empty_for_non_fabric_spec(self):
        gen = FabricGenerator()
        files = gen.generate(_make_non_fabric_spec())
        assert len(files) == 0

    def test_bronze_notebook_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        bronze_key = [k for k in files if "bronze" in k.lower() and "notebook" in k.lower()]
        assert len(bronze_key) >= 1, f"Expected bronze notebook, got keys: {list(files.keys())}"

    def test_silver_notebook_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        silver_key = [k for k in files if "silver" in k.lower() and "notebook" in k.lower()]
        assert len(silver_key) >= 1

    def test_gold_notebook_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        gold_key = [k for k in files if "gold" in k.lower() and "notebook" in k.lower()]
        assert len(gold_key) >= 1

    def test_pipeline_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        pipeline_key = [k for k in files if "pipeline" in k.lower()]
        assert len(pipeline_key) >= 1

    def test_kql_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        kql_key = [k for k in files if ".kql" in k.lower()]
        assert len(kql_key) >= 1

    def test_entity_names_in_bronze_notebook(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        bronze_files = [v for k, v in files.items() if "bronze" in k.lower()]
        assert any("Order" in content or "order" in content for content in bronze_files)
        assert any("Product" in content or "product" in content for content in bronze_files)

    def test_readme_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        readme_key = [k for k in files if "readme" in k.lower() or "README" in k]
        assert len(readme_key) >= 1

    def test_demo_script_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        demo_key = [k for k in files if "demo" in k.lower()]
        assert len(demo_key) >= 1

    def test_data_quality_notebook_generated(self):
        gen = FabricGenerator()
        files = gen.generate(_make_fabric_spec())
        dq_key = [k for k in files if "quality" in k.lower() or "dq" in k.lower()]
        assert len(dq_key) >= 1
