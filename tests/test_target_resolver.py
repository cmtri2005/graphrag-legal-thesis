from dataclasses import replace

import pytest

from legal_crawler.index import TemporalIndex
from legal_crawler.extraction import (
    ProvisionLocator,
    ProvisionReferencePart,
    ResolutionStatus,
    TargetReference,
    TargetResolution,
    TargetResolutionCode,
    TargetResolutionError,
    TargetResolver,
    TargetScope,
)
from legal_crawler.temporal import LegalDocument, Provision, ProvisionLevel


LAW_A = "document:law-a"
LAW_B = "document:law-b"


def part(level: ProvisionLevel, label: str) -> ProvisionReferencePart:
    return ProvisionReferencePart(level, label)


def locator(*parts: tuple[ProvisionLevel, str]) -> ProvisionLocator:
    return ProvisionLocator(tuple(part(level, label) for level, label in parts))


def reference(
    identifier: str,
    target: ProvisionLocator,
    *,
    scope: TargetScope = TargetScope.EXACT,
) -> TargetReference:
    return TargetReference(
        identifier,
        "tham chiếu kiểm thử",
        scope,
        locator=target,
    )


def seeded_resolver() -> tuple[TemporalIndex, TargetResolver]:
    store = TemporalIndex()
    store.put_documents(
        (
            LegalDocument(LAW_A, "01/2020/QH", "Luật A"),
            LegalDocument(LAW_B, "02/2020/QH", "Luật B"),
        )
    )
    store.put_provisions(
        (
            Provision(
                "chapter:a:ii",
                LAW_A,
                ProvisionLevel.CHAPTER,
                "CHƯƠNG II - QUY ĐỊNH CHUNG",
                None,
                order_index=1,
            ),
            Provision(
                "article:a:6",
                LAW_A,
                ProvisionLevel.ARTICLE,
                "Điều 6. Điều kiện áp dụng",
                "chapter:a:ii",
                order_index=1,
            ),
            Provision(
                "clause:a:6:2",
                LAW_A,
                ProvisionLevel.CLAUSE,
                "2. Phạm vi",
                "article:a:6",
                order_index=1,
            ),
            Provision(
                "point:a:6:2:d",
                LAW_A,
                ProvisionLevel.POINT,
                "d) Nội dung cũ",
                "clause:a:6:2",
                order_index=1,
            ),
            Provision(
                "clause:a:6:3",
                LAW_A,
                ProvisionLevel.CLAUSE,
                "Khoản 3",
                "article:a:6",
                order_index=2,
            ),
            Provision(
                "article:a:7",
                LAW_A,
                ProvisionLevel.ARTICLE,
                "Điều 7",
                "chapter:a:ii",
                order_index=2,
            ),
            Provision(
                "clause:a:7:2",
                LAW_A,
                ProvisionLevel.CLAUSE,
                "2.",
                "article:a:7",
                order_index=1,
            ),
            Provision(
                "unnumbered:a",
                LAW_A,
                ProvisionLevel.ARTICLE,
                "Quy định chuyển tiếp",
                "chapter:a:ii",
                order_index=3,
            ),
            Provision(
                "article:b:6",
                LAW_B,
                ProvisionLevel.ARTICLE,
                "Điều 6",
                None,
                order_index=1,
            ),
            Provision(
                "clause:b:6:2",
                LAW_B,
                ProvisionLevel.CLAUSE,
                "Khoản 2",
                "article:b:6",
                order_index=1,
            ),
        )
    )
    return store, TargetResolver(store)


def test_resolves_article_clause_point_by_complete_hierarchical_path():
    _, resolver = seeded_resolver()
    target = reference(
        "point-d",
        locator(
            (ProvisionLevel.ARTICLE, "Điều 6"),
            (ProvisionLevel.CLAUSE, "2"),
            (ProvisionLevel.POINT, "điểm d"),
        ),
    )

    result = resolver.resolve(target, (LAW_A,))

    assert result.code is TargetResolutionCode.RESOLVED_EXACT
    assert result.target.status is ResolutionStatus.RESOLVED
    assert result.target.target_document_id == LAW_A
    assert result.target.target_provision_ids == ("point:a:6:2:d",)
    assert result.target.confidence == 1.0


def test_outer_context_disambiguates_repeated_clause_labels():
    _, resolver = seeded_resolver()
    broad = reference(
        "clause-2",
        locator((ProvisionLevel.CLAUSE, "2")),
    )
    contextual = replace(
        broad,
        id="article-6-clause-2",
        locator=locator(
            (ProvisionLevel.ARTICLE, "6"),
            (ProvisionLevel.CLAUSE, "2"),
        ),
    )

    ambiguous = resolver.resolve(broad, (LAW_A,))
    resolved = resolver.resolve(contextual, (LAW_A,))

    assert ambiguous.code is TargetResolutionCode.AMBIGUOUS_LOCATOR
    assert ambiguous.target.status is ResolutionStatus.NEEDS_REVIEW
    assert ambiguous.target.target_provision_ids == ()
    assert ambiguous.target.candidate_provision_ids == (
        "clause:a:6:2",
        "clause:a:7:2",
    )
    assert resolved.target.target_provision_ids == ("clause:a:6:2",)


