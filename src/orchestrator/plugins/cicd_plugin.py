"""CI/CD Plugins -- additional GitHub Actions pipeline stages.

Each plugin generates a snippet of GitHub Actions YAML that can be
inserted into the generated CI/CD workflows (load testing, canary
deployment, smoke tests, etc.).
"""

from __future__ import annotations

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


class LoadTestStagePlugin:
    """Generates a GitHub Actions job for Azure Load Testing."""

    def applies_to(self, spec: IntentSpec) -> bool:
        keywords = {"load test", "performance", "stress test", "scale", "benchmark"}
        return any(kw in spec.raw_intent.lower() for kw in keywords)

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        return {
            ".github/workflows/load-test.yml": f"""\
name: Load Test
on:
  workflow_dispatch:
    inputs:
      target_url:
        description: 'Target URL for load testing'
        required: true
      duration:
        description: 'Test duration (e.g. 5m, 30m)'
        required: false
        default: '5m'
      concurrent_users:
        description: 'Number of concurrent virtual users'
        required: false
        default: '50'

permissions:
  id-token: write
  contents: read

jobs:
  load-test:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{{{ secrets.AZURE_CLIENT_ID }}}}
          tenant-id: ${{{{ secrets.AZURE_TENANT_ID }}}}
          subscription-id: ${{{{ secrets.AZURE_SUBSCRIPTION_ID }}}}

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \\
            --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D68
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \\
            | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update && sudo apt-get install k6

      - name: Run load test
        run: |
          k6 run \\
            --vus ${{{{ github.event.inputs.concurrent_users }}}} \\
            --duration ${{{{ github.event.inputs.duration }}}} \\
            --out json=results.json \\
            tests/load/load-test.js
        env:
          TARGET_URL: ${{{{ github.event.inputs.target_url }}}}

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: load-test-results
          path: results.json
""",
            f"tests/load/load-test.js": f"""\
import http from 'k6/http';
import {{ check, sleep }} from 'k6';

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

export const options = {{
  thresholds: {{
    http_req_duration: ['p(95)<500', 'p(99)<1500'],
    http_req_failed: ['rate<0.01'],
  }},
}};

export default function () {{
  // Health check
  const health = http.get(`${{BASE_URL}}/health`);
  check(health, {{
    'health status 200': (r) => r.status === 200,
    'health response < 200ms': (r) => r.timings.duration < 200,
  }});

  sleep(1);
}}
""",
        }


class CanaryDeployStagePlugin:
    """Generates a canary deployment workflow with traffic shifting."""

    def applies_to(self, spec: IntentSpec) -> bool:
        envs = spec.cicd.environments if spec.cicd else []
        return len(envs) >= 2 or "canary" in spec.raw_intent.lower()

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        return {
            ".github/workflows/canary-deploy.yml": f"""\
name: Canary Deployment
on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Container image tag to deploy'
        required: true
      canary_weight:
        description: 'Initial traffic percentage for canary (0-100)'
        required: false
        default: '10'

permissions:
  id-token: write
  contents: read

env:
  RESOURCE_GROUP: rg-{spec.project_name}-${{{{ vars.ENVIRONMENT }}}}
  APP_NAME: ca-{spec.project_name}

jobs:
  canary-deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{{{ secrets.AZURE_CLIENT_ID }}}}
          tenant-id: ${{{{ secrets.AZURE_TENANT_ID }}}}
          subscription-id: ${{{{ secrets.AZURE_SUBSCRIPTION_ID }}}}

      - name: Deploy canary revision
        run: |
          az containerapp revision copy \\
            --name ${{{{ env.APP_NAME }}}} \\
            --resource-group ${{{{ env.RESOURCE_GROUP }}}} \\
            --image ${{{{ github.event.inputs.image_tag }}}} \\
            --revision-suffix canary-${{{{ github.run_number }}}}

      - name: Set canary traffic weight
        run: |
          LATEST=$(az containerapp revision list \\
            --name ${{{{ env.APP_NAME }}}} \\
            --resource-group ${{{{ env.RESOURCE_GROUP }}}} \\
            --query "[-1].name" -o tsv)
          az containerapp ingress traffic set \\
            --name ${{{{ env.APP_NAME }}}} \\
            --resource-group ${{{{ env.RESOURCE_GROUP }}}} \\
            --revision-weight latest=${{{{ github.event.inputs.canary_weight }}}} \\
            --revision-weight $LATEST=$((100 - ${{{{ github.event.inputs.canary_weight }}}}))

      - name: Health check canary
        run: |
          FQDN=$(az containerapp show \\
            --name ${{{{ env.APP_NAME }}}} \\
            --resource-group ${{{{ env.RESOURCE_GROUP }}}} \\
            --query "properties.configuration.ingress.fqdn" -o tsv)
          for i in $(seq 1 10); do
            STATUS=$(curl -s -o /dev/null -w "%{{http_code}}" "https://$FQDN/health")
            if [ "$STATUS" = "200" ]; then echo "Health check passed"; exit 0; fi
            sleep 5
          done
          echo "Health check failed" && exit 1
""",
        }


class SmokeTestStagePlugin:
    """Generates a post-deployment smoke test workflow."""

    def applies_to(self, spec: IntentSpec) -> bool:
        return True  # Always useful after any deployment

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        entity_checks = ""
        for entity in spec.entities[:3]:
            entity_checks += f"""
      - name: Smoke test -- {entity.name} API
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{{{{http_code}}}}" "${{{{{{ env.APP_URL }}}}}}/api/{entity.name}")
          if [ "$STATUS" != "200" ]; then echo "FAIL: /{entity.name} returned $STATUS"; exit 1; fi
          echo "PASS: /{entity.name} returned 200"
"""
        return {
            ".github/workflows/smoke-test.yml": f"""\
name: Smoke Tests
on:
  workflow_run:
    workflows: ["Deploy"]
    types: [completed]
  workflow_dispatch:
    inputs:
      app_url:
        description: 'Application URL to test'
        required: true

permissions:
  contents: read

env:
  APP_URL: ${{{{ github.event.inputs.app_url || vars.APP_URL }}}}

jobs:
  smoke:
    runs-on: ubuntu-latest
    if: ${{{{ github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success' }}}}
    steps:
      - name: Health endpoint
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{{{{http_code}}}}" "${{{{{{ env.APP_URL }}}}}}/health")
          if [ "$STATUS" != "200" ]; then echo "FAIL: /health returned $STATUS"; exit 1; fi
          echo "PASS: /health returned 200"

      - name: Readiness endpoint
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{{{{http_code}}}}" "${{{{{{ env.APP_URL }}}}}}/health/ready")
          if [ "$STATUS" != "200" ]; then echo "FAIL: /health/ready returned $STATUS"; exit 1; fi
          echo "PASS: /health/ready returned 200"
{entity_checks}
      - name: Summary
        if: always()
        run: echo "Smoke tests completed"
""",
        }
