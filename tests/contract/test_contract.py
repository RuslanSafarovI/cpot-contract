import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

def test_contract_stage():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "ci_contract.py")],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
