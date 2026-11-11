# ADR-002: Durable worker and revisioned publication

Date: 2026-11-11. Status: accepted for implementation.

Context: an in-process background task cannot guarantee execution after restart. Snapshot replay must not erase historical postings, and old revisions must not revert newer data.

Decision: durable PostgreSQL import rows; claim with FOR UPDATE SKIP LOCKED; commit claim; process under row/source locks; commit all accepted effects and all row outcomes together. A crashed processing transaction rolls back effects; lease expiry permits reclaim. Three claims maximum. Semantic row failures use savepoints and explicit quarantine reasons. Database or programming failures abort the entire attempt and trigger bounded recovery.

Same source ID/revision/content is duplicate. Same revision/different content is conflict. Lower revision is quarantined. Higher revision preserves the earlier posting and adds reversal/replacement. Snapshot absence never deletes entities or postings; providers must send explicit ended lease revisions. Snapshot freshness is visible, and absence semantics are documented.

Consequences: one attempt may hold a long transaction, bounded by 8 MiB/20,000 rows; 10k benchmark will measure suitability. Source rows retain allowlisted sanitized payload plus content hash; receipt retains original file checksum. An opaque replay receipt is separate from the original batch. Production-scale COPY/staging is a future measured optimization, not a claimed capability.
