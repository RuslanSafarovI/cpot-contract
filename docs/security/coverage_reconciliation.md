# Сверка стресс-теста v0.3 с набором проверок

Источник: `ЦПОТ_Третий_архитектурный_Stress_Test_v0.3.xlsx` (54 сценария SEC).

| Статус | Кол-во | Доля |
|---|---|---|
| covered | 46 | 85.2% |
| partial | 4 | 7.4% |
| policy | 3 | 5.6% |
| open | 1 | 1.9% |

## По сценариям

| SEC | Статус | Где проверяется |
|---|---|---|
| SEC-01 | covered | runtime_p0.py |
| SEC-02 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-03 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-04 | covered | runtime_p0.py |
| SEC-05 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-06 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-07 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-08 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-09 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-10 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-11 | covered | runtime_p0.py |
| SEC-12 | covered | runtime_p0.py |
| SEC-13 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-14 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-15 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-16 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-17 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-18 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-19 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-20 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-21 | covered | runtime_p1.py |
| SEC-22 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-23 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-24 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-25 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-26 | partial | частично: см. открытые пункты ниже |
| SEC-27 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-28 | covered | runtime_p1.py |
| SEC-29 | partial | частично: см. открытые пункты ниже |
| SEC-30 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-31 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-32 | covered | runtime_p4.py |
| SEC-33 | covered | runtime_p4.py |
| SEC-34 | covered | runtime_p4.py |
| SEC-35 | covered | runtime_p4.py |
| SEC-36 | covered | runtime_p4.py |
| SEC-37 | covered | runtime_p4.py |
| SEC-38 | policy | policy_decisions.yaml (решение не выбрано) |
| SEC-39 | covered | out_of_band.py |
| SEC-40 | partial | частично: см. открытые пункты ниже |
| SEC-41 | policy | policy_decisions.yaml (решение не выбрано) |
| SEC-42 | covered | out_of_band.py |
| SEC-43 | covered | runtime_p4.py |
| SEC-44 | covered | runtime_p1.py |
| SEC-45 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-46 | covered | runtime_p1.py |
| SEC-47 | covered | runtime_p4.py |
| SEC-48 | covered | out_of_band.py |
| SEC-49 | covered | out_of_band.py |
| SEC-50 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-51 | covered | idor_matrix.py (attack A->B = 404, control A->A != 404) |
| SEC-52 | policy | policy_decisions.yaml (решение не выбрано) |
| SEC-53 | partial | частично: см. открытые пункты ниже |
| SEC-54 | open | не заложено |

## Findings

| ID | Уровень | Статус |
|---|---|---|
| F-01 | Критический | закрыт — idor_matrix.py, 66 проб |
| F-02 | Критический | закрыт — проверка ссылок в теле (runtime_p4) |
| F-03 | Высокий | решение — policy_decisions.yaml (SEC-38) |
| F-04 | Высокий | частично — executor scope в runtime_p1/p2 |
| F-05 | Высокий | закрыт — out_of_band.py (AI context) |
| F-06 | Высокий | закрыт — out_of_band.py (outbox envelope) |
| F-07 | Средний | закрыт — runtime_p2 (audit tenant scope) |
| F-08 | Средний | открыт — restore ACL regression не заложен |
