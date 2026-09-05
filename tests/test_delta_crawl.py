from delta_crawl import domain_of, is_stale


def test_unknown_document_is_stale():
    assert is_stale(None, "2026-09-01")


def test_matching_lastmod_is_fresh():
    assert not is_stale(("2026-09-01", "2026-09-04T00:00:00+00:00"), "2026-09-01")


def test_advanced_lastmod_is_stale():
    assert is_stale(("2026-08-01", "2026-09-04T00:00:00+00:00"), "2026-09-05")


def test_never_recorded_lastmod_is_not_evidence_of_a_change():
    # 3,168 BFS-discovered documents have an empty sitemap_lastmod. Treating
    # "" != "2026-08-01" as a change flagged 2,264 unchanged documents stale;
    # our copy is newer than that sitemap edit, so there is nothing to refetch.
    assert not is_stale(("", "2026-09-04T00:00:00+00:00"), "2026-08-01")


def test_never_recorded_but_edited_after_our_copy_is_stale():
    assert is_stale(("", "2026-09-04T00:00:00+00:00"), "2026-09-05")


def test_domain_is_matched_on_whole_slug_words():
    assert domain_of("luat-dat-dai-2024") == "dat_dai"
    assert domain_of("nghi-dinh-ve-van-tai-duong-bo") == "giao_thong"
    # "thue" must not match inside "phuong-thuc" — the whole-word rule.
    assert domain_of("quy-dinh-phuong-thuc-thanh-toan") is None
