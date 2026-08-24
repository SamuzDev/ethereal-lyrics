"""Minimal terminal UI that displays synced lyrics one word at a time,
centered on screen, using block character art."""

from __future__ import annotations

import os
import time
from typing import Any, Optional

from rich.console import Console
from rich.live import Live
from rich.text import Text

S = "\u2588"
_ = " "


def g(*rows: str) -> list[str]:
    return [r.ljust(6) for r in rows]


FONT: dict[str, list[str]] = {
    "A": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "B": g(
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588 ",
    ),
    "C": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "D": g(
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588 ",
    ),
    "E": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
    ),
    "F": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
    ),
    "G": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588    ",
        "\u2588\u2588 \u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "H": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "I": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
    ),
    "J": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "    \u2588\u2588",
        "    \u2588\u2588",
        "    \u2588\u2588",
        "    \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "K": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588 \u2588\u2588 ",
        "\u2588\u2588\u2588\u2588  ",
        "\u2588\u2588\u2588   ",
        "\u2588\u2588\u2588\u2588  ",
        "\u2588\u2588 \u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
    ),
    "L": g(
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
    ),
    "M": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "N": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588 \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588 \u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "O": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "P": g(
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
        "\u2588\u2588    ",
    ),
    "Q": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588 \u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588\u2588",
    ),
    "R": g(
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588 \u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "S": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588    ",
        " \u2588\u2588\u2588\u2588 ",
        "    \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "T": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
    ),
    "U": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "V": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
        " \u2588\u2588\u2588\u2588 ",
        "  \u2588\u2588  ",
    ),
    "W": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "X": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
        "  \u2588\u2588  ",
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "Y": g(
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
    ),
    "Z": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "    \u2588\u2588",
        "   \u2588\u2588 ",
        "  \u2588\u2588  ",
        " \u2588\u2588   ",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
    ),
    "0": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588 \u2588\u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588 \u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "1": g(
        "  \u2588\u2588  ",
        " \u2588\u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
    ),
    "2": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "    \u2588\u2588",
        "  \u2588\u2588\u2588 ",
        " \u2588\u2588   ",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
    ),
    "3": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "    \u2588\u2588",
        "  \u2588\u2588\u2588 ",
        "    \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "4": g(
        "   \u2588\u2588 ",
        "  \u2588\u2588\u2588 ",
        " \u2588\u2588 \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "   \u2588\u2588 ",
        "   \u2588\u2588 ",
    ),
    "5": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588 ",
        "    \u2588\u2588",
        "    \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "6": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588    ",
        "\u2588\u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "7": g(
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "    \u2588\u2588",
        "   \u2588\u2588 ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
    ),
    "8": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "9": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588\u2588",
        "    \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    " ": g(
        "      ",
        "      ",
        "      ",
        "      ",
        "      ",
        "      ",
        "      ",
    ),
    ".": g(
        "      ",
        "      ",
        "      ",
        "      ",
        "      ",
        " \u2588\u2588   ",
        " \u2588\u2588   ",
    ),
    ",": g(
        "      ",
        "      ",
        "      ",
        "      ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        " \u2588\u2588   ",
    ),
    "!": g(
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "      ",
        "  \u2588\u2588  ",
    ),
    "?": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "    \u2588\u2588",
        "   \u2588\u2588 ",
        "  \u2588\u2588  ",
        "      ",
        "  \u2588\u2588  ",
    ),
    ":": g(
        "      ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "      ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "      ",
    ),
    "-": g(
        "      ",
        "      ",
        "      ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "      ",
        "      ",
        "      ",
    ),
    "'": g(
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "      ",
        "      ",
        "      ",
        "      ",
    ),
    "á": g(
        "   \u2588\u2588 ",
        "  \u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "é": g(
        "    \u2588\u2588",
        "  \u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "í": g(
        "   \u2588\u2588 ",
        "  \u2588\u2588\u2588\u2588",
        "    \u2588\u2588",
        "  \u2588\u2588\u2588 ",
        "  \u2588\u2588  ",
        "  \u2588\u2588  ",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
    ),
    "ó": g(
        "   \u2588\u2588 ",
        "  \u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "ú": g(
        "   \u2588\u2588 ",
        "  \u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "ñ": g(
        " \u2588\u2588\u2588\u2588 ",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588\u2588 \u2588\u2588",
        "\u2588\u2588\u2588\u2588\u2588\u2588",
        "\u2588\u2588 \u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
    ),
    "ü": g(
        " \u2588\u2588 \u2588\u2588",
        "  \u2588\u2588\u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        "\u2588\u2588  \u2588\u2588",
        " \u2588\u2588\u2588\u2588 ",
    ),
    "ア": g("███ ", " █  ", " █  ", " █  ", " █  ", " █  ", "    "),  # ア
    "イ": g("█ █ ", "█ █ ", "█ █ ", " █  ", " █  ", "    ", "    "),  # イ
    "ウ": g("█   █", " █ █ ", "  █  ", "  █  ", " █ █ ", "█   █", "    "),  # ウ
    "エ": g("█████", "     ", "█████", "     ", "█████", "     ", "    "),  # エ
    "オ": g(" █ █ ", "█████", " █ █ ", "█   █", "█   █", "     ", "    "),  # オ
    "カ": g("    █", "████ ", "    █", "    █", "    █", "    █", "    "),  # カ
    "キ": g("█   █", " █ █ ", "  █  ", "  █  ", " █ █ ", "█   █", "    "),  # キ
    "ク": g("█    ", "█    ", "█    ", "█    ", "█████", "     ", "    "),  # ク
    "ケ": g("  █  ", "  █  ", "█████", "     ", "█████", "     ", "    "),  # ケ
    "コ": g("█  █ ", "████ ", "█  █ ", "████ ", "█  █ ", "     ", "    "),  # コ
    "サ": g("     ", "█  █ ", " ███ ", "  █  ", "█████", "     ", "    "),  # サ
    "シ": g("█  █ ", " ███ ", "  █  ", "█████", "     ", "     ", "    "),  # シ
    "ス": g("█   █", " ███ ", "█   █", "     ", "     ", "     ", "    "),  # ス
    "セ": g("  █  ", "█████", "  █  ", "  █  ", "█  █ ", "     ", "    "),  # セ
    "ソ": g("█   █", " █ ██", "  █ █", "     ", "     ", "     ", "    "),  # ソ
    "タ": g("█████", " █ █ ", "█████", "█   █", "     ", "     ", "    "),  # タ
    "チ": g("█████", " █   ", "█████", " █   ", " █   ", "     ", "    "),  # チ
    "ツ": g("█   █", "█ █ █", "█ █ █", " █ █ ", "     ", "     ", "    "),  # ツ
    "テ": g("█████", "  █  ", "█████", "  █  ", "  █  ", "     ", "    "),  # テ
    "ト": g("  █  ", " █ █ ", "█   █", "█   █", "     ", "     ", "    "),  # ト
    "ナ": g("  █  ", "█████", " █ █ ", "█   █", "█   █", "     ", "    "),  # ナ
    "ニ": g("█████", "     ", "     ", "     ", "█████", "     ", "    "),  # ニ
    "ノ": g("    █", "   █ ", "  █  ", " █   ", "█    ", "     ", "    "),  # ノ
    "ハ": g(" █ █ ", " █ █ ", " █ █ ", "█   █", "█   █", "     ", "    "),  # ハ
    "ヒ": g("█████", "    █", "    █", "    █", "    █", "     ", "    "),  # ヒ
    "フ": g("   █ ", "  █  ", " █   ", "█    ", "     ", "     ", "    "),  # フ
    "ヘ": g("█    ", " █   ", "  █  ", "   █ ", "    █", "     ", "    "),  # ヘ
    "ホ": g("█  █ ", "█████", "█  █ ", "█  █ ", "█  █ ", "     ", "    "),  # ホ
    "マ": g("█████", "   █ ", "  █  ", " █ █ ", "█   █", "     ", "    "),  # マ
    "ミ": g(" █ █ ", "█ █ █", "█ █ █", " █ █ ", "     ", "     ", "    "),  # ミ
    "ム": g("  █  ", " █ █ ", "█   █", "█   █", " █████", "     ", "    "),  # ム
    "メ": g("   █ ", "  █  ", " █   ", "█ █ █", "    █", "     ", "    "),  # メ
    "モ": g("█████", " █   ", "█████", " █   ", "█████", "     ", "    "),  # モ
    "ヤ": g("█   █", " █████", "     ", "█████", "     ", "     ", "    "),  # ヤ
    "ユ": g("█   █", "█   █", "█   █", " █████", "     ", "     ", "    "),  # ユ
    "ヨ": g("█████", " █   ", "█████", " █   ", "█████", "     ", "    "),  # ヨ
    "ラ": g("█████", "    █", "█████", "    █", "    █", "     ", "    "),  # ラ
    "リ": g("█   █", "█   █", "█   █", " █ █ ", " █ █ ", "     ", "    "),  # リ
    "ル": g("█  █ ", "█ █  ", "██   ", "█ █  ", "█  █ ", "     ", "    "),  # ル
    "レ": g("█   █", "█   █", " █ █ ", "  █  ", " █   ", "█    ", "    "),  # レ
    "ロ": g("█   █", "█   █", "█   █", "█   █", "█   █", "     ", "    "),  # ロ
    "ワ": g("█   █", "█   █", "█   █", "█   █", " █████", "     ", "    "),  # ワ
    "ヲ": g("█████", " █   ", "█████", " █   ", " █   ", "     ", "    "),  # ヲ
    "ン": g("█   █", "█  █ ", "█ █  ", "█    ", "     ", "     ", "    "),  # ン
    "ー": g("     ", "     ", "█████", "     ", "     ", "     ", "    "),  # ー
    "ッ": g("    █", "   █ ", "  █  ", " █   ", "     ", "     ", "    "),  # ッ
    "ヵ": g("    █", "████ ", "    █", "    █", "█████", "     ", "    "),  # ヵ
}


