from src.core.agentic_workflow import AgenticRAGWorkflow
from src.core.reranker import CrossEncoderReranker


class Doc:
    def __init__(self, text): self.page_content, self.metadata = text, {}


def test_reranker_lexical_fallback(monkeypatch):
    reranker=CrossEncoderReranker()
    monkeypatch.setattr(reranker,'_model',lambda: (_ for _ in ()).throw(RuntimeError('offline')))
    docs,scores=reranker.rerank('admission fee',[Doc('hostel'),Doc('admission fee details')],[.8,.4],1)
    assert docs[0].page_content=='admission fee details' and len(scores)==1


def test_agentic_workflow_verifies_sources():
    workflow=AgenticRAGWorkflow(lambda **kwargs:{'answer':'ok','is_grounded':True,'sources':[{'document':'x'}]})
    assert workflow.invoke(query='fees')['is_grounded'] is True


def test_agentic_workflow_rejects_grounded_answer_without_source():
    workflow=AgenticRAGWorkflow(lambda **kwargs:{'answer':'unsafe','is_grounded':True,'sources':[]})
    result=workflow.invoke(query='fees')
    assert result['is_grounded'] is False and result['reason']=='Agentic verification failed'


def test_agentic_workflow_retries_once_on_weak_evidence():
    calls=[]
    def answer(**kwargs):
        calls.append(kwargs)
        if len(calls)==1:
            return {'answer':'fallback','is_grounded':False,'sources':[],'reason':'weak retrieval'}
        return {'answer':'verified','is_grounded':True,'sources':[{'document':'handbook.pdf'}]}
    workflow=AgenticRAGWorkflow(answer)
    result=workflow.invoke(query='please tell me CSE fees', retry_retrieval_k=6)
    assert result['answer']=='verified'
    assert len(calls)==2
    assert calls[1]['query']=='CSE fees'
    assert calls[1]['retrieval_k']==6


def test_agentic_workflow_stops_after_bounded_retry():
    calls=[]
    def answer(**kwargs):
        calls.append(kwargs)
        return {'answer':'fallback','is_grounded':False,'sources':[],'reason':'weak retrieval'}
    workflow=AgenticRAGWorkflow(answer)
    result=workflow.invoke(query='unknown policy', retry_retrieval_k=6)
    assert len(calls)==2
    assert result['is_grounded'] is False
    assert result['reason']=='Agentic verification failed'
    assert result['agentic_retry_exhausted'] is True
