# College-only answer rule

Answers use evidence belonging to the requested college. Engineering, pharmacy,
nursing, polytechnic, arts and science, education, naturopathy, and school
requests are handled by the same rule. Questions without a college name use
the configured institute. A group directory is allowed when explicitly requested.

Mixed pages are filtered by college headings and sentence ownership before
grounding and answer formatting. Sentences naming additional colleges are
excluded unless all of those colleges were requested. Unattributed evidence
on group pages is excluded; ambiguous ownership produces a fallback rather
than transferring another college's facts.

The engineering verified Q&A and learned phrases cannot answer a question
scoped to a different college. If that college's answer cannot be verified,
the fallback asks the user to contact that college and does not give another
college's information or contact details.

College recognition uses the aliases in `src/core/college_scope.py`. Add aliases
and explicit ownership metadata when introducing additional institutions.
This is an application rule; no model retraining is needed. Restart a running
server to load changes.
