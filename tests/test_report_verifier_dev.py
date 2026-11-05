from report_verifier_dev import describe
from test_rag_corpus import CLAUSE, corpus, data  # noqa: F401


def test_x4_distinguishes_empty_citations_expiry_and_missing_representation(corpus):
    uid = f'version:{CLAUSE.split(":")[1]}:1'
    rows = [dict(id='a', group='T6', answerable=True, as_of='2021-01-01'),
            dict(id='b', group='T6', answerable=False, as_of='2022-01-01'),
            dict(id='c', group='T1', answerable=True, as_of='2021-01-01'),
            dict(id='d', group='T1', answerable=True, as_of='2021-01-01')]
    predictions = [dict(id='a', citations=[uid]), dict(id='b', citations=[uid]),
                   dict(id='c', citations=[]), dict(id='d', citations=[f'asis:{CLAUSE}'])]
    report = describe(rows, predictions, corpus)
    assert report['groups']['all']['flagged_rows'] == 1
    assert report['details'][3]['citation_tiers'] == {f'asis:{CLAUSE}': 'document'}
    assert report['groups']['all']['cited_rows'] == 3
    assert report['groups']['all']['rows_without_propagated_windows'] == 1
    assert report['groups']['T6_answerable']['flagged_rows'] == 0
    assert report['groups']['T6_unanswerable']['flagged_rows'] == 1
