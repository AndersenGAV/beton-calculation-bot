import re


def format_concrete_short_label(full_label: str) -> str:
    """Return a short concrete label with only B..., P... and optional (M...)."""
    text = " ".join(str(full_label).strip().split())
    if not text:
        return ""

    m_match = re.search(r"\((M[^)]*)\)", text, flags=re.IGNORECASE)
    m_value = m_match.group(1).strip() if m_match else None

    parts: list[str] = []

    for raw_part in re.split(r"\s*,\s*", text):
        part = raw_part.strip()
        if not part:
            continue

        upper_part = part.upper()

        if upper_part.startswith("B"):
            parts.append(part)
        elif upper_part.startswith("P"):
            parts.append(part)

    if parts:
        prefix = ", ".join(parts)
        if m_value:
            return f"{prefix} ({m_value})"
        return prefix

    if m_value:
        return f"({m_value})"

    return text