# M0 bar amendments

This file records changes to `docs/m0-bars.md`. The freeze on 2026-10-07 has no amendment. A later change appends one section below and leaves every earlier byte in place.

## Amendment

- date: 2026-11-25
- old_sha256: 90260c785e8ae256d519a0d2f5f964e546f92704af4e318ec666fd31162db7ef
- new_sha256: 90260c785e8ae256d519a0d2f5f964e546f92704af4e318ec666fd31162db7ef
- reason: The 25 Nov 2026 host switch moves scored inference to GEEKOM Halo (halo-395, Ubuntu). That host may carry a scored run immediately. Downstairs NVIDIA hosts (downstairs-4080, downstairs-3060) are fallback only. Do not average their rows with halo-395 rows. All other M0 bars stay frozen until a follow-up amend updates the normative page.

When `docs/m0-bars.md` is amended, set `host_budget.inference_hosts` to `["halo-395"]`, add `inference_hosts_fallback` as `["downstairs-4080", "downstairs-3060"]`, and remove the downstairs-before-halo gate in prose and JSON.