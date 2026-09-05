import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from legal_crawler.manifest import CrawlManifest


def make_manifest(tmp_path: Path) -> CrawlManifest:
    return CrawlManifest(tmp_path / "manifest.sqlite")


def test_new_id_needs_refetch(tmp_path: Path):
    manifest = make_manifest(tmp_path)
    assert manifest.needs_refetch("177815", "2026-08-24") is True


def test_unchanged_lastmod_skips_refetch(tmp_path: Path):
    manifest = make_manifest(tmp_path)
    manifest.upsert(
        "177815",
        sitemap_lastmod="2026-08-24",
        content_hash="abc",
        eff_status="Còn hiệu lực",
        eff_to=None,
        crawled_at="2026-08-24T00:00:00",
    )
    assert manifest.needs_refetch("177815", "2026-08-24") is False
    assert manifest.needs_refetch("177815", "2026-09-01") is True


def test_active_doc_ids_only_lists_still_in_effect(tmp_path: Path):
    manifest = make_manifest(tmp_path)
    manifest.upsert(
        "1", sitemap_lastmod="x", content_hash="h", eff_status="Còn hiệu lực",
        eff_to=None, crawled_at="t",
    )
    manifest.upsert(
        "2", sitemap_lastmod="x", content_hash="h", eff_status="Hết hiệu lực",
        eff_to="2020-01-01", crawled_at="t",
    )
    assert manifest.active_doc_ids() == ["1"]


def test_mark_removed_excludes_from_active(tmp_path: Path):
    manifest = make_manifest(tmp_path)
    manifest.upsert(
        "1", sitemap_lastmod="x", content_hash="h", eff_status="Còn hiệu lực",
        eff_to=None, crawled_at="t",
    )
    manifest.mark_removed(["1"], removed_at="2026-08-24T00:00:00")
    assert manifest.active_doc_ids() == []


def test_upsert_is_idempotent(tmp_path: Path):
    manifest = make_manifest(tmp_path)
    for _ in range(2):
        manifest.upsert(
            "1", sitemap_lastmod="x", content_hash="h", eff_status="Còn hiệu lực",
            eff_to=None, crawled_at="t",
        )
    assert manifest.get("1").content_hash == "h"
