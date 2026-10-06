# Contract stage

`python scripts/ci_contract.py` поднимает эталонный мок и гоняет:
static -> idor -> runtime_p0..p4 -> e2e -> out_of_band.

Переменные:
- `CPOT_STRICT=1` — отсутствие openapi.yaml валит стадию (для main).
- `CPOT_MOCK_LEAKY=1` — проверка чувствительности: снять object-level authz.
- `CPOT_PORT` — порт мока (по умолчанию 52868, с фолбэком).
- `CPOT_BASE_URL` — гонять наборы против живого стенда вместо мока.
