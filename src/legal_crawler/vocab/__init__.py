"""Verified code tables loaded from `data/*.json`, all under one rule.

`referenceType` numbers, effectivity codes and field/major names are all
undocumented vocabularies of the source. Each table here is hand-verified, and
each raises on a code it does not know rather than defaulting to a plausible
label — a mis-read code corrupts every point-in-time answer built on it, and
does so silently (docs/crawling-plan.md §3b).
"""
