.PHONY: contract idor clean

contract:
	python scripts/ci_contract.py

idor:
	python scripts/idor_matrix.py

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
