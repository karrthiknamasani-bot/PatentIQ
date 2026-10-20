import re


class TextCleaner:
    """Deterministic text sanitizer that normalizes whitespace and line endings

    while preserving technical notations, claims, punctuation, numbers, and
    units.
    """

    # Non-printable characters excluding tab and newline
    CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
    # Unicode space variants to standard space
    UNICODE_SPACES_REGEX = re.compile(r"[\u00a0\u1680\u2000-\u200b\u202f\u205f\u3000]")

    @classmethod
    def clean(cls, text: str) -> str:
        """Cleans and normalizes text deterministically."""
        if not text:
            return ""

        # 1. Normalize line endings to \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Normalize unicode spaces
        text = cls.UNICODE_SPACES_REGEX.sub(" ", text)

        # 3. Strip control characters
        text = cls.CONTROL_CHAR_REGEX.sub("", text)

        # 4. Clean line by line (strip trailing/leading horizontal spaces per line)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        cleaned_text = "\n".join(lines)

        # 5. Condense 3+ newlines into 2 (preserves clear paragraph breaks)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        return cleaned_text.strip()
