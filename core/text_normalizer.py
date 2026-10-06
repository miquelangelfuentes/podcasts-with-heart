"""
English Text Normalization and SSML Processing for Podcasts with Heart.
Handles numbers, ordinals, currencies, dates, common abbreviations,
and SSML prosodic tags (<break time="..."/>, etc.).
"""

import re
from typing import List, Tuple, Dict, Any

class EnglishTextNormalizer:
    """Fast, deterministic English text normalizer for TTS."""

    ONES = [
        "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen"
    ]
    TENS = [
        "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
    ]
    ORDINALS_ONES = {
        1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth",
        7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth",
        13: "thirteenth", 14: "fourteenth", 15: "fifteenth", 16: "sixteenth",
        17: "seventeenth", 18: "eighteenth", 19: "nineteenth"
    }
    ORDINALS_TENS = {
        20: "twentieth", 30: "thirtieth", 40: "fortieth", 50: "fiftieth",
        60: "sixtieth", 70: "seventieth", 80: "eightieth", 90: "ninetieth"
    }

    ABBREVIATIONS = {
        r"\bDr\.": "Doctor",
        r"\bMr\.": "Mister",
        r"\bMrs\.": "Missus",
        r"\bMs\.": "Mizz",
        r"\bProf\.": "Professor",
        r"\bSt\.": "Saint",
        r"\be\.g\.,?": "for example,",
        r"\bi\.e\.,?": "that is,",
        r"\betc\.": "et cetera",
        r"\bvs\.?": "versus",
        r"\bdept\.": "department",
        r"\bapprox\.": "approximately",
        r"\bmin\.": "minutes",
        r"\bsec\.": "seconds",
        r"\bhr\.": "hour",
        r"\bhrs\.": "hours",
        r"\bno\.": "number",
        r"\bNo\.": "Number",
    }

    def __init__(self):
        pass

    def number_to_words(self, n: int) -> str:
        """Converts an integer (up to 999,999,999) into English words."""
        if n == 0:
            return "zero"
        if n < 0:
            return "minus " + self.number_to_words(abs(n))

        # Check for years (e.g. 1984 -> nineteen eighty-four, 2026 -> twenty twenty-six)
        if 1100 <= n <= 2099 and n % 100 != 0:
            century = n // 100
            remainder = n % 100
            century_words = self._two_digits(century)
            remainder_words = self._two_digits(remainder)
            return f"{century_words} {remainder_words}".strip()

        words = []
        if n >= 1_000_000:
            millions = n // 1_000_000
            words.append(f"{self.number_to_words(millions)} million")
            n %= 1_000_000

        if n >= 1_000:
            thousands = n // 1_000
            words.append(f"{self.number_to_words(thousands)} thousand")
            n %= 1_000

        if n >= 100:
            hundreds = n // 100
            words.append(f"{self.ONES[hundreds]} hundred")
            n %= 100

        if n > 0:
            words.append(self._two_digits(n))

        return " ".join(words).strip()

    def _two_digits(self, n: int) -> str:
        if n < 20:
            return self.ONES[n]
        tens = n // 10
        ones = n % 10
        if ones == 0:
            return self.TENS[tens]
        return f"{self.TENS[tens]}-{self.ONES[ones]}"

    def ordinal_to_words(self, n: int) -> str:
        """Converts an integer to ordinal words (1 -> first, 21 -> twenty-first)."""
        if n in self.ORDINALS_ONES:
            return self.ORDINALS_ONES[n]
        if n in self.ORDINALS_TENS:
            return self.ORDINALS_TENS[n]
        if n < 100:
            tens = (n // 10) * 10
            ones = n % 10
            return f"{self.TENS[n // 10]}-{self.ORDINALS_ONES.get(ones, '')}"
        
        # General fallback: cardinal + th
        cardinal = self.number_to_words(n)
        if cardinal.endswith("y"):
            return cardinal[:-1] + "ieth"
        return cardinal + "th"

    def normalize(self, text: str) -> str:
        """Full normalization pipeline for English text."""
        if not text:
            return ""

        # 1. Expand abbreviations
        for pattern, replacement in self.ABBREVIATIONS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # 2. Currency expansion
        def _replace_currency(match):
            symbol = match.group(1)
            amount_str = match.group(2).replace(",", "")
            try:
                amount = float(amount_str)
                dollars = int(amount)
                cents = int(round((amount - dollars) * 100))
                
                curr_name = "dollar" if dollars == 1 else "dollars"
                if symbol == "£":
                    curr_name = "pound" if dollars == 1 else "pounds"
                elif symbol == "€":
                    curr_name = "euro" if dollars == 1 else "euros"

                res = f"{self.number_to_words(dollars)} {curr_name}"
                if cents > 0:
                    res += f" and {self.number_to_words(cents)} cents"
                return res
            except Exception:
                return match.group(0)

        text = re.sub(r'([$€£])(\d+(?:\.\d{1,2})?)', _replace_currency, text)

        # 3. Percentages
        def _replace_percent(match):
            num = match.group(1)
            try:
                val = int(num)
                return f"{self.number_to_words(val)} percent"
            except Exception:
                return f"{num} percent"

        text = re.sub(r'\b(\d+)%', _replace_percent, text)

        # 4. Ordinals (1st, 2nd, 3rd, 4th, etc.)
        def _replace_ordinal(match):
            num = int(match.group(1))
            return self.ordinal_to_words(num)

        text = re.sub(r'\b(\d+)(?:st|nd|rd|th)\b', _replace_ordinal, text, flags=re.IGNORECASE)

        # 5. Integers (isolated numbers)
        def _replace_number(match):
            num = int(match.group(0))
            if num < 1_000_000_000:
                return self.number_to_words(num)
            return match.group(0)

        text = re.sub(r'\b\d+\b', _replace_number, text)

        # 6. Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text).strip()

        return text

    def parse_ssml_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Parses text for <break time="..."/> tags and returns sequential segments.
        Each segment is either {"type": "text", "content": "..."} or
        {"type": "silence", "duration_ms": 400}.
        """
        tag_pattern = re.compile(r'<break\s+time=["\']([0-9.]+)(ms|s)["\']\s*/?>', re.IGNORECASE)
        segments = []
        last_idx = 0

        for match in tag_pattern.finditer(text):
            pre_text = text[last_idx:match.start()].strip()
            if pre_text:
                segments.append({"type": "text", "content": pre_text})
            
            val = float(match.group(1))
            unit = match.group(2).lower()
            duration_ms = int(val if unit == "ms" else val * 1000)
            segments.append({"type": "silence", "duration_ms": duration_ms})
            last_idx = match.end()

        tail = text[last_idx:].strip()
        if tail:
            segments.append({"type": "text", "content": tail})

        return segments
