# mime-nv

A media type, also called a MIME type, names what a piece of data is.
It is written `type/subtype`, optionally followed by parameters, and
its grammar is
[RFC 2045 section 5.1](https://www.rfc-editor.org/rfc/rfc2045#section-5.1).
`Content-Type` carries one. This package parses a media type, looks one
up from a file's name, works one out from a file's first bytes to the
[WHATWG MIME Sniffing Standard](https://mimesniff.spec.whatwg.org/),
and answers an `Accept` header to
[RFC 9110 section 12.5.1](https://www.rfc-editor.org/rfc/rfc9110#section-12.5.1).
[form-nv](https://novo-lang.org/packages/form-nv) and
[static-nv](https://novo-lang.org/packages/static-nv) are built on it.

**Status: NOT IMPLEMENTED — interface only.** Every function is
declared with its full signature, but every body is a `todo()` that
panics when called. The package is published so its design can be
reviewed and depended on before it is implemented. Version 0.1.0 will
be the first working release.

## What a media type is

`text/html; charset=utf-8` is a **type**, `text`, a **subtype**,
`html`, and one **parameter** with a name and a value. The type and the
subtype together, lowercased and with the parameters dropped, are the
media type's **essence** (RFC 9110 section 8.3.1). `text/html`,
`TEXT/HTML` and `text/html; charset=utf-8` have one essence and are
three different strings.

A parameter value is either a **token**, which excludes control
characters, spaces and the separators `()<>@,;:\"/[]?=`, or a **quoted
string** in double quotes with backslash escapes. A `multipart`
boundary usually needs the quoted form, because it contains characters
a token may not.

A subtype may carry a **structured syntax suffix** after a `+`, such as
`image/svg+xml` and `application/ld+json` (RFC 6839). The suffix says
what the underlying syntax is, so a parser for that syntax can be
chosen without knowing the subtype.

**Sniffing** is working out what data is from its leading bytes rather
than from what a server said. Browsers do it because servers get
`Content-Type` wrong. The WHATWG standard fixes a pattern table, the
order in which it is consulted, and the set of supplied types that may
be overridden at all. The response header
`X-Content-Type-Options: nosniff` turns it off for one response.

An **`Accept` header** is a client's list of media **ranges** with
optional quality values, such as `text/html;q=0.8, application/json`. A
range may use `*` for the type, the subtype or both. The quality value
`q` runs from 0 to 1 with at most three decimal places, and `q=0` means
the range is not acceptable at all.

Every function in this package performs no input and no output. It is
handed a file's first bytes and never opens one.

## Install

```
novo pkg add mime-nv
```

## Example

```novo
use std.bytes
use mimeaccept
use mimecode
use mimeext
use mimesniff
use mimetype

fn main() [io]
    // What the file's name claims it is.
    println(mimeext.type_for_name("logo.png"))

    // What its first bytes say it is, for a resource fetched by a
    // browser. The answer is a code; `code_name` spells it.
    let head = bytes.from_str("\x89PNG\r\n\x1a\n")
    println(mimecode.code_name(mimesniff.sniff(head, MimeSniffBrowsing)))

    // Whether a request body is JSON. The comparison ignores the
    // parameters and the case.
    let header = "application/json; charset=utf-8"
    match mimetype.parse(header)
        Err(e) => println("bad Content-Type: ${e.message()}")
        Ok(m)  => println("json: ${mimetype.essence_eq(header, m, "application/json")}")

    // Which of this server's two answers the client would rather have.
    match mimeaccept.best("text/html;q=0.8, application/json", ["application/json", "text/html"])
        Some(i) => println("offer ${i}")
        None    => println("406: nothing on offer is acceptable")
```

Build and test with `novo pkg build` and `novo test`. Today `novo test`
fails on purpose: every test reaches a
`not implemented: mime-nv.<module>.<fn>` panic. The tests are the
specification the implementation will have to satisfy.

## What the package contains

| Module | Contents |
| --- | --- |
| `mimecode` | The well-known media types as integer codes, with the name, the default charset and two predicates for each. |
| `mimetype` | `type/subtype; param=value` parsed into ranges over the caller's string, the essence comparison, and the writer. |
| `mimeext` | The extension table, looked up from a name to a type and from a type to its extensions. |
| `mimesniff` | The WHATWG pattern table as a function of the bytes, the supplied type and the `nosniff` flag, and the same table as a `@value` state machine. |
| `mimeaccept` | `Accept` parsed into ranges, and the caller's own list of offers ranked against it. |

## How to choose an entry point

**`mimetype.parse` reads a header value.** The result is spans into
that string, so a request that only asks whether the body is JSON
copies nothing. `parse_bounded` refuses an input longer than a caller's
limit or with more parameters than it allows.

**`mimeext.type_for_name` answers what a file's name claims.** It is
the cheap question, and the only one a server has before it opens the
file.

**`mimesniff.sniff` answers what bytes say, with no supplied type.**
Use it for data with no `Content-Type` at all, such as a file off a
disk. **`sniff_with` is the browser's own question**, taking the bytes,
the supplied type and the `nosniff` flag. **`would_sniff` is what a
server asks about its own response** before it sends one.

**`mimeaccept.best` takes the header and the caller's offers** and
answers an index into the offers. `best_of` takes ranges already
parsed, for a caller answering several requests against one header.
`best_bounded` caps how many ranges it will parse.

**`mimecode` is the device path.** See "Running on a microcontroller".

## The rules a user needs

1. **Compare essences, not strings.** `mimetype.essence_eq` lowercases
   and drops the parameters and allocates nothing. A program that wrote
   `header == "text/html"` breaks the first time a server adds a
   charset.
2. **Parameters are a list, not a map.** RFC 2045 gives no uniqueness
   rule, and a `multipart/form-data` boundary must survive verbatim. A
   map would reorder them and drop a duplicate silently.
3. **Quoted strings are ordinary, not an edge case.**
   `boundary="---=_Part_0_1"` is the usual spelling, because a boundary
   contains characters a token may not.
4. **Sniffing is not "the bytes win".** A supplied type outside a named
   set is kept. The set is `text/plain`,
   `application/octet-stream`, `unknown/unknown`, `*/*`, and no type at
   all. `mimesniff.is_sniffable_type` answers the question on its own.

   | Supplied type | `nosniff` | Answer |
   | --- | --- | --- |
   | `text/plain` | no | the bytes decide |
   | `text/plain` | yes | `text/plain`; the bytes are not consulted |
   | `image/png` | no | `image/png`; not a sniffable type |

5. **Sniffing is a security mechanism.** A file a site lets a user
   upload can be made to run as HTML on that site's own origin: a `.txt`
   whose first bytes are `<!DOCTYPE html>`, served as `text/plain`,
   renders as a page in a browser that sniffs. `nosniff` is what stops
   that, and `mimecode.code_is_inline` answers whether a browser
   displays a type rather than downloading it.
6. **The name and the bytes are two answers, and this package
   reconciles neither.** An extension is evidence of what whoever named
   the file believed. Which answer to take depends on the caller: a
   server over its own content trusts the name, an upload endpoint
   trusts neither and pins a type of its own with `nosniff`, and an
   archiver wants both and reports a disagreement.
7. **The sniffing algorithm never looks past
   `mimesniff.header_bytes()` bytes**, which is 1445. A server reading
   a file to decide its type reads that many.
8. **Specificity is checked before quality.** RFC 9110 section 12.5.1
   orders by the most specific range first, then by `q`, then by the
   server's own order. `text/*;q=0.9, */*;q=1` means the client prefers
   anything textual and will take anything; a negotiator that ranked by
   `q` alone would serve it the first thing on its list.
9. **`q=0` is a refusal.** `*/*;q=0` means nothing is acceptable and
   `mimeaccept.best` answers `None`, which is a 406. An **empty**
   header is the opposite: anything is acceptable, and the server's
   first offer wins.
10. **A quality value is carried as thousandths.** `q=0.8` is 800 and
    an absent `q` is 1000. RFC 9110 section 12.4.2 allows at most three
    decimal places, and two floating-point values that should compare
    equal sometimes do not, which in a negotiator reorders two equally
    acceptable types.
11. **`mimeaccept.parse_accept` does not sort.** The order written is
    the final tie-break, so a parser that sorted would have thrown it
    away.
12. **Send `Vary: Accept` with a negotiated response.**
    `mimeaccept.vary_header()` is that value. Without it a shared cache
    stores a JSON response under a URL and hands it to the next client
    that asked for HTML.
13. **Type and subtype are compared ASCII case-insensitively**, which
    is the specification's own rule. The `charset` parameter's value is
    an ASCII label registered with IANA; what the label means is a
    decoder's business.

## Running on a microcontroller

novo-lang lets a package state which of its modules can run on a device
with no heap allocator, and the compiler checks that claim on every
build. Here the claim covers `mimecode` and the `@value` half of
`mimesniff`.

A firmware HTTP server answering `GET /logo.png` off a flash filesystem
needs the nine bytes `image/png` and cannot build a `MimeType`, which
holds ranges into a string a device with no heap does not have. The
device path is integers instead: a code from the extension or from the
first bytes, and `mimecode.code_name` at the end, producing a constant
that lives in flash.

```bash
novo build --target=nrf52-qemu tests/embedded_probe.nv
```

That command builds a Cortex-M4 executable today.

`MimeSniff` is the same table walk that `sniff` performs, as a `@value`
struct the caller carries. A device feeds it the bytes it is already
reading and stops when `sniff_settled` answers `true`, which for a PNG
is eight bytes rather than 1445. The suite checks that the two agree on
every vector.

The codes are functions returning integers rather than an enum. A
`@value` struct's fields are scalars only (SPEC section 14.5), and the
sniffer's state holds a code. A function returning a literal compiles
to the literal.

`mimetype`, `mimeext` and `mimeaccept` are outside the claim. A parsed
type is a list of parameter ranges, the extension table is several
hundred strings, and negotiation builds a ranked list.

## What is not included

- **Reading a file.** This package declares no effects and is handed
  the first bytes.
- **Charset decoding.** A charset name is a label here. Turning
  Windows-1252 bytes into text belongs to an encoding package.
- **Multipart bodies.** This package answers the `boundary` parameter.
  [form-nv](https://novo-lang.org/packages/form-nv) parses what it
  delimits.
- **The full context-specific sniffing tables.** The general table is
  implemented and `MimeSniffContext` is where the others attach. The
  image and audio-or-video tables are each a different table chosen by
  how the resource was requested.
- **`Content-Disposition`.** A different header with a different
  grammar, whose filename rules are RFC 6266's.
- **A mirror of the IANA media type registry.** It is thousands of
  types with its own update cadence, and a copy compiled in here would
  be stale the day it published.
- **A dependency on an HTTP package.** A `Content-Type` is a header
  value, which is a string. Which header it came out of belongs to
  whatever parsed the message.

## Related packages

- [form-nv](https://novo-lang.org/packages/form-nv) parses
  `multipart/form-data` bodies, and asks this package for the boundary.
- [static-nv](https://novo-lang.org/packages/static-nv) serves files
  over HTTP, and needs a type for each one.
- [http-codec-nv](https://novo-lang.org/packages/http-codec-nv) reads
  and writes HTTP/1.1 messages, and hands over the `Content-Type` and
  `Accept` values this package parses. This package does not depend on
  it.
- [html-nv](https://novo-lang.org/packages/html-nv) is what to parse a
  body with once this package has said it is HTML.
- `std.http_server` in the standard library answers a media type from a
  file extension with a twenty-branch match, and has no parser, no
  sniffer and no negotiation.

## Tests

```bash
novo test tests/mimetype_tests.nv    # the grammar, the essence, the extension table
novo test tests/mimesniff_tests.nv   # the pattern table, nosniff, and Accept
```

The pattern table, its order, the sniffable-type set and the `nosniff`
rule are the WHATWG MIME Sniffing Standard's own. The extension table
is Apache's `mime.types` by way of the Rust crate `mime_guess`; taking
somebody else's list matters because a curated one disagrees with the
server in front of it. Python's `mimetypes` is the reference for the
two-way lookup. The grammar is RFC 2045 section 5.1, the `+suffix` is
RFC 6839, and the negotiation examples are RFC 9110 section 12.5.1's.

The suite asserts that `text/html` and `TEXT/HTML; charset=utf-8` have
one essence, that a quoted boundary survives verbatim, that a duplicate
parameter is kept, that a supplied `image/png` is not overridden by
sniffing, that `nosniff` suppresses sniffing entirely, that
specificity beats quality, that `q=0` is a refusal and an empty header
is not, and that the `@value` sniffer and `sniff` agree on every
vector.

`tests/embedded_probe.nv` is the device claim as a program. It builds a
Cortex-M4 executable against `mimecode` and the `@value` sniffer.

The tests compile today and fail at run, each on the
`not implemented: mime-nv.<module>.<fn>` panic that is its body. That
is the expected state of an interface release. They turn green one at a
time as bodies land.

## Implementation status

| Item | Implemented |
| --- | --- |
| `mimetype.MimeSpan`, `.MimeParam`, `.MimeType`, `.MimeError`, `mimesniff.MimeSniffContext`, `.MimeSniff`, `mimeaccept.MimeRange` | the types are declared |
| `mimecode.unknown` and the twenty named code functions | no |
| `mimecode.code_name`, `.code_named`, `.code_charset`, `.code_is_inline`, `.code_is_text`, `.code_count`, `.code_at` | no |
| `mimetype.parse`, `.parse_bounded`, `.print`, `.build` | no |
| `mimetype.type_of`, `.subtype_of`, `.suffix_of`, `.essence`, `.essence_eq`, `.span_str` | no |
| `mimetype.param`, `.param_str`, `.charset`, `.boundary` | no |
| `mimetype.token_byte_ok`, `.needs_quoting`, `.quote`, `.unquote`, `MimeError.message` | no |
| `mimeext.code_for_ext`, `.type_for_ext`, `.type_for_name`, `.code_for_name`, `.ext_of`, `.knows_ext` | no |
| `mimeext.exts_for_type`, `.preferred_ext`, `.ext_count`, `.ext_at` | no |
| `mimesniff.header_bytes`, `.sniff`, `.sniff_with`, `.would_sniff`, `.is_sniffable_type` | no |
| `mimesniff.looks_binary`, `.bom_charset`, `.bom_len` | no |
| `mimesniff.context_code`, `.sniff_start`, `.sniff_byte`, `.sniff_end` | no |
| `mimesniff.sniff_settled`, `.sniff_code`, `.sniff_binary`, `.sniff_pos` | no |
| `mimeaccept.parse_accept`, `.best`, `.best_bounded`, `.best_of` | no |
| `mimeaccept.quality_of`, `.range_matches`, `.specificity`, `.range_of` | no |
| `mimeaccept.print_range`, `.print_accept`, `.vary_header` | no |

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
