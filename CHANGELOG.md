# Changelog

All notable changes to mime-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.1.0 — 2026-09-27

The first implementation of the interface published as 0.0.1: media
types parsed and printed, the extension table both ways, the WHATWG
sniffing algorithm, and `Accept` negotiation.

### Added

- `mimetype` parses RFC 2045 section 5.1 with the optional whitespace
  RFC 9110 allows around `;`, and skips empty parameters.
  `value_str` answers one parameter's value, for a caller walking a
  repeated parameter.
- `mimeext` holds mime_guess's table of 1379 extensions, written by
  `tools/ext_table.py` from a pinned commit.  `preferred_ext` picks the
  extension Python's `mimetypes` prefers where it is one the table
  lists.
- `mimesniff_core`, a new module, is the sniffer's `@value` walk.  It
  covers every row of the MIME Sniffing Standard's general, image,
  audio-video, archive and text-or-binary tables, with the MP4 and WebM
  signatures computed a byte at a time.  Every function in it and in
  `mimecode` carries `@tier(embedded)`.
- `mimecode` gains eleven codes, one for each answer of the sniffing
  tables that had none, plus `text/javascript`, which the extension
  table answers for `.js` (RFC 9239): `text_javascript`, `text_xml`,
  `image_bmp`, `application_postscript`, `audio_aiff`,
  `application_ogg`, `audio_midi`, `video_avi`, `audio_wave`,
  `video_webm` and `application_x_rar_compressed`.
- `tests/differential_tests.nv` checks the parser against Python's
  `email` package and the table against its `mimetypes`, and is written
  by `tools/differential.py`.
- `tests/alloc_scan.sh` checks the emitted LLVM for an allocation in the
  two device modules, with a negative control that must be caught.

### Changed

These break code written against 0.0.x.

- The byte-at-a-time sniffer moved from `mimesniff` to
  `mimesniff_core`: `MimeSniff`, `sniff_start`, `sniff_byte`,
  `sniff_end`, `sniff_settled`, `sniff_code`, `sniff_binary` and
  `sniff_pos`.  `mimesniff` takes `Bytes` and `Str`, which the embedded
  runtime does not define, and one host-only function in a compilation
  unit fails a device build at link time.  The context codes are
  `mimesniff_core.ctx_browsing()` and its siblings;
  `mimesniff.context_code` still converts a `MimeSniffContext`.
- `MimeSniff`'s fields describe the walk and changed with it.
- `sniff_with` follows the standard's section 7 where the interface's
  comments did not.  A supplied `text/plain` is never sniffed to HTML:
  in the four spellings an old Apache server writes it becomes
  `application/octet-stream` for binary bytes and stays `text/plain`
  otherwise, and in any other spelling it is kept.
  `application/octet-stream` is kept.  With `nosniff`, a missing or
  unknown type is still sniffed without the HTML, XML and PDF rows.
- `is_sniffable_type` answers whether a supplied type counts as none:
  empty, not a media type, `unknown/unknown`, `application/unknown` or
  `*/*`.  It answered `true` for `text/plain` and
  `application/octet-stream` in the interface's tests.
- An empty resource sniffs as `text/plain`, the standard's answer, and
  a WebAssembly module as `application/octet-stream`, because the
  standard has no row for it.
- `mimeaccept` follows RFC 9110 section 12.5.1: the most specific
  matching range sets an offer's quality, and the highest quality wins.
  The interface compared specificity between offers, so
  `text/*;q=0.9, */*;q=1` now ranks JSON above HTML.  `specificity`
  adds one for each parameter a range names, and a range's parameters
  must be on an offer for it to match.
- `MimeRange.extensions` holds every parameter other than `q`, wherever
  it stands, as RFC 9110 has a recipient read `q` in any position.
- `mimeext` answers every extension with its dot: `ext_at` and
  `exts_for_type` as well as `ext_of` and `preferred_ext`.

### Toolchain

- The toolchain floor is 0.13.0. The bodies are written for it and use
  no workaround: the parameter loop skips an empty parameter with
  `continue`. One parameter is still read by a function of its own,
  because that keeps the loop short.

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
