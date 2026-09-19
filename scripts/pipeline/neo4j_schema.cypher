// Phase 3 D1: node identity for a derived, rebuildable Neo4j graph.
// This file can be rerun with cypher-shell -f. Each uniqueness constraint
// also provides the id lookup index used by MERGE in the D2 loader.
CREATE CONSTRAINT kg_document_id_unique IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT kg_provision_id_unique IF NOT EXISTS FOR (n:Provision) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT kg_provision_version_id_unique IF NOT EXISTS FOR (n:ProvisionVersion) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT kg_legal_event_id_unique IF NOT EXISTS FOR (n:LegalEvent) REQUIRE n.id IS UNIQUE;

// Structural relationship contract for D2 (not DDL-enforced in Neo4j):
// (:Document)-[:CONTAINS]->(:Provision)  for root legal units.
// (:Provision)-[:CONTAINS]->(:Provision) for parent/child legal units.
// (:ProvisionVersion)-[:VERSION_OF]->(:Provision).
// (:ProvisionVersion)-[:CAUSED_BY]->(:LegalEvent).
// Keep created-by versus ended-by event roles distinct when loading.
