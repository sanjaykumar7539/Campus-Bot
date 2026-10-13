from config import config

class FallbackHandler:
    def __init__(self):
        self.fallback_message = config.FALLBACK_MESSAGE

    def handle(self, query: str, reason: str = "") -> str:
        from src.core.college_scope import requested_colleges
        scope = requested_colleges(query)
        if len(scope) == 1 and scope != {'engineering'}:
            college = next(iter(scope))
            return (
                f'I do not have verified information for the requested {college} college question. '
                'Please contact that college for the details.'
            )
        contacts = []
        if config.ESCALATION_EMAIL:
            contacts.append(f"Email: {config.ESCALATION_EMAIL}")
        if config.ESCALATION_PHONE:
            contacts.append(f"Phone: {config.ESCALATION_PHONE}")
        contacts.append(f"Admissions information: {config.ADMISSIONS_CONTACT_URL}")
        return (
            f"{self.fallback_message}\n\n"
            'For admissions assistance, contact the institute:\n'
            + '\n'.join(contacts)
        )
