from __future__ import annotations

import re
from typing import Callable, TypedDict


class WorkflowState(TypedDict, total=False):
    query: str
    original_query: str
    plan: str
    result: dict
    verified: bool
    retry_count: int
    _arguments: dict


class AgenticRAGWorkflow:
    """Bounded, auditable Agentic RAG workflow.

    The workflow intentionally stays small for a college knowledge assistant:
    plan -> answer -> verify -> (rewrite + wider retrieval once, when needed) -> verify.
    It does not add autonomous web access, MCP, GraphRAG, or multi-agent overhead.
    """

    MAX_RETRIES = 1

    def __init__(self, answer_fn: Callable[..., dict]):
        self.answer_fn = answer_fn
        self.graph = None
        try:
            from langgraph.graph import StateGraph, START, END

            graph = StateGraph(WorkflowState)
            graph.add_node('planning', self._plan)
            graph.add_node('answer', self._answer)
            graph.add_node('verify', self._verify)
            graph.add_node('rewrite', self._rewrite)
            graph.add_edge(START, 'planning')
            graph.add_edge('planning', 'answer')
            graph.add_edge('answer', 'verify')
            graph.add_conditional_edges(
                'verify', self._route_after_verify,
                {'retry': 'rewrite', 'done': END},
            )
            graph.add_edge('rewrite', 'answer')
            self.graph = graph.compile()
        except ImportError:
            pass

    @staticmethod
    def _plan(state):
        return {
            'plan': 'retrieve -> rerank -> ground -> answer -> verify; retry once with a focused query and wider retrieval if evidence is weak',
            'retry_count': 0,
            'original_query': state.get('query', ''),
        }

    def _answer(self, state):
        arguments = dict(state['_arguments'])
        arguments['query'] = state.get('query', arguments.get('query', ''))
        # On the single retry, inspect a wider final evidence set. The retriever
        # still performs its normal hybrid search and cross-encoder reranking.
        if state.get('retry_count', 0) > 0:
            arguments['retrieval_k'] = arguments.get('retry_retrieval_k')
        arguments.pop('retry_retrieval_k', None)
        return {'result': self.answer_fn(**arguments)}

    @staticmethod
    def _is_valid(result: dict) -> bool:
        if not result or not result.get('answer'):
            return False
        if result.get('is_grounded') is True:
            return bool(result.get('sources'))
        return False

    def _verify(self, state):
        result = state.get('result') or {}
        valid = self._is_valid(result)
        # Keep the original failure reason during the retry decision. Only the
        # final failed attempt is labelled as an agentic verification failure.
        if not valid and state.get('retry_count', 0) >= self.MAX_RETRIES:
            result = {
                **result,
                'is_grounded': False,
                'sources': [],
                'reason': 'Agentic verification failed',
                'agentic_retry_exhausted': True,
            }
        return {'result': result, 'verified': valid}

    def _route_after_verify(self, state):
        if state.get('verified'):
            return 'done'
        return 'retry' if state.get('retry_count', 0) < self.MAX_RETRIES else 'done'

    @staticmethod
    def _focused_query(query: str) -> str:
        """Remove conversational filler while preserving IDs, names and numbers."""
        text = re.sub(r'\s+', ' ', query or '').strip()
        if not text:
            return text
        filler = re.compile(
            r'\b(?:please|can you|could you|would you|tell me|show me|i want to know|'
            r'enaku|ennaku|sollu|sollunga|konjam|please tell)\b', re.IGNORECASE,
        )
        focused = re.sub(r'\s+', ' ', filler.sub(' ', text)).strip(' ?.,')
        return focused or text

    def _rewrite(self, state):
        original = state.get('original_query') or state.get('query', '')
        return {
            'query': self._focused_query(original),
            'retry_count': state.get('retry_count', 0) + 1,
            'verified': False,
        }

    def invoke(self, **arguments):
        initial = {
            'query': arguments.get('query', ''),
            '_arguments': arguments,
            'retry_count': 0,
        }
        if self.graph:
            return self.graph.invoke(initial)['result']

        state = {**initial, **self._plan(initial)}
        while True:
            state.update(self._answer(state))
            state.update(self._verify(state))
            if self._route_after_verify(state) == 'done':
                return state['result']
            state.update(self._rewrite(state))
