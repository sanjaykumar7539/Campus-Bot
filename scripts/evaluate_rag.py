"""Offline, reproducible RAG quality evaluation; no judge LLM or cloud required."""
import json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.core.rag_chain import RAGChain

def tokens(text): return set(re.findall(r'[a-z0-9&]+',(text or '').lower()))
def overlap(a,b):
    a,b=tokens(a),tokens(b);return len(a&b)/max(len(a),1)

def main():
    cases=json.loads((ROOT/'evaluation/questions.json').read_text(encoding='utf-8'))
    rag=RAGChain(); rows=[]
    for case in cases:
        result=rag.invoke(case['question'])
        expected=case.get('expected_answer',''); expected_source=case.get('expected_source','').lower()
        source_hit=any(expected_source in s['document'].lower() for s in result['sources']) if expected_source else None
        rows.append({'question':case['question'],'grounded':result['is_grounded'],'confidence':result['confidence'],
            'answer_relevance':overlap(case['question'],result['answer']),
            'expected_answer_overlap':overlap(expected,result['answer']) if expected else None,'source_hit':source_hit})
    def avg(key):
        values=[r[key] for r in rows if r[key] is not None];return sum(values)/len(values) if values else None
    report={'cases':len(rows),'grounded_rate':sum(r['grounded'] for r in rows)/max(len(rows),1),
        'mean_confidence':avg('confidence'),'mean_answer_relevance':avg('answer_relevance'),
        'mean_expected_answer_overlap':avg('expected_answer_overlap'),'source_recall_at_k':avg('source_hit'),'results':rows}
    out=ROOT/'evaluation/rag_evaluation_report.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2));print(f'Report: {out}')
if __name__=='__main__': main()
