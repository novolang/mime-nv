# mime-nv

**Status: NOT IMPLEMENTED — interface only.**

Every public function below is published with its signature and its
effect row, and every body is `todo()`. Installing this package works;
calling it panics with `not implemented`.

## What this is

Media types as values: what a file claims to be, what its bytes say it
is, and which of a server's own answers a client would most like.

- `mimecode` — the well-known types as integers; the device half;
- `mimetype` — `type/subtype; param=value`, parsed into spans;
- `mimeext` — the extension table, both ways;
- `mimesniff` — the WHATWG pattern table, with `nosniff` as a flag;
- `mimeaccept` — negotiation, answering one of the caller's offers.

```
novo pkg add mime-nv
novo pkg build
novo test
```

## The one example that will work

```novo ignore
use mimecode
use mimeext
use mimesniff

// What a static-file server sends for a file it just read.
fn content_type(filename: Str, head: Bytes) -> Str
    let claimed = mimeext.code_for_name(filename)
    if claimed == mimecode.unknown()
        mimecode.code_name(mimesniff.sniff(head, MimeSniffBrowsing))
    else
        mimecode.code_name(claimed)
```

## The load-bearing interface: `sniff_with`

```novo ignore
pub fn sniff_with(head: Bytes, supplied: Str, nosniff: Bool,
                  ctx: MimeSniffContext) -> Int []
```

**Sniffing is a security mechanism pretending to be a convenience.** A
browser sniffs because servers lie about `Content-Type`, and the
consequence is that a file a site let a user upload can be made to run
as HTML **on that site's own origin**: upload a `.txt` whose first bytes
are `<!DOCTYPE html>`, serve it as `text/plain`, and a browser that
sniffs will render it.

That is why `X-Content-Type-Options: nosniff` exists, and why it is a
parameter here rather than a sentence in a README. The algorithm's
answer depends on all three of the bytes, the supplied type and the
flag, and a function that took only the bytes would be answering a
different question from the one a browser asks:

| supplied | `nosniff` | answer |
| --- | --- | --- |
| `text/plain` | no | **sniffed** — the bytes decide |
| `text/plain` | yes | `text/plain` — the bytes are not consulted |
| `image/png` | no | `image/png` — not a sniffable type |

The last row is the part most descriptions of sniffing leave out.
Sniffing is not "the bytes win": a supplied type outside a named set —
`text/plain`, `application/octet-stream`, `unknown/unknown`, `*/*` and
absent — is **kept**. `is_sniffable_type` answers that question on its
own, and `would_sniff` is what a server asks about **its own** response
before it sends one.

## The extension table and the sniffer disagree, and neither overrules

An extension is evidence of one thing: what the person who named the
file believed. That is weak evidence, and it is the only evidence a
server has before it opens the file.

So `mimeext` answers what the **name** says, `mimesniff` answers what
the **bytes** say, and this package never reconciles them — because the
right answer differs by caller:

- a **static-file server** over its own content trusts the name: it
  put the files there;
- an **upload endpoint** trusts neither, pins a type of its own
  choosing, and sends `nosniff` — because a `photo.png` whose bytes are
  HTML is either a mistake or an attack;
- an **archiver** or a **mail client** wants both, and to say so when
  they differ.

`code_is_inline` is published for the second case: whether a browser
renders a type inline rather than downloading it is the question that
decides whether an upload can run script on the serving origin.

## The essence is the comparison, and `==` on the header is the bug

`text/html`, `TEXT/HTML` and `text/html; charset=utf-8` are one type to
a browser and three strings to `==`. RFC 9110 calls the first two bytes
the media type's **essence** — type and subtype, lowercased, parameters
dropped — and `essence_eq` compares that without allocating anything.

A caller that wrote `header == "text/html"` has a bug that appears the
first time a server adds a charset.

A parsed type is **spans over the caller's own string**, so a request
that only asks "is this JSON?" copies nothing. Parameters are a **list**
and not a map: RFC 2045 gives no uniqueness rule, `multipart/form-data`
carries a `boundary` that must survive verbatim, and a map would reorder
them and lose a duplicate silently.

Quoted strings are part of the grammar rather than an edge case — a
boundary contains characters a token may not, so
`boundary="---=_Part_0_1"` is the ordinary spelling and a parser that
only handled tokens would fail on every multipart body it ever saw.

## Negotiation answers one of the server's own offers

```novo ignore
match mimeaccept.best(header, ["application/json", "text/html"])
    Some(i) => ...    // dispatch on the index
    None    => ...    // 406
```

A ranked list of what the *client* asked for is not an answer, because
most of what a client asks for is not on offer. `best` takes the header
and the caller's list and answers an **index into the caller's list**.

**Specificity is checked before q**, and that is the rule most
implementations get wrong. `text/*;q=0.9, */*;q=1` means *"I prefer
anything textual, and I will take anything"* — a negotiator that ranked
by q would serve it the first thing on its list. RFC 9110 § 12.5.1: most
specific first, then q, then the server's own order.

**`q=0` is a refusal, not a low score.** `*/*;q=0` means nothing is
acceptable, and `best` answers `None` — a 406. That is a different
answer from an **empty** header, which means anything and takes the
server's first offer.

q is carried as **thousandths** rather than a `Float`, because RFC 9110
gives it at most three decimal places and because two floats that should
compare equal sometimes do not — which in a negotiator means the order
of two equally-acceptable types depending on rounding.

`vary_header()` is published beside `best` because forgetting `Vary` is
a caching bug with an ugly shape: a shared cache that stored a JSON
response under a URL hands it to the next client that asked for HTML.

## The device claim, and the half it covers

