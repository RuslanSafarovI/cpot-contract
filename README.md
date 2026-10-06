# ЦПОТ — контрактный комплект (Contract v1.1 + P3)

Машинные артефакты: OpenAPI 3.1, схемы, эталонный мок, наборы проверок P0–P4,
IDOR-матрица, внеполосные тесты, CI.

## Быстрый старт
```bash
pip install pyyaml pytest
python scripts/ci_contract.py   # стадия Contract целиком
pytest -q                       # через pytest
```

## Что покрыто
- P0 core, P1 analysis/requests/packages, P2 auth/users/rules/audit, P3 workplaces/hazards/sout/ppe
- IDOR: 66 проб (attack A->B = 404, control A->A != 404)
- Out-of-band: signed URL scope, AI/OCR context, outbox envelope

## Документы
- `docs/security/idor_matrix.md` — выгрузка проб
- `docs/security/coverage_reconciliation.md` — сверка со стресс-тестом v0.3 (54 SEC)
- `docs/api/policy_decisions.yaml` — SEC-38/41/52 (решения, не тесты)

## Оговорка
Мок — эталон поведения (БД в памяти), а не реализация. Против живого стенда:
`CPOT_BASE_URL=https://... python scripts/ci_contract.py`.
