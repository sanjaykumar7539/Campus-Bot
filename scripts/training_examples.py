"""Shared prompt construction for evidence-grounded question answering."""
GROUNDING_INSTRUCTION = (
    'Answer the question using only the supplied evidence for the target college. '
    'Return the relevant answer without introductions or additional facts. '
    'If the evidence college differs from the target college, or evidence is missing, '
    'reply exactly: Verified information for the requested college is unavailable.'
)


def messages_for(row):
    messages = []
    if 'context' in row:
        messages.append({'role': 'system', 'content': GROUNDING_INSTRUCTION})
        question = (f"Target college: {row['college']}\nEvidence college: {row['evidence_college']}\n"
                    f"Evidence: {row['context']}\nQuestion: {row['question']}")
    else:
        question = row['question']
    messages.append({'role': 'user', 'content': question})
    return messages
