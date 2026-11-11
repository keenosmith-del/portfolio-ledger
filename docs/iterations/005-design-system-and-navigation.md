# Iteration 005 — Design system and navigation

Status: implementation and local acceptance complete; public hosting/CI gates remain. Starting SHA `3a605a0`, 14 pre-existing dirty files preserved.

The initial UI has olive/cream literals, small type and square controls. Replace the complete palette with centralized white/charcoal/grey tokens, native system type, pill controls, readable tables, responsive navigation and shared presentation primitives. Preserve API, portfolio/filter state and financial behavior. Before screenshots and baseline browser checks pending local stack startup.

## Implemented and verified checkpoint

Complete replacement stylesheet centralizes nine palette tokens plus shape/focus/elevation tokens. All hex values are confined to root tokens; a guard rejects legacy colors, gradients, blur and sub-11px type. System font stack requires no network or redistributed fonts. Buttons/search use pill geometry, fields 14px radius, cards 20px, sheets 24px. Grayscale labels retain explicit status text. Reduced motion removes transitions/animations.

`components/Workspace.tsx` owns Badge, Empty, generic Table, Pager and Panel. App retains the single source of portfolio/filter/tab state and existing API semantics. Source selection now reads the real registry; read-only dialogs hide mutation forms/replay. Mobile logout repairs the formerly sidebar-only affordance.

Baseline Chrome 2 passed; expanded suite 6 passed in 56.5s, preserving full import/replay/source/reconciliation/review/billing/CSV/audit journey. Search/empty, keyboard containment/Escape/focus restoration, session persistence, private reviewer and six viewport widths all pass. Automated axe selected WCAG A/AA/2.1 AA checks report no violations for login and six views.

Actual before: [login](../evidence/ui/before/login-desktop.png), [overview](../evidence/ui/before/overview-desktop.png), [tablet](../evidence/ui/before/overview-tablet.png), [mobile](../evidence/ui/before/overview-mobile.png). After: [login](../evidence/ui/after/login-desktop.png), [overview](../evidence/ui/after/overview-desktop.png), [integrations](../evidence/ui/after/integrations-desktop.png), [leases](../evidence/ui/after/leases-desktop.png), [ledger](../evidence/ui/after/ledger-desktop.png), [reconciliation](../evidence/ui/after/reconciliation-desktop.png), [billing](../evidence/ui/after/billing-desktop.png), [audit](../evidence/ui/after/audit-desktop.png), [modal](../evidence/ui/after/source-modal-desktop.png), [tablet](../evidence/ui/after/overview-tablet.png), [mobile](../evidence/ui/after/overview-mobile.png).

Visual inspection covered palette leakage, radii, padding, typography, nav, input/upload/search affordances, readable financial values/IDs, modal containment and internal table scrolling. One polish correction adds metric-note spacing and normalizes uppercase metadata. Final captures/public review/restart verification recorded in the journal as completed. Evidence reflects real accumulated demo state, not reset or invented metrics.

Final acceptance: six private Chrome cases pass (19.2s), public case passes (4.2s). Navigation transition contrast defect was reproduced and corrected with audit unchanged. All final captures replaced and actually viewed; session-cleanup helper corrected and complete rerun passed. See D023/D024 and journal.

Latest final checks include corrected Nginx readiness Host forwarding (D025): six private cases pass in 33.1s, public case in 9.9s, real browser readiness 200 and dialog asserts ready/b003. Private stack restored and healthy.
