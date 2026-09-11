# Changelog

All notable changes to mime-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.0.1 — 2026-09-11

The **interface**: every signature and every effect row, and no bodies.
`stability = "draft"`, and the release is recorded `implemented = false`.

### Added

- `mimecode` — the well-known types as integers, so the device path and
  the host's fast path share one vocabulary and every comparison is an
  integer test.
- `mimetype` — RFC 2045's grammar, quoted strings included, parsed into
  spans over the caller's own string, with `essence_eq` as the
  comparison a caller should make.
- `mimeext` — `mime_guess`'s table both ways, with `preferred_ext` as
  the pick the reverse direction otherwise refuses to make.
- `mimesniff` — the WHATWG pattern table as a whole-buffer function and
  as a `@value` machine, with `nosniff` and the supplied type in the
  signature.
- `mimeaccept` — RFC 9110 § 12.5.1's negotiation, answering an index
  into the caller's own offers.

### Known

- **`sniff_with` is the load-bearing interface.** Sniffing is a security
  mechanism, and its answer depends on the bytes, the supplied type and
  `X-Content-Type-Options` together.
- **A supplied type outside a named set is kept.** Sniffing is not "the
  bytes win", and that is the part most descriptions omit.
- **The name and the bytes are answered separately and neither
  overrules**, because the right reconciliation differs by caller.
- **`essence_eq` is the comparison**; `header == "text/html"` is a bug
  that appears the first time a server adds a charset.
- **Parameters are a list**, because RFC 2045 gives no uniqueness rule
  and a multipart boundary must survive verbatim.
- **Specificity is checked before q** in negotiation, and `q=0` is a
  refusal rather than a low score.
- **`@tier(embedded)` is claimed for `mimecode` and the sniffer's
  `@value` half**, and the probe builds it for a Cortex-M4. The other
  three modules allocate by construction.
- **No dependencies.** http-codec-nv and unicode-nv are both absent on
  purpose; the README says why for each.
