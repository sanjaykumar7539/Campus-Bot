import re

class PromptSecurity:
    PATTERNS=[r'ignore (all|any|the) previous instructions',r'reveal (the )?(system|developer) prompt',
              r'print.*(api|secret|password|token|environment)',r'bypass.*(guardrail|security|policy)',
              r'jailbreak|developer mode|do anything now']
    def assess(self,text):
        matches=[p for p in self.PATTERNS if re.search(p,text or '',re.I|re.S)]
        return {'safe':not matches,'risk':'high' if matches else 'low','matches':matches}
