import importlib.util
from pathlib import Path

import pytest

from vilexgraph import llm
from vilexgraph.framework.generate import Answer
from vilexgraph.framework.retrieve import Hit
from vilexgraph.framework.systems import get
from test_rag_corpus import CLAUSE, corpus, data  # noqa: F401

spec = importlib.util.spec_from_file_location('demo', Path(__file__).parents[1] / 'scripts/demo.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_demo_request_keeps_evidence_when_generator_is_unavailable(corpus):
    calls = []
    uid = f'version:{CLAUSE.split(":")[1]}:1'

    def search(question, as_of):
        calls.append((question, as_of))
        return [Hit(uid)]

    def unavailable(*args, **kwargs):
        raise llm.LLMError('no configured provider')

    result = demo.handle_request({'question': 'Quy định gì?', 'as_of': '2021-01-01'},
                                 spec=get('proposed2'), corpus=corpus, search=search,
                                 generator=unavailable)
    assert calls == [('Quy định gì?', '2021-01-01')]
    assert result['evidence'][0]['ordinal'] == 1
    assert result['evidence'][0]['effective_intervals'] == [('2020-01-01', '2022-01-01')]
    assert result['answer'] is None and result['verification'] is None
    assert 'chưa sinh câu trả lời' in result['status']
    success = demo.handle_request({'question': 'Quy định gì?', 'as_of': '2021-01-01'},
                                  spec=get('proposed2'), corpus=corpus, search=search,
                                  generator=lambda *a, **kw: Answer('x', True, (uid,), 'raw', 'fake', 'fake'))
    assert success['verification']['action'] == 'pass'
    assert success['verification']['checked'] == 1
    assert success['answer']['text'] == 'x'


def test_demo_rejects_invalid_date_before_retrieval():
    with pytest.raises(ValueError):
        demo.handle_request({'question': 'q', 'as_of': '2021-02-30'}, spec=get('proposed2'),
                            corpus=None, search=lambda *a: pytest.fail('retrieval must not run'))
