# Changelog

All notable changes to mime-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.0.2 — 2026-09-15

README rewritten to the package README style guide (docs/writing-a-readme.md); no change to the interface.

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

### Design notes

Public type names are unique across a whole assembly, dependencies
included, so every type here is prefixed. `MimeType` rather than
`MediaType` or `ContentType`, both of which a future HTTP package will
want; `MimeParam` because `HttpParam` is the standard library's;
`MimeSpan` because url-nv publishes `Span`; `MimeRange` because a byte
range is a different thing in the same domain; `MimeError` because
every parser wants `ParseError`. The modules are prefixed for the same
reason, and because a bare `mime` would collide with a future multipart
package's own module.

The named first consumer is `compiler/stdlib/http_server.nv`, whose
`http_server_mime_type` is a twenty-branch match over a path extension
and is the whole of the standard library's media-type support. A server
built on it cannot answer whether a request body is JSON without
comparing header strings, cannot decide a type for a file with no
extension, and cannot honour an `Accept`.
`orbit/static-site-generator` is the second, and wants
`mimeext.preferred_ext`, which is the reverse direction.
