# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class Contract(gl.Contract):
    org_trust: TreeMap[str, str]
    org_names: TreeMap[str, str]

    def __init__(self):
        pass

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
        v_url = str(verification_url)
        o_name = str(name)

        def leader_fn():
            try:
                page = gl.nondet.web.render(v_url, mode="text")
                if not page or len(page.strip()) == 0:
                    return {"legit": False, "reason": "URL dead"}
            except Exception:
                return {"legit": False, "reason": "URL error"}

            task = (
                "You are verifying a relief organization.\n"
                "Organization claimed name: " + o_name + "\n"
                "Website Content:\n" + page + "\n"
                "Does this look like a legitimate relief/charity organization?\n"
                'Respond ONLY as JSON with keys: legit (true/false), reason (short string).'
            )
            response = gl.nondet.exec_prompt(task, response_format="json")
            if isinstance(response, dict):
                return response
            return self._parse_legit(str(response))

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                mine = leader_fn()
            except Exception:
                return False
            theirs = leader_result.calldata
            return bool(theirs.get("legit", False)) == bool(mine.get("legit", False))

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        is_legit = bool(result.get("legit", False))

        self.org_names[org] = o_name
        self.org_trust[org] = "true" if is_legit else "false"

        return "true" if is_legit else "false"

    @gl.public.view
    def get_trust(self, org: str) -> str:
        return self.org_trust.get(org, "unknown")

    @gl.public.view
    def get_name(self, org: str) -> str:
        return self.org_names.get(org, "unknown")
