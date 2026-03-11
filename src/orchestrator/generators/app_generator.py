"""Application Generator -- produces sample application code.

Generates a minimal but production-grade application with:
    - Health endpoint
    - Managed Identity integration
    - Key Vault client
    - Storage client (if applicable)
    - Structured logging
    - Dockerfile
    - Dependency file

Supports multiple languages:
    - Python (FastAPI)  -- default
    - Node.js (Express)
    - .NET (ASP.NET Core minimal API)
"""

from __future__ import annotations

from src.orchestrator.intent_schema import DataStore, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


class AppGenerator:
    """Generates application scaffold -- multi-language support."""

    def generate(self, spec: IntentSpec) -> dict[str, str]:
        """Generate application files based on spec.language."""
        logger.info("app_generator.start", project=spec.project_name, language=spec.language)

        language = spec.language.lower()
        if language == "node":
            files = self._generate_node(spec)
        elif language == "dotnet":
            files = self._generate_dotnet(spec)
        else:
            files = self._generate_python(spec)

        logger.info("app_generator.complete", file_count=len(files), language=language)
        return files

    # ===============================================================
    # Python / FastAPI
    # ===============================================================

    def _generate_python(self, spec: IntentSpec) -> dict[str, str]:
        """Generate Python/FastAPI scaffold with enterprise DDD layout."""
        files: dict[str, str] = {}
        files["src/__init__.py"] = '"""Generated source package."""\n'
        files["src/app/__init__.py"] = '"""Generated application package."""\n'
        files["src/app/main.py"] = self._python_main(spec)
        files["src/app/requirements.txt"] = self._python_requirements(spec)
        files["src/app/Dockerfile"] = self._python_dockerfile(spec)

        # DDD layered architecture
        files["src/app/api/__init__.py"] = '"""API layer -- versioned routers."""\n'
        files["src/app/api/v1/__init__.py"] = '"""API v1 router package."""\n'
        files["src/app/api/v1/router.py"] = self._python_v1_router(spec)
        files["src/app/api/v1/schemas.py"] = self._python_v1_schemas(spec)
        files["src/app/core/__init__.py"] = '"""Core layer -- services, config, and dependencies."""\n'
        files["src/app/core/config.py"] = self._python_core_config(spec)
        files["src/app/core/dependencies.py"] = self._python_core_dependencies(spec)
        files["src/app/core/services.py"] = self._python_core_services(spec)
        return files

    # ===============================================================
    # Node.js / Express
    # ===============================================================

    def _generate_node(self, spec: IntentSpec) -> dict[str, str]:
        """Generate Node.js/Express scaffold."""
        files: dict[str, str] = {}
        files["src/app/index.js"] = self._node_main(spec)
        files["src/app/package.json"] = self._node_package_json(spec)
        files["src/app/Dockerfile"] = self._node_dockerfile(spec)
        files["src/app/.env.example"] = self._node_env_example(spec)
        return files

    # ===============================================================
    # .NET / ASP.NET Core
    # ===============================================================

    def _generate_dotnet(self, spec: IntentSpec) -> dict[str, str]:
        """Generate .NET/ASP.NET Core minimal API scaffold."""
        files: dict[str, str] = {}
        files["src/app/Program.cs"] = self._dotnet_program(spec)
        files[f"src/app/{spec.project_name}.csproj"] = self._dotnet_csproj(spec)
        files["src/app/Dockerfile"] = self._dotnet_dockerfile(spec)
        files["src/app/appsettings.json"] = self._dotnet_appsettings(spec)
        return files

    def _python_main(self, spec: IntentSpec) -> str:
        storage_imports = ""
        storage_client = ""
        storage_endpoint = ""

        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_imports = """
from azure.storage.blob import BlobServiceClient
"""
            storage_client = """
# -- Storage Client ---------------------------------------------------
def get_blob_client() -> BlobServiceClient:
    \"\"\"Create an authenticated Blob Storage client using Managed Identity.\"\"\"
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )
    account_url = os.getenv("STORAGE_ACCOUNT_URL", "")
    if not account_url:
        raise ValueError("STORAGE_ACCOUNT_URL environment variable not set")
    return BlobServiceClient(account_url=account_url, credential=credential)
"""
            storage_endpoint = """

@app.get("/storage/status")
async def storage_status():
    \"\"\"Check storage account connectivity.\"\"\"
    try:
        client = get_blob_client()
        containers = list(client.list_containers(max_results=1))
        return {
            "status": "connected",
            "containers_accessible": True,
        }
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": str(e)},
        )
"""

        return f"""\"\"\"Enterprise DevEx Orchestrator -- Generated Application.

Project: {spec.project_name}
Description: {spec.description}
Generated by: Enterprise DevEx Orchestrator Agent

This is a production-grade FastAPI application with:
- Health check endpoint
- Managed Identity authentication
- Key Vault integration
- Structured logging
\"\"\"

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
{storage_imports}
from api.v1.router import router as v1_router

# -- Configuration ----------------------------------------------------
APP_NAME = "{spec.project_name}"
VERSION = "1.0.0"

# -- Logging ----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}}',
)
logger = logging.getLogger(APP_NAME)

# -- FastAPI Application ---------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="{spec.description}",
    docs_url="/docs",
    redoc_url=None,
)

# -- Mount versioned API router --------------------------------------
app.include_router(v1_router, prefix="/api/v1", tags=["v1"])


# -- Key Vault Client ------------------------------------------------
def get_keyvault_client() -> SecretClient:
    \"\"\"Create an authenticated Key Vault client using Managed Identity.
    
    Supports two configuration patterns:
    1. KEY_VAULT_URI - full vault URL (https://vault-name.vault.azure.net)
    2. KEY_VAULT_NAME - vault name only (will construct URL)
    \"\"\"
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )
    
    # Try full URI first (recommended)
    vault_uri = os.getenv("KEY_VAULT_URI", "")
    if vault_uri:
        return SecretClient(vault_url=vault_uri, credential=credential)
    
    # Fallback to name-based construction
    vault_name = os.getenv("KEY_VAULT_NAME", "")
    if not vault_name:
        raise ValueError("Either KEY_VAULT_URI or KEY_VAULT_NAME must be set")
    
    return SecretClient(
        vault_url=f"https://{{vault_name}}.vault.azure.net",
        credential=credential
    )

{storage_client}
# -- Health Endpoint --------------------------------------------------
@app.get("/health")
async def health():
    \"\"\"Health check endpoint for liveness and readiness probes.\"\"\"
    return {{
        "status": "healthy",
        "service": APP_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }}


# -- Root Endpoint (HTML Landing Page) ------
@app.get("/")
async def root():
    \"\"\"Root endpoint with basic HTML response.\"\"\"
    html = f\"\"\"<!DOCTYPE html>
<html>
<head>
    <title>{{APP_NAME}}</title>
    <style>
        body {{{{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}}}
        .container {{{{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }}}}
        h1 {{{{ color: #333; }}}}
        a {{{{ display: inline-block; margin-top: 10px; padding: 10px 15px; background: #0078d4; color: white; text-decoration: none; border-radius: 4px; }}}}
        a:hover {{{{ background: #106ebe; }}}}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>{{APP_NAME}}</h1>
        <p>Version: {{VERSION}}</p>
        <p>Status: Running</p>
        <a href=\"/docs\">📚 API Documentation</a>
        <a href=\"/health\">💚 Health Check</a>
        <a href=\"/keyvault/status\">🔐 Key Vault Status</a>
    </div>
</body>
</html>
\"\"\"
    return HTMLResponse(content=html)


# -- Key Vault Status ------------------------------------------------
@app.get("/keyvault/status")
async def keyvault_status():
    \"\"\"Check Key Vault connectivity via Managed Identity.\"\"\"
    try:
        client = get_keyvault_client()
        # List secrets to verify access (limited to 1)
        secrets = list(client.list_properties_of_secrets(max_page_size=1))
        return {{
            "status": "connected",
            "vault_accessible": True,
        }}
    except Exception as e:
        logger.error(f"Key Vault health check failed: {{e}}")
        return JSONResponse(
            status_code=503,
            content={{"status": "error", "detail": str(e)}},
        )

{storage_endpoint}
# -- Startup Event ----------------------------------------------------
@app.on_event("startup")
async def startup():
    \"\"\"Application startup tasks.\"\"\"
    logger.info(f"{{APP_NAME}} v{{VERSION}} starting up")
    logger.info(f"Environment: {{os.getenv('ENVIRONMENT', 'unknown')}}")


@app.on_event("shutdown")
async def shutdown():
    \"\"\"Application shutdown tasks.\"\"\"
    logger.info(f"{{APP_NAME}} shutting down")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
"""

    def _python_requirements(self, spec: IntentSpec) -> str:
        reqs = """# Enterprise DevEx Orchestrator -- Generated Application Dependencies
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
azure-identity>=1.15.0
azure-keyvault-secrets>=4.8.0
pydantic>=2.5.0
python-dotenv>=1.0.0
"""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            reqs += "azure-storage-blob>=12.19.0\n"
        if DataStore.COSMOS_DB in spec.data_stores:
            reqs += "azure-cosmos>=4.5.0\n"

        return reqs

    def _python_dockerfile(self, spec: IntentSpec) -> str:
        return f"""# ===================================================================
# Dockerfile -- {spec.project_name}
# Multi-stage build for minimal production image
# ===================================================================

# -- Build Stage ------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -- Runtime Stage ----------------------------------------------------
FROM python:3.11-slim AS runtime

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Security: non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
"""

    # ===============================================================
    # Python DDD architecture layer files
    # ===============================================================

    def _python_v1_router(self, spec: IntentSpec) -> str:
        storage_routes = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_routes = """

@router.get("/storage/containers", summary="List storage containers")
async def list_containers(
    storage: BlobServiceClient = Depends(get_blob_service),
):
    containers = [c["name"] for c in storage.list_containers(max_results=10)]
    return {"containers": containers}
"""

        storage_import = ""
        storage_dep = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_import = "\nfrom azure.storage.blob import BlobServiceClient"
            storage_dep = "\nfrom core.dependencies import get_blob_service"

        return f'''"""API v1 router -- versioned business endpoints.

Mount this router in main.py under /api/v1.
Add domain-specific routes here as the application grows.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from api.v1.schemas import ItemCreate, ItemResponse
from core.dependencies import get_settings
from core.config import Settings
from core.services import ItemService{storage_import}{storage_dep}

router = APIRouter()


@router.get("/items", response_model=list[ItemResponse], summary="List items")
async def list_items(
    settings: Settings = Depends(get_settings),
):
    """Return items from the service layer."""
    svc = ItemService(project_name=settings.app_name)
    return svc.list_items()


@router.post("/items", response_model=ItemResponse, status_code=201, summary="Create item")
async def create_item(
    payload: ItemCreate,
    settings: Settings = Depends(get_settings),
):
    """Create a new item via the service layer."""
    svc = ItemService(project_name=settings.app_name)
    return svc.create_item(payload.name, payload.description)
{storage_routes}'''

    def _python_v1_schemas(self, spec: IntentSpec) -> str:
        return f'''"""API v1 request/response schemas.

Keep Pydantic models here so routers stay thin.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    name: str = Field(..., min_length=1, max_length=120, description="Item name")
    description: str = Field(default="", max_length=500, description="Item description")


class ItemResponse(BaseModel):
    """Schema returned by item endpoints."""

    id: str = Field(..., description="Unique item identifier")
    name: str = Field(..., description="Item name")
    description: str = Field(default="", description="Item description")
    project: str = Field(..., description="Owning project name")
'''

    def _python_core_config(self, spec: IntentSpec) -> str:
        storage_field = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_field = '\n    storage_account_url: str = Field(default="", description="Azure Storage account URL")'

        return f'''"""Application configuration via pydantic-settings.

Environment variables are automatically loaded.  Values can be
overridden with a .env file during local development.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised configuration -- reads from environment variables."""

    app_name: str = Field(default="{spec.project_name}", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="{spec.environment}", description="Runtime environment")
    port: int = Field(default=8000, description="HTTP listen port")

    # Azure integration
    azure_client_id: str = Field(default="", description="Managed identity client ID")
    key_vault_uri: str = Field(default="", description="Key Vault URI")
    key_vault_name: str = Field(default="", description="Key Vault name (fallback)"){storage_field}

    model_config = {{"env_file": ".env", "extra": "ignore"}}
'''

    def _python_core_dependencies(self, spec: IntentSpec) -> str:
        storage_dep = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_dep = """

def get_blob_service() -> BlobServiceClient:
    \"\"\"Dependency that yields an authenticated BlobServiceClient.\"\"\"
    from azure.storage.blob import BlobServiceClient

    settings = get_settings()
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.azure_client_id or None
    )
    if not settings.storage_account_url:
        raise ValueError("STORAGE_ACCOUNT_URL not configured")
    return BlobServiceClient(
        account_url=settings.storage_account_url, credential=credential
    )
"""

        return f'''"""Dependency injection helpers for FastAPI.

Use these with `Depends()` in route functions to obtain
configured clients and settings.
"""

from __future__ import annotations

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from core.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def get_keyvault_client() -> SecretClient:
    \"\"\"Dependency that yields an authenticated SecretClient.\"\"\"
    settings = get_settings()
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.azure_client_id or None
    )
    vault_uri = settings.key_vault_uri
    if not vault_uri and settings.key_vault_name:
        vault_uri = f"https://{{settings.key_vault_name}}.vault.azure.net"
    if not vault_uri:
        raise ValueError("KEY_VAULT_URI or KEY_VAULT_NAME must be set")
    return SecretClient(vault_url=vault_uri, credential=credential)
{storage_dep}'''

    def _python_core_services(self, spec: IntentSpec) -> str:
        return f'''"""Business service layer.

Put domain logic here, not in routers.  Services are framework-agnostic
and can be tested independently of FastAPI.
"""

from __future__ import annotations

import uuid


class ItemService:
    """Example domain service -- replace with real business logic."""

    def __init__(self, project_name: str = "{spec.project_name}") -> None:
        self.project_name = project_name
        # In production: inject a repository / data-access object here.

    def list_items(self) -> list[dict]:
        """Return a list of items (stub -- wire to a real data store)."""
        return [
            {{
                "id": "sample-001",
                "name": "Example Item",
                "description": "Replace this stub with your data store query.",
                "project": self.project_name,
            }}
        ]

    def create_item(self, name: str, description: str = "") -> dict:
        """Create and return a new item (stub -- wire to a real data store)."""
        return {{
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "project": self.project_name,
        }}
'''

    # ===============================================================
    # Node.js / Express -- implementation methods
    # ===============================================================

    def _node_main(self, spec: IntentSpec) -> str:
        storage_require = ""
        storage_route = ""

        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_require = 'const { BlobServiceClient } = require("@azure/storage-blob");\n'
            storage_route = """
// -- Storage Status --------------------------------------------------
app.get("/storage/status", async (req, res) => {{
  try {{
    const credential = new DefaultAzureCredential();
    const blobClient = new BlobServiceClient(
      process.env.STORAGE_ACCOUNT_URL || "",
      credential
    );
    const iter = blobClient.listContainers({{ maxPageSize: 1 }});
    await iter.next();
    res.json({{ status: "connected", containers_accessible: true }});
  }} catch (err) {{
    console.error("Storage health check failed:", err.message);
    res.status(503).json({{ status: "error", detail: err.message }});
  }}
}});
"""

        return f"""// ===================================================================
// Enterprise DevEx Orchestrator -- Generated Application (Node.js)
//
// Project: {spec.project_name}
// Description: {spec.description}
// ===================================================================

const express = require("express");
const {{ DefaultAzureCredential }} = require("@azure/identity");
const {{ SecretClient }} = require("@azure/keyvault-secrets");
{storage_require}
const app = express();
const APP_NAME = "{spec.project_name}";
const VERSION = "1.0.0";
const PORT = parseInt(process.env.PORT || "8000", 10);

app.use(express.json());

// -- Health Endpoint -------------------------------------------------
app.get("/health", (req, res) => {{
  res.json({{
    status: "healthy",
    service: APP_NAME,
    version: VERSION,
    timestamp: new Date().toISOString(),
  }});
}});

// -- Root Endpoint (HTML Landing Page) -------------------------------
app.get("/", (req, res) => {{
  const html = `<!DOCTYPE html>
<html>
<head>
    <title>${{APP_NAME}}</title>
    <style>
        body {{{{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}}}
        .container {{{{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }}}}
        h1 {{{{ color: #333; }}}}
        a {{{{ display: inline-block; margin-top: 10px; padding: 10px 15px; background: #0078d4; color: white; text-decoration: none; border-radius: 4px; }}}}
        a:hover {{{{ background: #106ebe; }}}}
    </style>
</head>
<body>
    <div class="container">
        <h1>${{APP_NAME}}</h1>
        <p>Version: ${{VERSION}}</p>
        <p>Status: Running</p>
        <a href="/health">Health Check</a>
        <a href="/keyvault/status">Key Vault Status</a>
    </div>
</body>
</html>`;
  res.send(html);
}});

// -- Key Vault Status ------------------------------------------------
app.get("/keyvault/status", async (req, res) => {{
  try {{
    const credential = new DefaultAzureCredential();
    const vaultUri = process.env.KEY_VAULT_URI || "";
    const vaultName = process.env.KEY_VAULT_NAME || "";
    let vaultUrl = vaultUri;
    if (!vaultUrl && vaultName) {{
      vaultUrl = `https://${{vaultName}}.vault.azure.net`;
    }}
    if (!vaultUrl) throw new Error("KEY_VAULT_URI or KEY_VAULT_NAME must be set");
    const client = new SecretClient(
      vaultUrl,
      credential
    );
    const iter = client.listPropertiesOfSecrets({{ maxPageSize: 1 }});
    await iter.next();
    res.json({{ status: "connected", vault_accessible: true }});
  }} catch (err) {{
    console.error("Key Vault health check failed:", err.message);
    res.status(503).json({{ status: "error", detail: err.message }});
  }}
}});
{storage_route}
app.listen(PORT, () => {{
  console.log(`${{APP_NAME}} v${{VERSION}} listening on port ${{PORT}}`);
}});
"""

    def _node_package_json(self, spec: IntentSpec) -> str:
        deps = {
            "express": "^4.18.0",
            "@azure/identity": "^4.0.0",
            "@azure/keyvault-secrets": "^4.8.0",
        }
        if DataStore.BLOB_STORAGE in spec.data_stores:
            deps["@azure/storage-blob"] = "^12.17.0"
        if DataStore.COSMOS_DB in spec.data_stores:
            deps["@azure/cosmos"] = "^4.0.0"

        import json as _json

        deps_str = _json.dumps(deps, indent=4)

        return f"""{{
  "name": "{spec.project_name}",
  "version": "1.0.0",
  "description": "{spec.description}",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "dev": "node --watch index.js",
    "test": "jest --coverage"
  }},
  "dependencies": {deps_str},
  "devDependencies": {{
    "jest": "^29.7.0"
  }},
  "engines": {{
    "node": ">=20.0.0"
  }}
}}
"""

    def _node_dockerfile(self, spec: IntentSpec) -> str:
        return f"""# ===================================================================
# Dockerfile -- {spec.project_name} (Node.js)
# Multi-stage build for minimal production image
# ===================================================================

FROM node:20-slim AS builder
WORKDIR /build
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-slim AS runtime
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /build/node_modules ./node_modules
COPY . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:8000/health', r => r.statusCode === 200 ? process.exit(0) : process.exit(1))"
CMD ["node", "index.js"]
"""

    def _node_env_example(self, spec: IntentSpec) -> str:
        lines = [
            "# Application configuration",
            "PORT=8000",
            f"ENVIRONMENT={spec.environment}",
            "",
            "# Azure Managed Identity",
            "AZURE_CLIENT_ID=",
            "",
            "# Key Vault",
            "KEY_VAULT_NAME=",
        ]
        if DataStore.BLOB_STORAGE in spec.data_stores:
            lines += ["", "# Storage", "STORAGE_ACCOUNT_URL="]
        return "\n".join(lines) + "\n"

    # ===============================================================
    # .NET / ASP.NET Core -- implementation methods
    # ===============================================================

    def _dotnet_program(self, spec: IntentSpec) -> str:
        storage_usings = ""
        storage_services = ""
        storage_endpoint = ""

        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_usings = "using Azure.Storage.Blobs;\n"
            storage_services = """
builder.Services.AddSingleton(sp =>
{{
    var credential = new DefaultAzureCredential();
    var accountUrl = builder.Configuration["STORAGE_ACCOUNT_URL"] ?? "";
    return new BlobServiceClient(new Uri(accountUrl), credential);
}});
"""
            storage_endpoint = """
app.MapGet("/storage/status", async (BlobServiceClient blobClient) =>
{{
    try
    {{
        await foreach (var _ in blobClient.GetBlobContainersAsync().AsPages(pageSizeHint: 1))
        {{ break; }}
        return Results.Ok(new {{ status = "connected", containers_accessible = true }});
    }}
    catch (Exception ex)
    {{
        return Results.Json(new {{ status = "error", detail = ex.Message }}, statusCode: 503);
    }}
}});
"""

        return f"""// ===================================================================
// Enterprise DevEx Orchestrator -- Generated Application (.NET)
//
// Project: {spec.project_name}
// Description: {spec.description}
// ===================================================================

using Azure.Identity;
using Azure.Security.KeyVault.Secrets;
{storage_usings}
var builder = WebApplication.CreateBuilder(args);

var appName = "{spec.project_name}";
var version = "1.0.0";

// -- Key Vault Client ------------------------------------------------
builder.Services.AddSingleton(sp =>
{{
    var credential = new DefaultAzureCredential();
    var vaultUri = builder.Configuration["KEY_VAULT_URI"] ?? "";
    var vaultName = builder.Configuration["KEY_VAULT_NAME"] ?? "";
    if (string.IsNullOrEmpty(vaultUri) && !string.IsNullOrEmpty(vaultName))
        vaultUri = $"https://{{vaultName}}.vault.azure.net";
    if (string.IsNullOrEmpty(vaultUri))
        throw new InvalidOperationException("KEY_VAULT_URI or KEY_VAULT_NAME must be set");
    return new SecretClient(new Uri(vaultUri), credential);
}});
{storage_services}
var app = builder.Build();

// -- Health Endpoint -------------------------------------------------
app.MapGet("/health", () => Results.Ok(new
{{
    status = "healthy",
    service = appName,
    version,
    timestamp = DateTime.UtcNow.ToString("o"),
}}));

// -- Root Endpoint (HTML Landing Page) -------------------------------
app.MapGet("/", () =>
{{
    var html = $@"<!DOCTYPE html>
<html>
<head>
    <title>{{appName}}</title>
    <style>
        body {{{{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}}}
        .container {{{{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }}}}
        h1 {{{{ color: #333; }}}}
        a {{{{ display: inline-block; margin-top: 10px; padding: 10px 15px; background: #0078d4; color: white; text-decoration: none; border-radius: 4px; }}}}
        a:hover {{{{ background: #106ebe; }}}}
    </style>
</head>
<body>
    <div class=""container"">
        <h1>{{appName}}</h1>
        <p>Version: {{version}}</p>
        <p>Status: Running</p>
        <a href=""/health"">Health Check</a>
        <a href=""/keyvault/status"">Key Vault Status</a>
    </div>
</body>
</html>";
    return Results.Content(html, "text/html");
}});

// -- Key Vault Status ------------------------------------------------
app.MapGet("/keyvault/status", async (SecretClient kvClient) =>
{{
    try
    {{
        await foreach (var _ in kvClient.GetPropertiesOfSecretsAsync().AsPages(pageSizeHint: 1))
        {{ break; }}
        return Results.Ok(new {{ status = "connected", vault_accessible = true }});
    }}
    catch (Exception ex)
    {{
        return Results.Json(new {{ status = "error", detail = ex.Message }}, statusCode: 503);
    }}
}});
{storage_endpoint}
app.Run();
"""

    def _dotnet_csproj(self, spec: IntentSpec) -> str:
        storage_pkg = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_pkg = '    <PackageReference Include="Azure.Storage.Blobs" Version="12.19.0" />\n'
        cosmos_pkg = ""
        if DataStore.COSMOS_DB in spec.data_stores:
            cosmos_pkg = '    <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.37.0" />\n'

        return f"""<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Azure.Identity" Version="1.11.0" />
    <PackageReference Include="Azure.Security.KeyVault.Secrets" Version="4.6.0" />
{storage_pkg}{cosmos_pkg}  </ItemGroup>
</Project>
"""

    def _dotnet_dockerfile(self, spec: IntentSpec) -> str:
        return f"""# ===================================================================
# Dockerfile -- {spec.project_name} (.NET)
# Multi-stage build for minimal production image
# ===================================================================

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS builder
WORKDIR /build
COPY *.csproj ./
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /publish .
USER appuser
EXPOSE 8000
ENV ASPNETCORE_URLS=http://+:8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["dotnet", "{spec.project_name}.dll"]
"""

    def _dotnet_appsettings(self, spec: IntentSpec) -> str:
        import json as _json

        settings: dict = {
            "Logging": {"LogLevel": {"Default": "Information", "Microsoft.AspNetCore": "Warning"}},
            "ENVIRONMENT": spec.environment,
            "KEY_VAULT_NAME": "",
        }
        if DataStore.BLOB_STORAGE in spec.data_stores:
            settings["STORAGE_ACCOUNT_URL"] = ""
        return _json.dumps(settings, indent=2) + "\n"
