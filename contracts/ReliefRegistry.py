# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class Contract(gl.Contract):
    org_trust: TreeMap[str, str]
    org_names: TreeMap[str, str]

    def __init__(self):
        self.owner = "deployer"

    def _parse_legit(self, s: str) -> dict:
        res = {
            "legit": False,
            "reason": "Failed to parse"
        }
        if not s:
            return res

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

        res["legit"] = extract_bool("legit")
        res["reason"] = extract_str("reason")
        return res

    @gl.public.write
    def register_org(self, org: str, name: str, verification_url: str) -> str:
        def leader_fn() -> dict:
            try:
                page = gl.nondet.web.render(verification_url, mode="text")
                if not page or len(page.strip()) == 0:
                    return {"legit": False, "reason": "URL dead"}
            except Exception:
                return {"legit": False, "reason": "URL error"}

            task = f"""
            You are verifying a relief organization.
            Organization claimed name: {name}
            Website Content:
            {page}

            Does this look like a legitimate relief/charity organization?
            Respond ONLY with this exact JSON format:
            {{
                "legit": true,
                "reason": "short explanation"
            }}
            """
            raw = gl.nondet.exec_prompt(task)
            if not isinstance(raw, str):
                raw = str(raw)
            return self._parse_legit(raw)

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader_parsed = leader_res.calldata
            
            my_parsed = leader_fn()

            return leader_parsed.get("legit") == my_parsed.get("legit")

        parsed = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        is_legit = parsed.get("legit", False)

        self.org_names[org] = name
        self.org_trust[org] = "true" if is_legit else "false"

        return "true" if is_legit else "false"

    @gl.public.view
    def get_trust(self, org: str) -> str:
        return self.org_trust.get(org, "unknown")

    @gl.public.view
    def get_name(self, org: str) -> str:
        return self.org_names.get(org, "unknown")
