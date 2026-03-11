"""Run full test suite and write results to file."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line", "--no-header", "-p", "no:warnings"],
    capture_output=True,
    text=True,
    timeout=120,
    cwd=r"c:\Users\okofoworola\GitHub Copilot SDK Enterprise Challenge"
)
output = result.stdout + result.stderr
with open("test_fresh.txt", "w") as f:
    f.write(output)
lines = output.strip().split("\n")
for line in lines[-25:]:
    print(line)
print(f"\nEXIT CODE: {result.returncode}")
