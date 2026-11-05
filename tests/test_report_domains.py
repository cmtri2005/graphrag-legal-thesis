from report_domains import summarize


def test_domains_count_multilabel_rows_once_and_keep_scorer_denominators():
    rows = [dict(id='a', lineage_id='p', version_id='version:p:1', answerable=True,
                 short_answer='đúng', answer='đúng', accepted_evidence=['version:p:1'],
                 group='T1', as_of='2021-01-01', domain=['thue', 'dat_dai', 'thue']),
            dict(id='b', lineage_id='p', version_id=None, answerable=False, short_answer='',
                 answer='', accepted_evidence=[], group='T6', as_of='2022-01-01', domain=['thue'])]
    predictions = {'old': {'a': dict(answer='đúng', retrieved=['version:p:1'], citations=['version:p:1']),
                           'b': dict(answerable=True, answer='', citations=[])}}
    units = {'version:p:1': [('p', 1, [('2020-01-01', None)])]}
    report = summarize(rows, predictions, units)
    assert (report['thue']['rows'], report['thue']['lineages']) == (2, 1)
    assert report['dat_dai']['rows'] == 1
    assert report['thue']['small'] is True
    metrics = report['thue']['systems']['old']
    assert metrics == dict(accuracy=0.5, **{'tv_recall@1': 0.5}, tver=0.0, cited_rows=1)
    assert report['dat_dai']['systems']['old']['accuracy'] == 1.0