`@tier(embedded)` is claimed for **`mimecode` and the `@value` half of
`mimesniff`**, and `tests/embedded_probe.nv` builds for
`--target=nrf52-qemu`.

A firmware HTTP server answering `GET /logo.png` off a flash filesystem
needs one thing from this package — the nine bytes `image/png` — and
what it cannot do is build them: a `MimeType` holds spans into a string,
and a device with no heap has no string to span. So the device path is
integers: a code out of the extension, or a code out of the first bytes,
and `code_name` at the end producing a constant that lives in flash.

The sniffer's `@value` machine is the same table walk `sniff` does,
called from two places rather than implemented twice — the suite checks
that they agree on every vector. A device feeds it the bytes it was
already reading and stops as soon as `sniff_settled` answers `true`,
which for a PNG is eight bytes rather than 1445.

`mimetype`, `mimeext` and `mimeaccept` are **not** claimed: a parsed
type is a list of parameter spans, the extension table is six hundred
strings, and negotiation builds a ranked list. All three allocate by
construction.

## The layer, and the two absent dependencies

`core` — no effects. This package is **handed** the first bytes of a
file; it never opens one. The `Content-Type` it parses is a string the
caller already has.

**http-codec-nv is not a dependency.** A `Content-Type` is a header
*value*, and a header value is a string; which header it came out of is
the business of whatever parsed the message. That is what lets the
standard library's `HttpHeader`, http-codec-nv's `H1Headers` and a
device's own eight-line parser all hand it the same string.

**unicode-nv is not one either, and the absence is a finding.** RFC 2045
defines a media type's grammar over ASCII and browsers compare type and
subtype ASCII-case-insensitively, deliberately — so `TEXT/HTML` and
`text/html` are one type with no Unicode table anywhere. The one place a
caller might expect Unicode is the `charset` parameter, and a charset
*name* is an ASCII label registered with IANA; what the label **means**
is a decoder's business.

## What this replaces, and what it would take

`compiler/stdlib/http_server.nv`'s `http_server_mime_type` is a
twenty-branch `match` over `path.ext`, and it is the whole of the
standard library's media-type support. It has no parser, no sniffer and
no negotiation, so a server built on it cannot answer *"is this request
body JSON?"* without comparing header strings, cannot decide a type for
a file with no extension, and cannot honour an `Accept`.

Adopting this deletes that `match` and gives the same servers the other
three. `orbit/static-site-generator` is the second consumer: it writes
files whose type it knows and would use `mimeext.preferred_ext` to name
them, which is the reverse direction and the one a generator needs.

## Where the names come from

Public type names are unique across the whole assembly, dependencies
included.

| here | the obvious name | why not |
| --- | --- | --- |
| `MimeType` | `MediaType`, `ContentType` | both are names a future HTTP package will want, and `Type` is impossible |
| `MimeParam` | `Param` | `HttpParam` is the standard library's and `Param` is what four packages want |
| `MimeSpan` | `Span` | url-nv publishes `Span`, and it is a module name in use |
| `MimeRange` | `Range` | generic, and a byte range is a different thing in the same domain |
| `MimeSniff` | `Sniffer`, `Scanner` | generic |
| `MimeError` | `ParseError` | every parser on the grid wants it |
| module `mimetype`, `mimeext`, … | `mime`, `types`, `ext`, `sniff`, `accept` | all five are names another package will want, and a bare `mime` would collide with a future multipart package's own module |

The codes are **functions returning integers** rather than an enum,
which looks odd until the device is in view: an enum is not a position a
`@value` sniffer's state may occupy (SPEC § 14.5), and the state has to
hold one. A function returning a literal compiles to the literal.

## The reference implementation

**`mime_guess`** for the extension table, which is Apache's
`mime.types` — and the reason to take somebody else's list rather than
curate one is that a curated list disagrees with the server in front of
it. **Python's `mimetypes`** for the two-way lookup and for the
observation that the reverse direction has to be a list. **The WHATWG
MIME Sniffing standard** for the pattern table, its order, the
sniffable-type set and the `nosniff` rule. **RFC 2045 § 5.1** for the
grammar, **RFC 6839** for the `+suffix`, and **RFC 9110 § 12.5.1** for
negotiation.

The oracles are the WHATWG standard's own pattern table, the
`mime_guess` extension list, and RFC 9110's `Accept` examples.

Deliberately left out, and where it goes instead:

- **Reading a file.** `core`; this package is handed the head.
- **Charset decoding.** A charset name is a label here; turning
  Windows-1252 bytes into text is an encoding package's job.
- **Multipart bodies.** `form-nv`'s row on the plan. This package
  answers the `boundary`; parsing what it delimits is a different
  parser.
- **The image, audio and video sniffing tables' full pattern sets.**
  `MimeSniffContext` is the seam and the general table is implemented;
  the context-specific tables are each a different table selected by how
  the resource was requested.
- **`Content-Disposition`.** A different header with a different
  grammar, and RFC 6266's filename rules are their own package.
- **An IANA registry mirror.** The full registry is thousands of types
  with its own update cadence, and a copy compiled in here would be
  stale the day it published.

## Status

Every function is `todo()`. Two suites, both red, both for the same
reason — every assertion reaches `not implemented: mime-nv.<fn>`, which
is the expected result until the bodies land.

```
novo test --isolate tests/mimetype_tests.nv    # the grammar, the essence, the extension table
novo test --isolate tests/mimesniff_tests.nv   # the pattern table, nosniff, and Accept
```

`tests/embedded_probe.nv` is not a test: it is the device claim, built
for `--target=nrf52-qemu` by the audit's `core-embedded` row.

`novo doc` renders and its examples compile.
