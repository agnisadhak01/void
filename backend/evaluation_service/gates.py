"""Evaluation gate policy for agent completion."""


def eval_passed(eval_result: dict | None, *, admin_override: bool = False) -> bool:
    if admin_override:
        return True
    if not eval_result:
        return False
    return bool(eval_result.get("passed"))
