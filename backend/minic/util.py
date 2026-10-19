"""Small string utilities shared by the semantic analyzer and the repair engine."""
from __future__ import annotations


def edit_distance(a: str, b: str) -> int:
    """Optimal-string-alignment (Damerau-Levenshtein) distance: insert, delete,
    substitute and adjacent transposition each cost 1."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if not la:
        return lb
    if not lb:
        return la
    d = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = i
    for j in range(lb + 1):
        d[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[la][lb]


def similarity(a: str, b: str) -> float:
    """1.0 for identical strings, 0.0 for completely different ones."""
    m = max(len(a), len(b)) or 1
    return max(0.0, 1.0 - edit_distance(a, b) / m)