def test_does_not_guess_for_missing_or_unnumbered_titles():
    _, resolver = seeded_resolver()
    missing = reference(
        "article-99",
        locator((ProvisionLevel.ARTICLE, "99")),
    )

    result = resolver.resolve(missing, (LAW_A,))

    assert result.code is TargetResolutionCode.LOCATOR_NOT_FOUND
    assert result.target.status is ResolutionStatus.UNRESOLVED
    assert "unnumbered:a" not in result.target.candidate_provision_ids


def test_rejects_unsupported_reference_label_instead_of_fuzzy_matching():
    _, resolver = seeded_resolver()
    target = reference(
        "descriptive-article",
        locator((ProvisionLevel.ARTICLE, "Điều về điều kiện áp dụng")),
    )

    result = resolver.resolve(target, (LAW_A,))

    assert result.code is TargetResolutionCode.UNSUPPORTED_LABEL
    assert result.target.status is ResolutionStatus.UNRESOLVED


def test_multiple_document_candidates_remain_ambiguous_when_both_match():
    _, resolver = seeded_resolver()
    target = reference(
        "article-6",
        locator((ProvisionLevel.ARTICLE, "6")),
    )

    result = resolver.resolve(target, (LAW_A, LAW_B))

    assert result.code is TargetResolutionCode.AMBIGUOUS_LOCATOR
    assert result.target.candidate_document_ids == (LAW_A, LAW_B)
    assert result.target.candidate_provision_ids == (
        "article:a:6",
        "article:b:6",
    )


def test_unique_structural_match_can_select_one_of_candidate_documents():
    _, resolver = seeded_resolver()
    target = reference(
        "article-7",
        locator((ProvisionLevel.ARTICLE, "7")),
    )

    result = resolver.resolve(target, (LAW_A, LAW_B))

    assert result.target.status is ResolutionStatus.RESOLVED
    assert result.target.target_document_id == LAW_A
    assert result.target.target_provision_ids == ("article:a:7",)


def test_unknown_document_candidate_prevents_partial_resolution():
    _, resolver = seeded_resolver()
    target = reference(
        "article-7",
        locator((ProvisionLevel.ARTICLE, "7")),
    )

    result = resolver.resolve(target, (LAW_A, "document:missing"))

    assert result.code is TargetResolutionCode.DOCUMENT_NOT_FOUND
    assert result.target.status is ResolutionStatus.UNRESOLVED
    assert result.target.target_document_id is None


def test_document_scope_requires_one_explicit_document_candidate():
    _, resolver = seeded_resolver()
    target = TargetReference(
        "whole-law",
        "Luật này",
        TargetScope.DOCUMENT,
        document_reference="Luật này",
    )

    resolved = resolver.resolve(target, (LAW_A,))
    ambiguous = resolver.resolve(target, (LAW_A, LAW_B))

    assert resolved.code is TargetResolutionCode.RESOLVED_DOCUMENT
    assert resolved.target.target_document_id == LAW_A
    assert ambiguous.code is TargetResolutionCode.AMBIGUOUS_DOCUMENT
    assert ambiguous.target.status is ResolutionStatus.NEEDS_REVIEW


def test_subtree_resolution_retains_root_and_descendants_in_document_order():
    _, resolver = seeded_resolver()
    target = reference(
        "chapter-ii",
        locator((ProvisionLevel.CHAPTER, "ii")),
        scope=TargetScope.SUBTREE,
    )

    result = resolver.resolve(target, (LAW_A,))

    assert result.code is TargetResolutionCode.RESOLVED_SUBTREE
    assert result.target.target_provision_ids == ("chapter:a:ii",)
    assert result.target.affected_provision_ids == (
        "chapter:a:ii",
        "article:a:6",
        "clause:a:6:2",
        "point:a:6:2:d",
        "clause:a:6:3",
        "article:a:7",
        "clause:a:7:2",
        "unnumbered:a",
    )


def insertion_reference(
    *,
    under: ProvisionLocator | None,
    after: ProvisionLocator | None,
) -> TargetReference:
    return TargetReference(
        "new-point-dd",
        "bổ sung điểm đ sau điểm d khoản 2 Điều 6",
        TargetScope.EXACT,
        locator=locator(
            (ProvisionLevel.ARTICLE, "6"),
            (ProvisionLevel.CLAUSE, "2"),
            (ProvisionLevel.POINT, "đ"),
        ),
        is_insertion=True,
        insert_under=under,
        insert_after=after,
    )


