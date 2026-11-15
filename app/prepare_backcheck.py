"""Обновить тестовые email в contract.json перед повторным запуском backcheck.

Команда: python -m app.prepare_backcheck
Существующие записи в БД не затрагиваются.
"""

import json
from pathlib import Path
from uuid import uuid4


def main() -> None:
    contract_path = Path(__file__).resolve().parent.parent / "contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    # Уникальные адреса не конфликтуют ни с сидами, ни с предыдущими
    # проверками. Первому и второму сотруднику нужны *разные* email.
    suffix = uuid4().hex
    contract["child"]["create"]["email"] = f"bc-child-first-{suffix}@example.test"
    contract["child"]["create_other"]["email"] = f"bc-child-second-{suffix}@example.test"

    # Правило ★★ по-прежнему должно вернуть 409: адрес повторяется,
    # отличие только в регистре символов.
    rule_email = f"bc-rule-{suffix}@example.test"
    contract["rule"]["setup"][0]["body"]["email"] = rule_email
    contract["rule"]["violate"]["body"]["email"] = rule_email.upper()

    contract_path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Тестовые email в contract.json обновлены. База данных не изменялась.")


if __name__ == "__main__":
    main()
