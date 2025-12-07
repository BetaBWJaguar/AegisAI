class MaskingRuleUtil:

    @staticmethod
    def apply(text: str, mode: str) -> str:
        if not text:
            return text

        mode = mode.upper()

        if mode == "FULL":
            return "*" * len(text)

        if mode == "PARTIAL":
            visible = max(1, int(len(text) * 0.3))
            return text[:visible] + "*" * (len(text) - visible)

        return text
