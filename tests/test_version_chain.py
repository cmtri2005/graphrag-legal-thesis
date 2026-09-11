import json
from datetime import date
from pathlib import Path

import pytest

from legal_crawler.temporal.models import ProvisionVersion, TemporalInterval
from legal_crawler.temporal.version_chain import (
    DuplicateVersionError,
    NoCurrentVersionError,
    OverlappingVersionError,
    ProvisionMismatchError,
    VersionChain,
    VersionChainError,
)

FIXTURE = Path(__file__).parent / "fixtures" / "temporal" / "version_chain.json"


def make_version(
    provision_id: str,
    ordinal: int,
    start: date,
    end: date | None = None,
    *,
    version_id: str | None = None,
) -> ProvisionVersion:
    return ProvisionVersion(
        id=version_id or f"version-{ordinal}",
        provision_id=provision_id,
        ordinal=ordinal,
        text=f"version {ordinal}",
        validity=TemporalInterval(start, end),
    )


def load_fixture_chain() -> tuple[VersionChain, dict]:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    versions = [
        ProvisionVersion(
            id=item["id"],
            provision_id=raw["provision_id"],
            ordinal=item["ordinal"],
            text=item["text"],
            validity=TemporalInterval(
                date.fromisoformat(item["start"]),
                date.fromisoformat(item["end"]) if item["end"] else None,
            ),
            created_by_event_id=item.get("created_by_event_id"),
        )
        for item in raw["versions"]
    ]
    return VersionChain(raw["provision_id"], reversed(versions)), raw


def test_chain_sorts_input_and_resolves_a_b_c_fixture():
    chain, raw = load_fixture_chain()

    assert [version.ordinal for version in chain.versions] == [1, 2, 3]
    for query in raw["queries"]:
        result = chain.at(date.fromisoformat(query["at"]))
        actual = result.ordinal if result else None
        assert actual == query["expected_ordinal"]


def test_exact_duplicate_add_is_idempotent():
    version = make_version("article-1", 1, date(2020, 1, 1))
    chain = VersionChain("article-1", [version])

    assert chain.add(version) is False
    assert len(chain) == 1


def test_conflicting_id_or_ordinal_is_rejected():
    original = make_version("article-1", 1, date(2020, 1, 1), date(2021, 1, 1))
    chain = VersionChain("article-1", [original])

    with pytest.raises(DuplicateVersionError, match="id already exists"):
        chain.add(
            make_version(
                "article-1",
                2,
                date(2021, 1, 1),
                version_id=original.id,
            )
        )
    with pytest.raises(DuplicateVersionError, match="ordinal already exists"):
        chain.add(
            make_version(
                "article-1",
                1,
                date(2021, 1, 1),
                version_id="different-version-id",
            )
        )


def test_overlapping_versions_are_rejected_but_gaps_are_allowed():
    chain = VersionChain(
        "article-1",
        [make_version("article-1", 1, date(2020, 1, 1), date(2022, 1, 1))],
    )

    with pytest.raises(OverlappingVersionError):
        chain.add(make_version("article-1", 2, date(2021, 1, 1)))

    assert chain.add(make_version("article-1", 2, date(2023, 1, 1)))
    assert chain.at(date(2022, 6, 1)) is None


def test_version_for_another_provision_is_rejected():
    chain = VersionChain("article-1")
    with pytest.raises(ProvisionMismatchError):
        chain.add(make_version("article-2", 1, date(2020, 1, 1)))


def test_close_current_preserves_frozen_version_and_boundary_semantics():
    current = make_version("article-1", 1, date(2020, 1, 1))
    chain = VersionChain("article-1", [current])

    closed = chain.close_current(date(2024, 1, 1))

    assert current.validity.end is None
    assert closed.validity.end == date(2024, 1, 1)
    assert chain.current() is None
    assert chain.at(date(2023, 12, 31)) == closed
    assert chain.at(date(2024, 1, 1)) is None


def test_close_requires_an_open_version_and_later_date():
    closed = make_version("article-1", 1, date(2020, 1, 1), date(2021, 1, 1))
    chain = VersionChain("article-1", [closed])
    with pytest.raises(NoCurrentVersionError):
        chain.close_current(date(2022, 1, 1))

    open_chain = VersionChain(
        "article-1", [make_version("article-1", 1, date(2020, 1, 1))]
    )
    with pytest.raises(VersionChainError, match="at least one day"):
        open_chain.close_current(date(2020, 1, 1))


def test_consistency_requires_contiguous_ordinals():
    with pytest.raises(DuplicateVersionError, match="contiguous"):
        VersionChain(
            "article-1", [make_version("article-1", 2, date(2020, 1, 1))]
        )


def test_failed_add_does_not_mutate_the_chain():
    first = make_version("article-1", 1, date(2020, 1, 1), date(2021, 1, 1))
    chain = VersionChain("article-1", [first])

    with pytest.raises(DuplicateVersionError, match="contiguous"):
        chain.add(make_version("article-1", 3, date(2021, 1, 1)))

    assert chain.versions == (first,)
