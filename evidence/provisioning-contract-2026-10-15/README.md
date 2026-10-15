# Evidence: delivered provisioning contract

Commit: de43764afd20d6fb465e194e78f0d937f6bd5bd5

## git show de43764a:crates/iw-protocol/src/provision.rs (key lines)
```
46:pub const MAX_PROVISION_BYTES: usize = 1 << 20;
52:pub enum ProvisionFeature {
424:        #[serde(flatten)]
430:        #[serde(flatten)]
432:        #[serde(flatten)]
437:        #[serde(flatten)]
439:        #[serde(flatten)]
444:        #[serde(flatten)]
446:        #[serde(flatten)]
451:        #[serde(flatten)]
453:        #[serde(flatten)]
458:        #[serde(flatten)]
460:        #[serde(flatten)]
465:        #[serde(flatten)]
467:        #[serde(flatten)]
472:        #[serde(flatten)]
474:        #[serde(flatten)]
```
## git show de43764a:crates/iw-core/src/provisioning.rs (key lines)
```
27://! - **Fail closed.** [`emergency_stop`](OwnerPolicy::emergency_stop) refuses
29://!   [`allowlist`](OwnerPolicy::allowlist) authorizes no parent at all.
61:    /// allowlisted parents, and never downloads, loads or activates anything
87:    pub allowlist: Vec<String>,
91:    pub emergency_stop: bool,
98:            allowlist: Vec::new(),
99:            emergency_stop: false,
130:    /// The parent is not on the allowlist.
139:    AutonomousUnavailable,
145:/// mode refuses everything; then a parent outside the allowlist is refused;
148:    if policy.emergency_stop {
154:            if !policy.allowlist.iter().any(|p| p == parent) {
170:                    Decision::Refused(Refusal::AutonomousUnavailable)
185:            allowlist: allow.iter().map(|s| s.to_string()).collect(),
186:            emergency_stop: false,
208:    fn disabled_ignores_allowlist() {
235:    fn empty_allowlist_authorizes_nobody() {
244:    fn parent_outside_allowlist_is_refused_before_mode_rule() {
246:        // ObserveOnly — the allowlist check runs first (fail closed).
277:            Decision::Refused(Refusal::AutonomousUnavailable)
```
## git show de43764a:crates/iw-core/src/provision_planner.rs (key lines)
```
151:                model_name == req.model || model_name.starts_with(&format!("{}-", req.model));
248:            available_vram: Quantity {
```
## git show de43764a:crates/iw-core/src/provision_capacity.rs (key lines)
```
25://!   `deny_unknown_fields`), so a newer owner never makes an older reader
93:    pub available_vram: Quantity,
138:    /// - `available_vram` is summed across adverts into one `Derived`
177:        let available_vram = if any_vram {
202:            available_vram,
276:            available_vram: Quantity {
380:        assert_eq!(sig.available_vram.known_bytes(), Some(20_000_000));
408:        assert_eq!(sig.available_vram.known_bytes(), None);
409:        assert_eq!(sig.available_vram.basis, Basis::Unknown);
```
## git show de43764a:crates/iw-gateway/src/provision_controller.rs (key lines)
```
20://!   activated. An allowlisted parent can book a reservation but can never
30://! - **Expiring lease**: each reservation has a `lease_expires_at`; the
55:pub const DEFAULT_LEASE_TTL: u64 = 300;
79:    pub lease_expires_at: u64,
232:    /// `Disabled` with an empty allowlist, so a fresh controller serves and
252:    /// allowlist and emergency stop. The caller is responsible for persisting
307:                r.lease_expires_at <= now
395:    /// Accept an offer and make a reservation for an allowlisted parent. The
441:            lease_expires_at: now + DEFAULT_LEASE_TTL,
455:                expires_at: Some(now + DEFAULT_LEASE_TTL),
462:                lease_ttl: DEFAULT_LEASE_TTL,
588:            if reservation.lease_expires_at <= now {
776:            allowlist: allow.iter().map(|s| s.to_string()).collect(),
777:            emergency_stop: false,
808:            available_vram: Quantity {
830:    fn allowlist_authorizes_only_named_parents() {
846:    fn emergency_stop_beats_everything() {
848:        policy.emergency_stop = true;
980:        assert_eq!(c.tick(100 + DEFAULT_LEASE_TTL - 1).len(), 0);
982:        let events = c.tick(100 + DEFAULT_LEASE_TTL);
```
## git show de43764a:crates/iw-gateway/src/provision_transport.rs (key lines)
```
28://! (mode `Disabled`, empty allowlist) refuses every message it receives,
45:pub const MAX_PROVISION_BODY: usize = 1 << 20;
53:    /// The body was larger than [`MAX_PROVISION_BODY`].
69:            Self::Oversized => write!(f, "provision message exceeds {MAX_PROVISION_BODY} bytes"),
122:    /// default policy is `Disabled` with an empty allowlist, so the
161:        if bytes.len() > MAX_PROVISION_BODY {
317:            allowlist: allow.iter().map(|s| s.to_string()).collect(),
318:            emergency_stop: false,
337:            available_vram: Quantity {
416:        let big = vec![b'x'; MAX_PROVISION_BODY + 1];
```