def test_resolves_insertion_parent_and_sibling_anchor_consistently():
    _, resolver = seeded_resolver()
    parent = locator(
        (ProvisionLevel.ARTICLE, "6"),
        (ProvisionLevel.CLAUSE, "2"),
    )
    sibling = locator(
        (ProvisionLevel.ARTICLE, "6"),
        (ProvisionLevel.CLAUSE, "2"),
        (ProvisionLevel.POINT, "d"),
    )

    result = resolver.resolve(
        insertion_reference(under=parent, after=sibling),
        (LAW_A,),
        introduced_provision_id="provision:new-point-dd",
    )

    assert result.code is TargetResolutionCode.RESOLVED_INSERTION
    assert result.target.resolves_insertion
    assert result.target.introduced_provision_id == "provision:new-point-dd"
    assert result.target.insertion_parent_id == "clause:a:6:2"
    assert result.target.insertion_after_provision_id == "point:a:6:2:d"


def test_insertion_requires_stable_id_after_anchors_are_resolved():
    _, resolver = seeded_resolver()
    sibling = locator(
        (ProvisionLevel.ARTICLE, "6"),
        (ProvisionLevel.CLAUSE, "2"),
        (ProvisionLevel.POINT, "d"),
    )

    result = resolver.resolve(
        insertion_reference(under=None, after=sibling),
        (LAW_A,),
    )

    assert result.code is TargetResolutionCode.INSERTION_ID_REQUIRED
    assert result.target.status is ResolutionStatus.UNRESOLVED
    assert result.target.candidate_provision_ids == ("point:a:6:2:d",)


def test_inconsistent_insertion_anchors_are_not_accepted():
    _, resolver = seeded_resolver()
    wrong_parent = locator(
        (ProvisionLevel.ARTICLE, "7"),
        (ProvisionLevel.CLAUSE, "2"),
    )
    sibling = locator(
        (ProvisionLevel.ARTICLE, "6"),
        (ProvisionLevel.CLAUSE, "2"),
        (ProvisionLevel.POINT, "d"),
    )

    result = resolver.resolve(
        insertion_reference(under=wrong_parent, after=sibling),
        (LAW_A,),
        introduced_provision_id="provision:new-point-dd",
    )

    assert result.code is TargetResolutionCode.INCONSISTENT_INSERTION_ANCHORS
    assert result.target.status is ResolutionStatus.UNRESOLVED


def test_resolve_many_preserves_order_and_introduced_id_mapping():
    _, resolver = seeded_resolver()
    article = reference(
        "article-7",
        locator((ProvisionLevel.ARTICLE, "7")),
    )
    sibling = locator(
        (ProvisionLevel.ARTICLE, "6"),
        (ProvisionLevel.CLAUSE, "2"),
        (ProvisionLevel.POINT, "d"),
    )
    insertion = insertion_reference(under=None, after=sibling)

    results = resolver.resolve_many(
        (article, insertion),
        (LAW_A,),
        introduced_provision_ids={
            insertion.id: "provision:new-point-dd",
        },
    )

    assert tuple(item.target.reference_id for item in results) == (
        article.id,
        insertion.id,
    )
    assert results[1].target.introduced_provision_id == "provision:new-point-dd"


def test_resolver_rejects_invalid_batch_contracts():
    _, resolver = seeded_resolver()
    target = reference(
        "article-7",
        locator((ProvisionLevel.ARTICLE, "7")),
    )

    with pytest.raises(TargetResolutionError, match="duplicates"):
        resolver.resolve(target, (LAW_A, LAW_A))
    with pytest.raises(TargetResolutionError, match="duplicate IDs"):
        resolver.resolve_many((target, target), (LAW_A,))
    with pytest.raises(TargetResolutionError, match="must be a mapping"):
        resolver.resolve_many(
            (target,),
            (LAW_A,),
            introduced_provision_ids=[],
        )
    with pytest.raises(TargetResolutionError, match="unknown references"):
        resolver.resolve_many(
            (target,),
            (LAW_A,),
            introduced_provision_ids={"missing": "provision:new"},
        )


def test_resolution_outcome_rejects_code_and_status_mismatch():
    _, resolver = seeded_resolver()
    target = reference(
        "article-7",
        locator((ProvisionLevel.ARTICLE, "7")),
    )
    resolved = resolver.resolve(target, (LAW_A,))

    with pytest.raises(TargetResolutionError, match="requires status"):
        TargetResolution(
            resolved.target,
            TargetResolutionCode.LOCATOR_NOT_FOUND,
            "inconsistent outcome",
        )


def test_part_ordinal_words_match_on_both_sides():
    store = TemporalIndex()
    store.put_documents([LegalDocument(LAW_A, "01/2020/QH", "Luật A")])
    store.put_provisions([
        Provision("part:2", LAW_A, ProvisionLevel.PART, "Phần Thứ Hai", None, order_index=0),
        Provision("art:49", LAW_A, ProvisionLevel.ARTICLE, "Điều 49", "part:2", order_index=1),
    ])
    result = TargetResolver(store).resolve(
        reference("r", locator((ProvisionLevel.PART, "Thứ Hai"), (ProvisionLevel.ARTICLE, "49"))),
        (LAW_A,),
    )
    assert result.target.candidate_provision_ids == ("art:49",)