def render_big(text: str, max_width: int) -> list[str]:
    normalized = text.upper()
    for ch in "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00fc":
        normalized = normalized.replace(ch.upper(), ch)

    glyphs: list[list[str]] = []
    for ch in normalized:
        if ch in FONT:
            glyphs.append(FONT[ch])
        else:
            glyphs.append(FONT.get("?", FONT[" "]))

    if not glyphs:
        return [""] * 7

    raw_width = len(glyphs) * 6 + max(0, len(glyphs) - 1)
    if raw_width == 0:
        return [""] * 7

    if raw_width > max_width:
        count = max(1, (max_width + 1) // 7)
        glyphs = glyphs[:count]

    rows: list[str] = []
    for r in range(7):
        parts = []
        for g_idx, glyph in enumerate(glyphs):
            parts.append(glyph[r])
            if g_idx < len(glyphs) - 1:
                parts.append(" ")
        rows.append("".join(parts))
    return rows


class TerminalUI:
    def __init__(self, offset_ms: int = 0) -> None:
        self.console = Console()
        self._live: Optional[Live] = None
        self._prev_lyric_idx: int = -1
        self._word_index: int = 0
        self._word_change_time: float = time.monotonic()
        self._offset_ms = offset_ms

    def render(
        self,
        track: Any,
        lyrics: Any,
    ) -> None:
        if self._live is None:
            self._live = Live(
                self._build_frame(track, lyrics),
                console=self.console,
                refresh_per_second=10,
            )
            self._live.start()
        else:
            self._live.update(self._build_frame(track, lyrics))

    def stop(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        self.console.clear()

    def print_error(self, msg: str) -> None:
        pass

    def print_info(self, msg: str) -> None:
        pass

    def _get_current_lyric_index(
        self,
        lines: list[Any],
        progress_ms: int,
        is_synced: bool,
        lyrics: Any = None,
    ) -> int:
        if not lines:
            return -1

        if is_synced:
            # Get effective offset (static + dynamic)
            offset = self._offset_ms
            if lyrics and hasattr(lyrics, 'get_effective_offset'):
                offset = lyrics.get_effective_offset()

            # Use improved interpolation with offset
            adjusted = progress_ms - offset
            idx = -1
            for i, line in enumerate(lines):
                if line.start_ms is not None and line.start_ms <= adjusted:
                    idx = i
                elif line.start_ms is not None and line.start_ms > adjusted:
                    break
            return idx
        else:
            line_duration_ms = 5000
            idx = (progress_ms // line_duration_ms) % len(lines)
            return int(idx)

    def _get_interpolated_word_index(
        self,
        lines: list[Any],
        progress_ms: int,
        is_synced: bool,
        current_idx: int,
    ) -> int:
        """Get word index based on interpolation for smoother sync."""
        if not is_synced or current_idx < 0 or current_idx >= len(lines):
            return 0

        line = lines[current_idx]
        if not hasattr(line, '_word_positions') or not line._word_positions:
            return 0

        adjusted = progress_ms + self._offset_ms
        if line.start_ms is None or line.end_ms is None:
            return 0

        duration = line.end_ms - line.start_ms
        if duration <= 0:
            return 0

        elapsed = adjusted - line.start_ms
        ratio = max(0.0, min(1.0, elapsed / duration))

        # Map ratio to word index
        num_words = len(line._word_positions)
        if num_words == 0:
            return 0

        return min(int(ratio * num_words), num_words - 1)

    def _build_frame(
        self,
        track: Any,
        lyrics: Any,
    ) -> Text:
        text = Text()

        try:
            term_size = os.get_terminal_size()
            width = term_size.columns
            height = term_size.lines
        except (ValueError, OSError):
            width, height = 80, 24

        if lyrics is None or not lyrics:
            pad = (height - 7) // 2
            text.append("\n" * pad, style="bold white")
            text.append(" " * ((width - 3) // 2) + "...", style="bold white")
            text.append("\n" * (height - pad - 1), style="bold white")
            return text

        lines = lyrics.lines
        is_synced = lyrics.is_synced
        progress_ms = track.progress_ms

        idx = self._get_current_lyric_index(lines, progress_ms, is_synced, lyrics)

        if idx < 0 or idx >= len(lines):
            pad = (height - 7) // 2
            text.append("\n" * pad, style="bold white")
            text.append(" " * ((width - 3) // 2) + "...", style="bold white")
            text.append("\n" * (height - pad - 1), style="bold white")
            return text

        line_text = lines[idx].text

        if idx != self._prev_lyric_idx:
            self._prev_lyric_idx = idx
            self._word_index = 0
            self._word_change_time = time.monotonic()

        # Detect if text has spaces (romance languages) or not (Japanese, Chinese, etc.)
        has_spaces = " " in line_text
        if has_spaces:
            words = line_text.split()
        else:
            # For languages without spaces (Japanese, Chinese), split by character
            words = list(line_text)

        if len(words) > 1:
            # Calculate word duration based on time to next lyric line
            if is_synced and idx + 1 < len(lines) and lines[idx + 1].start_ms is not None:
                line_duration = lines[idx + 1].start_ms - lines[idx].start_ms
            elif is_synced and lines[idx].end_ms is not None:
                line_duration = lines[idx].end_ms - lines[idx].start_ms
            else:
                line_duration = len(words) * 800  # fallback: 800ms per word

            word_duration_ms = max(600, line_duration // len(words))
            word_duration_s = word_duration_ms / 1000.0

            # Use interpolation for smoother word transitions
            if is_synced:
                # Get effective offset (static + dynamic)
                offset = self._offset_ms
                if lyrics and hasattr(lyrics, 'get_effective_offset'):
                    offset = lyrics.get_effective_offset()

                adjusted = progress_ms - offset
                current_line = lines[idx]
                if current_line.start_ms is not None and current_line.end_ms is not None:
                    duration = current_line.end_ms - current_line.start_ms
                    if duration > 0:
                        elapsed = adjusted - current_line.start_ms
                        ratio = max(0.0, min(1.0, elapsed / duration))
                        interpolated_idx = min(int(ratio * len(words)), len(words) - 1)
                        # Use interpolated index if it's different from time-based
                        now = time.monotonic()
                        if now - self._word_change_time >= word_duration_s * 0.8:
                            self._word_index = interpolated_idx
                            self._word_change_time = now
                    else:
                        now = time.monotonic()
                        if now - self._word_change_time >= word_duration_s:
                            self._word_index += 1
                            self._word_change_time = now
                else:
                    now = time.monotonic()
                    if now - self._word_change_time >= word_duration_s:
                        self._word_index += 1
                        self._word_change_time = now
            else:
                now = time.monotonic()
                if now - self._word_change_time >= word_duration_s:
                    self._word_index += 1
                    self._word_change_time = now

            if self._word_index >= len(words):
                self._word_index = 0
            display_word = words[self._word_index]
        else:
            display_word = " ".join(words) if has_spaces else "".join(words)

        big_lines = render_big(display_word, width - 4)

        total_height = len(big_lines)
        pad_top = max(0, (height - total_height) // 2)

        text.append("\n" * pad_top, style="bold white")

        for line in big_lines:
            line_width = len(line)
            pad_left = max(0, (width - line_width) // 2)
            text.append(" " * pad_left + line + "\n", style="bold white")

        remaining = height - pad_top - total_height - 1
        if remaining > 0:
            text.append("\n" * remaining, style="bold white")

        return text
