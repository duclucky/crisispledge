# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class Contract(gl.Contract):
    next_id: u256
    pledge_donor: TreeMap[u256, str]
    pledge_org: TreeMap[u256, str]
    pledge_amount: TreeMap[u256, u256]
    pledge_criteria: TreeMap[u256, str]
    pledge_urls: TreeMap[u256, str]
    pledge_deadline: TreeMap[u256, u256]
    pledge_status: TreeMap[u256, str]
    pledge_verdict: TreeMap[u256, str]
    pledge_reason: TreeMap[u256, str]
    trusted_orgs: TreeMap[str, str]

    def __init__(self):
        self.owner = "deployer"
        self.next_id = u256(0)

    def _parse_verdict(self, s: str) -> dict:
        res = {
            "verdict": "INSUFFICIENT",
            "confidence": 0,
            "cross_source_consistency": False,
            "scale_meets_threshold": False,
            "reason": "Failed to parse"
        }
        if not s:
            return res

        def extract_str(key: str) -> str:
            idx = s.find('"' + key + '"')
            if idx == -1: return ""
            col = s.find(':', idx)
            if col == -1: return ""
            st = s.find('"', col)
            if st == -1: return ""
            en = s.find('"', st + 1)
            while en != -1 and s[en-1] == '\\':
                en = s.find('"', en + 1)
            if en == -1: return ""
            return s[st+1:en]

        def extract_int(key: str) -> int:
            idx = s.find('"' + key + '"')
            if idx == -1: return 0
            col = s.find(':', idx)
            if col == -1: return 0
            st = col + 1
            while st < len(s) and not (s[st].isdigit() or s[st] == '-'):
                st += 1
            if st == len(s): return 0
            en = st
            while en < len(s) and s[en].isdigit():
                en += 1
            try:
                return int(s[st:en])
            except Exception:
                return 0

        def extract_bool(key: str) -> bool:
            idx = s.find('"' + key + '"')
            if idx == -1: return False
            col = s.find(':', idx)
            if col == -1: return False
            en = s.find(',', col)
            if en == -1: en = s.find('}', col)
            if en == -1: en = len(s)
            val = s[col+1:en].strip().lower()
            return "true" in val

        v = extract_str("verdict")
        if v in ["CONFIRMED", "REJECTED", "INSUFFICIENT"]:
            res["verdict"] = v
        res["confidence"] = extract_int("confidence")
        res["cross_source_consistency"] = extract_bool("cross_source_consistency")
        res["scale_meets_threshold"] = extract_bool("scale_meets_threshold")
        res["reason"] = extract_str("reason")
        return res

    @gl.public.write
    def create_pledge(self, relief_org: str, amount: int, criteria: str, source_urls: str, deadline_ts: int) -> u256:
        if amount <= 0:
            raise Exception("UserError: amount must be > 0")

        pid = self.next_id
        self.pledge_donor[pid] = "donor"
        self.pledge_org[pid] = relief_org
        self.pledge_amount[pid] = u256(amount)
        self.pledge_criteria[pid] = criteria
        self.pledge_urls[pid] = source_urls
        self.pledge_deadline[pid] = u256(deadline_ts)
        self.pledge_status[pid] = "OPEN"
        self.pledge_verdict[pid] = "NONE"
        self.pledge_reason[pid] = ""

        self.next_id = pid + u256(1)
        return pid

    @gl.public.write
    def set_trusted_org(self, org: str) -> None:
        self.trusted_orgs[org] = "true"

    @gl.public.write
    def trigger_verification(self, pledge_id: int) -> str:
        pid = u256(pledge_id)
        status = self.pledge_status.get(pid, "")
        if status != "OPEN":
            raise Exception("UserError: pledge already resolved")

        urls_str = self.pledge_urls.get(pid, "")
        url_list = urls_str.split("\n")
        source_urls = [u.strip() for u in url_list if len(u.strip()) > 0]
        criteria = self.pledge_criteria.get(pid, "")
        relief_org = self.pledge_org.get(pid, "")

        def leader_fn() -> dict:
            if len(source_urls) == 0:
                return {"verdict": "INSUFFICIENT", "confidence": 0, "cross_source_consistency": False, "scale_meets_threshold": False, "reason": "No sources"}

            gathered = []
            for url in source_urls:
                try:
                    page = gl.nondet.web.render(url, mode="text")
                    if page and len(page.strip()) > 0:
                        gathered.append(page)
                except Exception:
                    pass

            if len(gathered) == 0:
                return {"verdict": "INSUFFICIENT", "confidence": 0, "cross_source_consistency": False, "scale_meets_threshold": False, "reason": "All URLs dead"}

            evidence = "\n\n---SOURCE---\n\n".join(gathered)
            task = f"""
            You are a disaster-verification juror. Donor criteria: {criteria}.
            Using the independent sources below, decide:
            - Did a REAL disaster matching the criteria actually occur?
            - Do the sources AGREE (cross-consistent) or contradict?
            - Does the scale meet the donor's threshold in the criteria?
            - Any sign of fake, recycled, or exaggerated news?
            Sources:
            {evidence}
            Respond ONLY with this exact JSON format:
            {{
                "verdict": "CONFIRMED",
                "confidence": 90,
                "cross_source_consistency": true,
                "scale_meets_threshold": true,
                "reason": "short text"
            }}
            """
            raw = gl.nondet.exec_prompt(task)
            if not isinstance(raw, str):
                raw = str(raw)
            return self._parse_verdict(raw)

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader_parsed = leader_res.calldata
            
            my_parsed = leader_fn()

            if leader_parsed.get("verdict") != my_parsed.get("verdict"):
                return False
            if leader_parsed.get("cross_source_consistency") != my_parsed.get("cross_source_consistency"):
                return False
            if leader_parsed.get("scale_meets_threshold") != my_parsed.get("scale_meets_threshold"):
                return False
            return True

        parsed = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        v = parsed.get("verdict", "INSUFFICIENT")
        c = parsed.get("confidence", 0)
        consist = parsed.get("cross_source_consistency", False)
        scale = parsed.get("scale_meets_threshold", False)
        reason = parsed.get("reason", "")

        self.pledge_verdict[pid] = v
        self.pledge_reason[pid] = reason

        is_trusted = self.trusted_orgs.get(relief_org, "false") == "true"

        if v == "CONFIRMED" and c >= 75 and consist and scale and is_trusted:
            self.pledge_status[pid] = "RELEASED"
        else:
            self.pledge_status[pid] = "OPEN"

        return v

    @gl.public.write
    def claim_refund(self, pledge_id: int, now_ts: int) -> str:
        pid = u256(pledge_id)
        status = self.pledge_status.get(pid, "")
        if status != "OPEN":
            raise Exception("UserError: refund not allowed yet / already resolved")

        deadline = self.pledge_deadline.get(pid, u256(0))
        if u256(now_ts) < deadline:
            raise Exception("UserError: refund not allowed yet")

        self.pledge_status[pid] = "REFUNDED"
        return "REFUNDED"

    @gl.public.view
    def get_status(self, id: int) -> str:
        return self.pledge_status.get(u256(id), "")

    @gl.public.view
    def get_verdict(self, id: int) -> str:
        return self.pledge_verdict.get(u256(id), "")

    @gl.public.view
    def get_reason(self, id: int) -> str:
        return self.pledge_reason.get(u256(id), "")

    @gl.public.view
    def get_amount(self, id: int) -> u256:
        return self.pledge_amount.get(u256(id), u256(0))

    @gl.public.view
    def get_pledge_count(self) -> u256:
        return self.next_id

    @gl.public.view
    def is_trusted(self, org: str) -> str:
        return self.trusted_orgs.get(org, "false")
