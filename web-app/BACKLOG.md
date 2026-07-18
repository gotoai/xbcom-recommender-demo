# web-app — backlog

Tracked follow-ups for the XB.com recommender demo front-end.

## User display names
- [ ] **Associate a display name with each traveler (user).** The source
  `DATA/s03_primary/inbound_traveler.tsv` has no name field, so the active-user
  list currently labels each user as `Traveler #<id>` with a nationality flag.
  Give every `traveler_id` a stable, locale-appropriate display name (ideally
  keyed off nationality so, e.g., a 米国 traveler reads as an English name and a
  韓国 traveler as a Korean one), then surface it on the user card and detail
  screen in place of / alongside the ID. Keep it deterministic (seeded by
  `traveler_id`) so the same user always shows the same name.

## Later phases (not in the current scope)
- [ ] User detail: replace the stub "recommendations coming soon" panel with the
      actual coupon recommendations (join visits → shops/coupons active on the
      aligned dates).
