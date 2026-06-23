# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class Contract(gl.Contract):
    latest_verdict: str
    latest_confidence: u256
    latest_consistency: str
    latest_scale: str
    latest_reason: str

    def __init__(self):
        self.latest_verdict = "NONE"
        self.latest_confidence = u256(0)
        self.latest_consistency = "false"
        self.latest_scale = "false"
        self.latest_reason = ""

    @gl.public.write
    def verify_disaster(self, criteria: str, source_urls: DynArray[str]) -> str:
        if len(source_urls) == 0:
            raise Exception("UserError: 0 source_urls provided")

        urls = []
        for u in source_urls:
            urls.append(u)

        def leader_fn():
            gathered = []
            for url in urls:
                try:
                    page = gl.nondet.web.render(url, mode="text")
                    if page and len(page.strip()) > 0:
                        gathered.append(page)
                except Exception:
                    pass

            if len(gathered) == 0:
                return {
                    "verdict": "INSUFFICIENT",
                    "confidence": 0,
                    "cross_source_consistency": False,
                    "scale_meets_threshold": False,
                    "reason": "No usable sources found or all URLs dead",
                }

            evidence = "\n\n---SOURCE---\n\n".join(gathered)
            task = (
                "You are a disaster-verification juror. Donor criteria: " + criteria + ".\n"
                "Using the independent sources below, decide:\n"
                "- Did a REAL disaster matching the criteria actually occur?\n"
                "- Do the sources AGREE (cross-consistent) or contradict?\n"
                "- Does the scale meet the donor's threshold in the criteria?\n"
                "- Any sign of fake, recycled, or exaggerated news?\n"
                "Sources:\n" + evidence + "\n"
                'Respond ONLY as JSON with keys: '
                'verdict (one of "CONFIRMED","REJECTED","INSUFFICIENT"), '
                "confidence (integer 0-100), "
                "cross_source_consistency (true/false), "
                "scale_meets_threshold (true/false), "
                "reason (short string)."
            )
            response = gl.nondet.exec_prompt(task, response_format="json")
            return self._parse(response)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                mine = leader_fn()
            except Exception:
                return False
            theirs = leader_result.calldata
            return (
                str(theirs.get("verdict", "")) == str(mine.get("verdict", ""))
                and bool(theirs.get("cross_source_consistency", False))
                == bool(mine.get("cross_source_consistency", False))
            )

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        verdict = str(result.get("verdict", "INSUFFICIENT"))
        if verdict not in ("CONFIRMED", "REJECTED", "INSUFFICIENT"):
            raise Exception("UserError: invalid verdict label")

        conf = 0
        try:
            conf = int(result.get("confidence", 0))
        except Exception:
            conf = 0

        self.latest_verdict = verdict
        self.latest_confidence = u256(conf)
        self.latest_consistency = "true" if result.get("cross_source_consistency", False) else "false"
        self.latest_scale = "true" if result.get("scale_meets_threshold", False) else "false"
        self.latest_reason = str(result.get("reason", "No reason provided"))

        return verdict

    def _parse(self, response):
        if isinstance(response, dict):
            return response
        text = str(response)
        out = {}
        out["verdict"] = self._field(text, "verdict", "INSUFFICIENT")
        out["reason"] = self._field(text, "reason", "No reason provided")
        cons = self._field(text, "cross_source_consistency", "false").lower()
        scal = self._field(text, "scale_meets_threshold", "false").lower()
        out["cross_source_consistency"] = (cons == "true")
        out["scale_meets_threshold"] = (scal == "true")
        digits = ""
        for ch in self._field(text, "confidence", "0"):
            if ch >= "0" and ch <= "9":
                digits += ch
        out["confidence"] = int(digits) if len(digits) > 0 else 0
        return out

    def _field(self, text: str, key: str, default: str) -> str:
        marker = '"' + key + '"'
        idx = text.find(marker)
        if idx == -1:
            return default
        i = idx + len(marker)
        n = len(text)
        while i < n and text[i] in ' \t\r\n:':
            i += 1
        if i >= n:
            return default
        if text[i] == '"':
            i += 1
            start = i
            while i < n and text[i] != '"':
                i += 1
            return text[start:i]
        start = i
        while i < n and text[i] not in ',}':
            i += 1
        return text[start:i].strip()

    @gl.public.view
    def get_latest_verdict(self) -> str:
        return self.latest_verdict

    @gl.public.view
    def get_latest_reason(self) -> str:
        return self.latest_reason

    @gl.public.view
    def get_latest_confidence(self) -> u256:
        return self.latest_confidence

    @gl.public.view
    def get_latest_consistency(self) -> str:
        return self.latest_consistency

    @gl.public.view
    def get_latest_scale(self) -> str:
        return self.latest_scale
