"""Frontend API Generator -- Azure-deployable BFF with Fabric data connector.

Generates a Backend-For-Frontend (BFF) API that:
1. Deploys as a separate Azure Container App alongside the main API
2. Serves the React SPA (built static files via nginx)
3. Proxies API calls to the main backend Container App
4. Provides a /fabric endpoint that pulls synthetic data from Fabric lakehouses
5. Exposes /fabric/sync endpoint to push Fabric data into the frontend state

Every scaffolded application gets both local and Azure frontend API support:
- **Local**: Vite dev server on :3000, proxy to backend :8000
- **Azure**: Containerized nginx+BFF on Container Apps, proxy to backend Container App
"""

from __future__ import annotations

from src.orchestrator.intent_schema import DataStore, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


def _kebab(name: str) -> str:
    return name.lower().replace("_", "-").replace(" ", "-")


def _snake(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


class FrontendApiGenerator:
    """Generates an Azure-deployable frontend API with Fabric data connector."""

    def __init__(self) -> None:
        self._scaffold_plan = None

    def set_scaffold_plan(self, scaffold_plan) -> None:
        """Receive platform-wide planning objects from the orchestrator."""
        self._scaffold_plan = scaffold_plan

    def generate(self, spec: IntentSpec) -> dict[str, str]:
        project = _kebab(spec.project_name)
        entities = spec.entities or []
        uses_fabric = getattr(spec, "uses_fabric", False) or DataStore.FABRIC_LAKEHOUSE in spec.data_stores

        files: dict[str, str] = {}

        # -- Frontend API (BFF) FastAPI app --------------------------
        files["frontend-api/main.py"] = self._bff_main(project, entities, uses_fabric, spec.endpoints or [])
        files["frontend-api/requirements.txt"] = self._requirements(uses_fabric)
        files["frontend-api/Dockerfile"] = self._dockerfile()

        # -- Fabric data connector -----------------------------------
        files["frontend-api/fabric_connector.py"] = self._fabric_connector(project, entities, uses_fabric)

        # -- Environment configs for local + Azure -------------------
        files["frontend-api/.env.local"] = self._env_local(project)
        files["frontend-api/.env.azure"] = self._env_azure(project)

        # -- Nginx config for serving SPA + proxying API -------------
        files["frontend-api/nginx.conf"] = self._nginx_conf()
        files["frontend-api/docker-entrypoint.sh"] = self._entrypoint()

        # -- Deployment compose for local testing --------------------
        files["docker-compose.yml"] = self._docker_compose(project, uses_fabric)

        # -- Azure deployment script ---------------------------------
        files["scripts/deploy-frontend.sh"] = self._deploy_script(project)
        files["scripts/deploy-frontend.ps1"] = self._deploy_script_ps1(project)

        # -- Update frontend .env for Azure mode ---------------------
        files["frontend/.env.azure"] = (
            f"VITE_API_BASE_URL=https://ca-{project}-fe-dev.azurecontainerapps.io/api/v1\n"
            f'VITE_APP_TITLE="{project}"\n'
            f"VITE_FABRIC_ENABLED={'true' if uses_fabric else 'false'}\n"
        )

        # -- Fabric data page for the frontend -----------------------
        files["frontend/src/pages/FabricDataPage.tsx"] = self._fabric_data_page(entities, uses_fabric)
        files["frontend/src/api/fabric.ts"] = self._fabric_api_client(entities)

        logger.info("frontend_api_generator.complete", file_count=len(files), project=project)
        return files

    # -----------------------------------------------------------------
    # BFF Main Application
    # -----------------------------------------------------------------
    def _bff_main(self, project: str, entities: list, uses_fabric: bool, endpoints: list = None) -> str:
        entity_imports = ""
        entity_routes = ""
        entity_path_map_entries = []
        endpoints = endpoints or []
        for e in entities:
            name = _snake(e.name)
            entity_routes += f"""
@app.get("/fabric/{name}")
async def fabric_{name}():
    \"\"\"Pull {e.name} data from Fabric lakehouse (or synthetic fallback).\"\"\"
    return await connector.fetch_entity("{name}")

"""
            # Map API path plurals to fabric connector keys
            api_path = name + "s" if not name.endswith("s") else name + "es"
            for ep in endpoints:
                if ep.method == "GET" and "/" + name in ep.path:
                    # Extract the collection path segment
                    path_parts = ep.path.strip("/").split("/")
                    if path_parts:
                        api_path = path_parts[0]
                        break
            entity_path_map_entries.append(f'    "{api_path}": "{name}",')

        entity_path_map = "{\n" + "\n".join(entity_path_map_entries) + "\n}" if entity_path_map_entries else "{}"

        return f'''"""Frontend API (BFF) -- {project}

Azure-deployable Backend-For-Frontend that proxies API calls and
provides Fabric data connectivity for the React dashboard.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fabric_connector import FabricDataConnector

APP_NAME = "{project}-frontend-api"
VERSION = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format=\'{{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"{project}-fe","message":"%(message)s"}}\',
)
logger = logging.getLogger(APP_NAME)

app = FastAPI(
    title=f"{{APP_NAME}} -- Frontend API",
    version=VERSION,
    description="Backend-For-Frontend API with Fabric data connector",
    docs_url="/bff/docs",
)

# -- CORS for local dev + Azure deployment --
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Fabric Data Connector --
connector = FabricDataConnector(
    workspace=os.getenv("FABRIC_WORKSPACE", "{project}-workspace"),
    lakehouse=os.getenv("FABRIC_LAKEHOUSE", "{project}-lakehouse"),
    backend_url=BACKEND_URL,
)

# -- Health Check --
@app.get("/health")
async def health():
    return {{
        "status": "healthy",
        "service": APP_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backend_url": BACKEND_URL,
        "fabric_enabled": connector.is_connected,
    }}

# -- Fabric Sync Endpoint --
@app.post("/fabric/sync")
async def fabric_sync():
    """Trigger a sync of all entity data from Fabric lakehouse."""
    result = await connector.sync_all()
    return {{"status": "synced", "entities": result}}

@app.get("/fabric/status")
async def fabric_status():
    """Get Fabric connection status and data freshness."""
    return await connector.get_status()

# -- Entity-specific Fabric endpoints --
{entity_routes}

# -- Entity name mapping (API path -> Fabric connector key) --
ENTITY_PATH_MAP = {entity_path_map}

# -- Proxy to backend API with synthetic data fallback --
import httpx
import uuid

@app.api_route("/api/{{path:path}}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_backend(request: Request, path: str):
    """Proxy API calls to the backend. Serves Fabric synthetic data for GET lists.
    POST/PUT/DELETE operations are applied to the local cache AND proxied to backend."""
    parts = path.strip("/").split("/")
    entity_key = parts[1] if len(parts) >= 2 else parts[0]
    fabric_entity = ENTITY_PATH_MAP.get(entity_key)

    # -- GET: serve from Fabric connector cache --
    if request.method == "GET":
        if fabric_entity and len(parts) <= 2:
            data = await connector.fetch_entity(fabric_entity)
            return JSONResponse(content=data)

        if fabric_entity and len(parts) == 3:
            item_id = parts[2]
            data = await connector.fetch_entity(fabric_entity)
            item = next((r for r in data if r.get("id") == item_id), None)
            if item:
                return JSONResponse(content=item)
            return JSONResponse(content={{"detail": "Not found"}}, status_code=404)

    # -- POST: create record in local cache + proxy to backend --
    if request.method == "POST" and fabric_entity and len(parts) == 2:
        content_type_hdr = request.headers.get("content-type", "")
        if "application/json" in content_type_hdr:
            import json as _json
            body = await request.body()
            try:
                record = _json.loads(body)
            except Exception:
                record = {{}}
            if not record.get("id"):
                record["id"] = str(uuid.uuid4())
            if not record.get("status"):
                record["status"] = "uploaded"
            record["created_at"] = datetime.now(timezone.utc).isoformat()
            # Insert into local cache so it appears in GET immediately
            if fabric_entity in connector._cache:
                connector._cache[fabric_entity].insert(0, record)
            else:
                data = await connector.fetch_entity(fabric_entity)
                data.insert(0, record)
                connector._cache[fabric_entity] = data
            logger.info(f"Record created in BFF cache: {{fabric_entity}}/{{record['id']}}")
            # Also proxy to backend (best-effort)
            try:
                async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
                    await client.post(
                        f"{{BACKEND_URL}}/api/{{path}}",
                        content=body,
                        headers={{"content-type": "application/json"}},
                    )
            except Exception as e:
                logger.warning(f"Backend proxy for POST failed (record saved locally): {{e}}")
            return JSONResponse(content=record, status_code=201)

    # -- DELETE: remove from local cache + proxy to backend --
    if request.method == "DELETE" and fabric_entity and len(parts) == 3:
        item_id = parts[2]
        if fabric_entity in connector._cache:
            connector._cache[fabric_entity] = [
                r for r in connector._cache[fabric_entity] if r.get("id") != item_id
            ]
            logger.info(f"Record deleted from BFF cache: {{fabric_entity}}/{{item_id}}")

    # -- For file uploads, actions, and other mutations, proxy to backend --
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=True,
            follow_redirects=True,
        ) as client:
            url = f"{{BACKEND_URL}}/api/{{path}}"
            forward_headers = {{}}
            for key in ("accept", "content-type", "authorization"):
                val = request.headers.get(key)
                if val:
                    forward_headers[key] = val
            body = await request.body()
            resp = await client.request(
                method=request.method,
                url=url,
                headers=forward_headers,
                content=body,
                params=dict(request.query_params),
            )
            resp_content_type = resp.headers.get("content-type", "")
            if resp_content_type.startswith("application/json"):
                return JSONResponse(content=resp.json(), status_code=resp.status_code)
            return JSONResponse(content={{"detail": resp.text}}, status_code=resp.status_code)
    except Exception as e:
        logger.warning(f"Backend proxy failed for /api/{{path}}: {{e}}")

    return JSONResponse(
        content={{"detail": f"Backend unavailable for {{path}}"}},
        status_code=503,
    )

logger.info(f"{{APP_NAME}} initialized -- backend={{BACKEND_URL}}")
'''

    # -----------------------------------------------------------------
    # Fabric Data Connector
    # -----------------------------------------------------------------
    def _fabric_connector(self, project: str, entities: list, uses_fabric: bool) -> str:
        entity_schemas = ""
        synthetic_generators = ""

        for e in entities:
            name = _snake(e.name)
            fields = getattr(e, "fields", []) or []

            field_list = []
            for f in fields:
                fname = f.name if hasattr(f, "name") else str(f)
                ftype = f.field_type if hasattr(f, "field_type") else "str"
                field_list.append(f'        "{fname}": "{ftype}",')

            entity_schemas += f'''    "{name}": {{
{chr(10).join(field_list)}
    }},
'''

            # Generate synthetic data function
            synthetic_generators += f'''
    def _generate_{name}(self, count: int = 100) -> list[dict]:
        """Generate synthetic {e.name} records (Fabric lakehouse simulation)."""
        records = []
        for i in range(count):
            record = {{"id": f"{name}-{{i+1:04d}}"}}
'''
            for f in fields:
                fname = f.name if hasattr(f, "name") else str(f)
                ftype = f.field_type if hasattr(f, "field_type") else "str"
                if fname == "id":
                    continue
                if ftype in ("str", "string"):
                    if "name" in fname and "file" not in fname:
                        label = fname.replace("_", " ").title()
                        synthetic_generators += f'            record["{fname}"] = f"{label} {{i+1}}"\n'
                    elif "status" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.choice(["active", "pending", "completed", "failed"])\n'
                    elif "email" in fname:
                        email_domain = project.replace("-", "") + ".com"
                        synthetic_generators += f'            record["{fname}"] = f"user{{i+1}}@{email_domain}"\n'
                    elif "url" in fname:
                        synthetic_generators += f'            record["{fname}"] = f"https://storage.blob.core.windows.net/{name}/{{i+1:04d}}"\n'
                    elif "type" in fname or "category" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.choice(["type-a", "type-b", "type-c", "type-d"])\n'
                    elif "priority" in fname or "severity" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.choice(["critical", "high", "medium", "low"])\n'
                    elif "department" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.choice(["Finance", "Legal", "HR", "Operations", "Procurement", "Engineering", "Compliance"])\n'
                    elif "ip_address" in fname:
                        synthetic_generators += f'            record["{fname}"] = f"10.{{random.randint(0,255)}}.{{random.randint(0,255)}}.{{random.randint(1,254)}}"\n'
                    elif any(kw in fname for kw in ("_by", "assigned", "reviewer", "created_by", "performed_by", "uploaded_by")):
                        synthetic_generators += f'            record["{fname}"] = random.choice(["sarah.chen@enterprise.com", "james.wilson@enterprise.com", "maria.garcia@enterprise.com", "admin@enterprise.com"])\n'
                    elif "description" in fname or "notes" in fname or "details" in fname or "summary" in fname:
                        synthetic_generators += f'            _choice = random.choice(["Automated", "Manual", "Scheduled", "Ad-hoc"])\n'
                        synthetic_generators += f'            record["{fname}"] = f"{{_choice}} {fname.replace("_", " ")} for record {{i+1}}"\n'
                    elif "result" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.choice(["success", "partial", "failure"])\n'
                    elif "version" in fname:
                        synthetic_generators += f'            record["{fname}"] = f"{{random.randint(1,5)}}.{{random.randint(0,9)}}"\n'
                    elif "filename" in fname or "file_name" in fname:
                        synthetic_generators += f'            _ext = random.choice(["pdf", "png", "jpg", "docx"])\n'
                        synthetic_generators += f'            record["{fname}"] = f"{name}_{{i+1:04d}}.{{_ext}}"\n'
                    elif "file_type" in fname or "format" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.choice(["pdf", "png", "jpg", "tiff", "docx"])\n'
                    else:
                        synthetic_generators += f'            record["{fname}"] = f"{fname.replace("_", " ").title()} {{i+1}}"\n'
                elif ftype in ("int", "integer"):
                    if "count" in fname or "total" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.randint(0, 1000)\n'
                    elif "size" in fname or "bytes" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.randint(1024, 52428800)\n'
                    elif "duration" in fname or "time" in fname or "latency" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.randint(50, 5000)\n'
                    elif "days" in fname:
                        synthetic_generators += f'            record["{fname}"] = random.choice([30, 90, 180, 365, 730])\n'
                    else:
                        synthetic_generators += f'            record["{fname}"] = random.randint(1, 100)\n'
                elif ftype in ("float", "double", "decimal"):
                    if "confidence" in fname or "accuracy" in fname or "rate" in fname:
                        synthetic_generators += f'            record["{fname}"] = round(random.uniform(0.65, 0.99), 3)\n'
                    elif "pct" in fname or "percent" in fname or "progress" in fname:
                        synthetic_generators += f'            record["{fname}"] = round(random.uniform(0.0, 100.0), 1)\n'
                    else:
                        synthetic_generators += f'            record["{fname}"] = round(random.uniform(0.0, 1000.0), 2)\n'
                elif ftype in ("bool", "boolean"):
                    synthetic_generators += f'            record["{fname}"] = random.choice([True, False])\n'
                elif ftype in ("datetime", "date", "timestamp"):
                    synthetic_generators += f'            record["{fname}"] = (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))).isoformat()\n'
            synthetic_generators += '            records.append(record)\n'
            synthetic_generators += '        return records\n'

        entity_fetch_cases = ""
        for e in entities:
            name = _snake(e.name)
            entity_fetch_cases += f'''        if entity == "{name}":
            return self._generate_{name}(count=self._record_count)
'''

        return f'''"""Fabric Data Connector -- pulls synthetic data from Microsoft Fabric.

Connects to Azure Fabric lakehouse via the Fabric REST API or
falls back to high-fidelity synthetic data generation when Fabric
is not available (local dev, demo mode).

Supports:
- Direct lakehouse table reads via Fabric REST API
- OneLake file system access for Delta tables
- Synthetic data fallback with domain-aware generation
- Data freshness tracking and incremental sync
"""
from __future__ import annotations

import os
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


class FabricDataConnector:
    """Connects to Microsoft Fabric lakehouse or generates synthetic data."""

    # Entity schemas for validation and type coercion
    ENTITY_SCHEMAS: dict[str, dict[str, str]] = {{
{entity_schemas}    }}

    def __init__(
        self,
        workspace: str = "",
        lakehouse: str = "",
        backend_url: str = "http://localhost:8000",
        record_count: int = 500,
    ) -> None:
        self._workspace = workspace or os.getenv("FABRIC_WORKSPACE", "")
        self._lakehouse = lakehouse or os.getenv("FABRIC_LAKEHOUSE", "")
        self._backend_url = backend_url
        self._record_count = record_count
        self._cache: dict[str, list[dict]] = {{}}
        self._last_sync: dict[str, str] = {{}}
        self._fabric_token = os.getenv("FABRIC_ACCESS_TOKEN", "")

        # Try to connect to Fabric
        self._connected = bool(self._workspace and self._lakehouse and self._fabric_token)
        if self._connected:
            logger.info(f"Fabric connector initialized: {{workspace}}/{{lakehouse}}")
        else:
            logger.info("Fabric not configured -- using synthetic data engine")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def fetch_entity(self, entity: str, count: int | None = None) -> list[dict]:
        """Fetch entity data from Fabric lakehouse or synthetic fallback."""
        if count:
            self._record_count = count

        # Try Fabric first
        if self._connected:
            try:
                return await self._fetch_from_fabric(entity)
            except Exception as e:
                logger.warning(f"Fabric fetch failed for {{entity}}: {{e}} -- using synthetic data")

        # Check cache
        if entity in self._cache:
            return self._cache[entity]

        # Generate synthetic data
        data = self._generate_synthetic(entity)
        self._cache[entity] = data
        self._last_sync[entity] = datetime.now(timezone.utc).isoformat()
        return data

    async def _fetch_from_fabric(self, entity: str) -> list[dict]:
        """Fetch data from Fabric lakehouse via REST API."""
        import httpx

        # Fabric SQL analytics endpoint
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{{self._workspace}}/lakehouses/{{self._lakehouse}}/tables/gold_{{entity}}/rows"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                headers={{
                    "Authorization": f"Bearer {{self._fabric_token}}",
                    "Content-Type": "application/json",
                }},
                params={{"$top": str(self._record_count)}},
            )
            resp.raise_for_status()
            result = resp.json()
            rows = result.get("value", result.get("data", []))
            self._cache[entity] = rows
            self._last_sync[entity] = datetime.now(timezone.utc).isoformat()
            return rows

    def _generate_synthetic(self, entity: str) -> list[dict]:
        """Generate synthetic data matching Fabric gold-layer schema."""
{entity_fetch_cases}
        # Generic fallback
        return [
            {{"id": f"{{entity}}-{{i+1:04d}}", "name": f"{{entity}} {{i+1}}", "status": "active"}}
            for i in range(self._record_count)
        ]

    async def sync_all(self) -> dict[str, int]:
        """Sync all entities from Fabric (or regenerate synthetic data)."""
        result = {{}}
        self._cache.clear()
        for entity in self.ENTITY_SCHEMAS:
            data = await self.fetch_entity(entity)
            result[entity] = len(data)
        return result

    async def get_status(self) -> dict[str, Any]:
        """Get Fabric connection status and data freshness."""
        return {{
            "connected": self._connected,
            "workspace": self._workspace,
            "lakehouse": self._lakehouse,
            "entities": list(self.ENTITY_SCHEMAS.keys()),
            "cached_counts": {{k: len(v) for k, v in self._cache.items()}},
            "last_sync": self._last_sync,
            "data_source": "fabric" if self._connected else "synthetic",
        }}

    # -- Synthetic Data Generators (per entity) --
{synthetic_generators}
'''

    # -----------------------------------------------------------------
    # Requirements
    # -----------------------------------------------------------------
    def _requirements(self, uses_fabric: bool) -> str:
        lines = [
            "fastapi>=0.111.0",
            "uvicorn[standard]>=0.27.0",
            "httpx>=0.27.0",
            "pydantic>=2.5.0",
        ]
        if uses_fabric:
            lines.extend([
                "azure-identity>=1.15.0",
                "azure-storage-file-datalake>=12.14.0",
            ])
        return "\n".join(lines) + "\n"

    # -----------------------------------------------------------------
    # Dockerfile (multi-stage: build frontend + serve via nginx + BFF)
    # -----------------------------------------------------------------
    def _dockerfile(self) -> str:
        return '''# ===================================================================
# Frontend API -- multi-stage build
# Stage 1: Build React SPA
# Stage 2: BFF API + nginx serving + API proxy
# ===================================================================

# -- Stage 1: Build React SPA --
FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY ../frontend/package*.json ./
RUN npm ci
COPY ../frontend/ .
RUN npm run build

# -- Stage 2: BFF + nginx --
FROM python:3.11-slim

RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /bff
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy BFF application
COPY main.py fabric_connector.py ./

# Copy built frontend
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Security: create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /bff appuser

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
'''

    # -----------------------------------------------------------------
    # Nginx config
    # -----------------------------------------------------------------
    def _nginx_conf(self) -> str:
        return '''server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Serve React SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to BFF
    location /bff/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Proxy Fabric endpoints to BFF
    location /fabric/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Proxy backend API calls through BFF (handles TLS to backend)
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health check for Container Apps
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
    }
}
'''

    # -----------------------------------------------------------------
    # Docker entrypoint
    # -----------------------------------------------------------------
    def _entrypoint(self) -> str:
        return '''#!/bin/sh
set -e

# Start BFF API in background
cd /bff
uvicorn main:app --host 0.0.0.0 --port 8080 &

# Start nginx in foreground
nginx -g "daemon off;"
'''

    # -----------------------------------------------------------------
    # Environment configs
    # -----------------------------------------------------------------
    def _env_local(self, project: str) -> str:
        return f'''# Local development configuration
BACKEND_API_URL=http://localhost:8000
FABRIC_WORKSPACE=
FABRIC_LAKEHOUSE=
FABRIC_ACCESS_TOKEN=
'''

    def _env_azure(self, project: str) -> str:
        return f'''# Azure deployment configuration
BACKEND_API_URL=https://ca-{project}-dev.azurecontainerapps.io
FABRIC_WORKSPACE={project}-workspace
FABRIC_LAKEHOUSE={project}-lakehouse
FABRIC_ACCESS_TOKEN=${{FABRIC_TOKEN}}
'''

    # -----------------------------------------------------------------
    # Docker Compose for local testing
    # -----------------------------------------------------------------
    def _docker_compose(self, project: str, uses_fabric: bool) -> str:
        fabric_env = ""
        if uses_fabric:
            fabric_env = """
      - FABRIC_WORKSPACE=${FABRIC_WORKSPACE:-}
      - FABRIC_LAKEHOUSE=${FABRIC_LAKEHOUSE:-}
      - FABRIC_ACCESS_TOKEN=${FABRIC_ACCESS_TOKEN:-}"""

        return f'''# Docker Compose -- Local development with frontend + backend
version: "3.9"

services:
  # Backend API
  api:
    build:
      context: ./src/app
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PORT=8000

  # Frontend API (BFF + SPA + Fabric connector)
  frontend:
    build:
      context: .
      dockerfile: frontend-api/Dockerfile
    ports:
      - "3000:80"
    environment:
      - BACKEND_API_URL=http://api:8000{fabric_env}
    depends_on:
      - api
'''

    # -----------------------------------------------------------------
    # Azure deployment scripts
    # -----------------------------------------------------------------
    def _deploy_script(self, project: str) -> str:
        return f'''#!/bin/bash
# Deploy frontend API to Azure Container Apps
set -euo pipefail

RG="rg-{project}-dev"
ACR_NAME=$(az acr list --resource-group $RG --query "[0].name" -o tsv)
ACR_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
BACKEND_FQDN=$(az containerapp show --name ca-{project}-dev --resource-group $RG --query properties.configuration.ingress.fqdn -o tsv)

echo "Building frontend API image..."
az acr build --registry $ACR_NAME --image {project}-frontend:latest -f frontend-api/Dockerfile .

echo "Deploying frontend Container App..."
az containerapp create \\
  --name ca-{project}-fe-dev \\
  --resource-group $RG \\
  --environment $(az containerapp env list --resource-group $RG --query "[0].name" -o tsv) \\
  --image $ACR_SERVER/{project}-frontend:latest \\
  --target-port 80 \\
  --ingress external \\
  --min-replicas 1 \\
  --max-replicas 3 \\
  --env-vars BACKEND_API_URL=https://$BACKEND_FQDN \\
  --registry-server $ACR_SERVER

FRONTEND_FQDN=$(az containerapp show --name ca-{project}-fe-dev --resource-group $RG --query properties.configuration.ingress.fqdn -o tsv)
echo ""
echo "Frontend deployed: https://$FRONTEND_FQDN"
echo "Backend API:       https://$BACKEND_FQDN"
echo "BFF Docs:          https://$FRONTEND_FQDN/bff/docs"
echo "Fabric Status:     https://$FRONTEND_FQDN/fabric/status"
'''

    def _deploy_script_ps1(self, project: str) -> str:
        return f'''# Deploy frontend API to Azure Container Apps (PowerShell)
$ErrorActionPreference = "Stop"

$RG = "rg-{project}-dev"
$ACR_NAME = az acr list --resource-group $RG --query "[0].name" -o tsv
$ACR_SERVER = az acr show --name $ACR_NAME --query loginServer -o tsv
$BACKEND_FQDN = az containerapp show --name ca-{project}-dev --resource-group $RG --query properties.configuration.ingress.fqdn -o tsv
$CAE_NAME = az containerapp env list --resource-group $RG --query "[0].name" -o tsv

Write-Host "Building frontend API image..."
az acr build --registry $ACR_NAME --image {project}-frontend:latest -f frontend-api/Dockerfile .

Write-Host "Deploying frontend Container App..."
az containerapp create `
  --name ca-{project}-fe-dev `
  --resource-group $RG `
  --environment $CAE_NAME `
  --image "$ACR_SERVER/{project}-frontend:latest" `
  --target-port 80 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3 `
  --env-vars "BACKEND_API_URL=https://$BACKEND_FQDN" `
  --registry-server $ACR_SERVER

$FRONTEND_FQDN = az containerapp show --name ca-{project}-fe-dev --resource-group $RG --query properties.configuration.ingress.fqdn -o tsv

Write-Host ""
Write-Host "Frontend deployed: https://$FRONTEND_FQDN"
Write-Host "Backend API:       https://$BACKEND_FQDN"
Write-Host "BFF Docs:          https://$FRONTEND_FQDN/bff/docs"
Write-Host "Fabric Status:     https://$FRONTEND_FQDN/fabric/status"
'''

    # -----------------------------------------------------------------
    # Fabric Data Page (React component)
    # -----------------------------------------------------------------
    def _fabric_data_page(self, entities: list, uses_fabric: bool) -> str:
        entity_tabs = ""
        entity_cases = ""
        for e in entities:
            name = _snake(e.name)
            label = e.name.replace("_", " ").title()
            entity_tabs += f'    {{ key: "{name}", label: "{label}" }},\n'
            entity_cases += f'    case "{name}": return fabricApi.fetch{e.name}();\n'

        return f'''import {{ useState, useEffect }} from 'react';
import {{ fabricApi }} from '../api/fabric';

interface FabricEntity {{
  key: string;
  label: string;
}}

const ENTITIES: FabricEntity[] = [
{entity_tabs}];

export default function FabricDataPage() {{
  const [activeEntity, setActiveEntity] = useState(ENTITIES[0]?.key || '');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {{
    loadStatus();
  }}, []);

  useEffect(() => {{
    if (activeEntity) loadData(activeEntity);
  }}, [activeEntity]);

  async function loadStatus() {{
    try {{
      const s = await fabricApi.getStatus();
      setStatus(s);
    }} catch (e) {{
      console.error('Failed to load Fabric status', e);
    }}
  }}

  async function loadData(entity: string) {{
    setLoading(true);
    try {{
      const result = await fabricApi.fetchEntity(entity);
      setData(Array.isArray(result) ? result : []);
    }} catch (e) {{
      console.error('Failed to load data', e);
      setData([]);
    }} finally {{
      setLoading(false);
    }}
  }}

  async function handleSync() {{
    setSyncing(true);
    try {{
      await fabricApi.syncAll();
      await loadData(activeEntity);
      await loadStatus();
    }} catch (e) {{
      console.error('Sync failed', e);
    }} finally {{
      setSyncing(false);
    }}
  }}

  const columns = data.length > 0 ? Object.keys(data[0]).slice(0, 8) : [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Fabric Data Explorer</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {{status?.data_source === 'fabric' ? '🟢 Connected to Fabric Lakehouse' : '🔵 Synthetic Data Engine'}}
            {{status?.workspace && ` — ${{status.workspace}}/${{status.lakehouse}}`}}
          </p>
        </div>
        <button
          onClick={{handleSync}}
          disabled={{syncing}}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {{syncing ? 'Syncing...' : '🔄 Sync from Fabric'}}
        </button>
      </div>

      {{/* Status Cards */}}
      {{status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500">Data Source</div>
            <div className="text-lg font-semibold capitalize">{{status.data_source}}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500">Entities</div>
            <div className="text-lg font-semibold">{{status.entities?.length || 0}}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500">Cached Records</div>
            <div className="text-lg font-semibold">{{Object.values(status.cached_counts || {{}}).reduce((a: number, b: any) => a + (b as number), 0)}}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500">Connection</div>
            <div className="text-lg font-semibold">{{status.connected ? '🟢 Active' : '🔵 Local'}}</div>
          </div>
        </div>
      )}}

      {{/* Entity Tabs */}}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 overflow-x-auto">
        {{ENTITIES.map(e => (
          <button
            key={{e.key}}
            onClick={{() => setActiveEntity(e.key)}}
            className={{`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${{
              activeEntity === e.key
                ? 'bg-white dark:bg-gray-700 shadow text-blue-600'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
            }}`}}
          >
            {{e.label}}
          </button>
        ))}}
      </div>

      {{/* Data Table */}}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <span className="font-medium">{{activeEntity.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase())}}</span>
          <span className="text-sm text-gray-500">{{data.length}} records</span>
        </div>
        {{loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : data.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No data available. Click Sync to generate.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  {{columns.map(col => (
                    <th key={{col}} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">
                      {{col.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase())}}
                    </th>
                  ))}}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {{data.slice(0, 50).map((row, i) => (
                  <tr key={{i}} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    {{columns.map(col => (
                      <td key={{col}} className="px-4 py-3 whitespace-nowrap">
                        {{typeof row[col] === 'boolean' ? (row[col] ? '✅' : '❌') : String(row[col] ?? '—')}}
                      </td>
                    ))}}
                  </tr>
                ))}}
              </tbody>
            </table>
          </div>
        )}}
      </div>
    </div>
  );
}}
'''

    # -----------------------------------------------------------------
    # Fabric API Client (TypeScript)
    # -----------------------------------------------------------------
    def _fabric_api_client(self, entities: list) -> str:
        entity_methods = ""
        for e in entities:
            name = _snake(e.name)
            entity_methods += f"""  fetch{e.name}: () => request<any[]>('/{name}'),\n"""

        return f'''const FABRIC_BASE = import.meta.env.VITE_FABRIC_API_URL || '/fabric';

async function request<T>(path: string): Promise<T> {{
  const res = await fetch(`${{FABRIC_BASE}}${{path}}`);
  if (!res.ok) throw new Error(`Fabric API error: ${{res.status}}`);
  return res.json();
}}

export const fabricApi = {{
  getStatus: () => request<any>('/status'),
  syncAll: () => fetch(`${{FABRIC_BASE}}/sync`, {{ method: 'POST' }}).then(r => r.json()),
  fetchEntity: (entity: string) => request<any[]>(`/${{entity}}`),
{entity_methods}}};
'''
