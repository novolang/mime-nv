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
`Content-Type` wrong. The WHATWG standard fixes a table of byte
patterns, the order in which it is consulted, and, for each supplied
type, whether the bytes may change it at all. The response header
`X-Content-Type-Options: nosniff` sets the standard's **no-sniff
flag**, which keeps a supplied type as it is.

An **`Accept` header** is a client's list of media **ranges** with
optional quality values, such as `text/html;q=0.8, application/json`. A
range may use `*` for the subtype or for both parts. The quality value
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

    // What its first bytes say it is, for a resource with no type.
    // The answer is a code; `code_name` spells it.
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

## What the package contains

| Module | Contents |
| --- | --- |
| `mimecode` | The well-known media types as integer codes, with the name, the default charset and two predicates for each. |
| `mimetype` | `type/subtype; param=value` parsed into ranges over the caller's string, the essence comparison, and the writer. |
| `mimeext` | The extension table, looked up from a name to a type and from a type to its extensions. |
| `mimesniff` | The WHATWG sniffing algorithm as a function of the bytes, the supplied type and the no-sniff flag. |
| `mimesniff_core` | The pattern tables as a `@value` state fed one byte at a time, which `mimesniff` runs and a microcontroller can run. |
| `mimeaccept` | `Accept` parsed into ranges, and the caller's own list of offers ranked against it. |

## How to choose an entry point

**`mimetype.parse` reads a header value.** The result is spans into
that string, so a request that only asks whether the body is JSON
copies nothing. `parse_bounded` refuses an input longer than a caller's
limit or with more parameters than it allows.

**`mimeext.type_for_name` answers what a file's name claims.** It is
the cheap question, and the only one a server has before it opens the
file. `preferred_ext` answers the other way, for a file about to be
written.

**`mimesniff.sniff` answers what bytes say, with no supplied type.**
Use it for data with no `Content-Type` at all, such as a file off a
disk. **`sniff_with` is the browser's own question**, taking the bytes,
the supplied type and the no-sniff flag. **`would_sniff` is what a
server asks about its own response** before it sends one.

**`mimesniff_core` is the same walk a byte at a time**, for a caller
with no buffer. It answers as soon as the prefix decides, which for a
PNG is after eight bytes.

**`mimeaccept.best` takes the header and the caller's offers** and
answers an index into the offers. `best_of` takes ranges already
parsed, for a caller answering several requests against one header.
`best_bounded` caps how many ranges it will read.

## The rules a user needs

1. **Compare essences, not strings.** `mimetype.essence_eq` lowercases
   and drops the parameters and allocates nothing. A program that wrote
   `header == "text/html"` breaks the first time a server adds a
   charset.
2. **Parameters are a list, not a map.** RFC 2045 gives no uniqueness
   rule, and a `multipart/form-data` boundary must survive verbatim. A
   repeated parameter is kept, and `param` answers the first.
3. **Quoted strings are ordinary, not an edge case.**
   `boundary="---=_Part_0_1"` is the usual spelling, because a boundary
   contains characters a token may not.
4. **Sniffing is not "the bytes win".** The supplied type decides what
   the bytes may change (MIME Sniffing Standard section 7):

   | Supplied type | no-sniff | Answer |
   | --- | --- | --- |
   | none, `unknown/unknown`, `application/unknown`, `*/*` | unset | the whole table, HTML included |
   | the same | set | the table without the HTML, XML and PDF rows |
   | `text/html`, `text/xml`, `application/xml`, any `+xml` | either | the supplied type |
   | `text/plain`, as an old Apache server writes it | unset | `text/plain`, or `application/octet-stream` for binary bytes |
   | an `image/*` type | unset | the image the bytes are, or the supplied type |
   | an `audio/*` or `video/*` type | unset | the audio or video the bytes are, or the supplied type |
   | any other type, or any type with no-sniff set | | the supplied type |

   `mimesniff.is_sniffable_type` answers whether a supplied type counts
   as none, and `would_sniff` whether the bytes are read at all.
5. **Sniffing never turns `text/plain` into HTML.** The standard's
   text-or-binary rules answer only `text/plain` or
   `application/octet-stream` (section 7.2). The danger is a response
   with no type or an unknown one: a user upload served that way whose
   first bytes are `<!DOCTYPE html>` renders as a page on the site's
   own origin. Serve uploads with a real type and `nosniff`.
   `mimecode.code_is_inline` answers whether a browser displays a type
   rather than downloading it.
6. **An answer is a code.** When the answer is a supplied type that
   `mimecode` has no code for, `sniff_with` answers
   `mimecode.unknown()`. A caller that gets `false` from `would_sniff`
   keeps its own string.
7. **The name and the bytes are two answers, and this package
   reconciles neither.** An extension is evidence of what whoever named
   the file believed. Which answer to take depends on the caller: a
   server over its own content trusts the name, an upload endpoint
   trusts neither and pins a type of its own with `nosniff`, and an
   archiver wants both and reports a disagreement.
8. **The sniffing algorithm never looks past
   `mimesniff.header_bytes()` bytes**, which is 1445 (section 5.2). A
   server reading a file to decide its type reads that many.
9. **An empty resource sniffs as `text/plain`**, because it holds no
   binary byte (section 7.1).
10. **The most specific range sets an offer's quality, and the highest
    quality wins.** RFC 9110 section 12.5.1: for `text/html` the range
    `text/html` outranks `text/*`, which outranks `*/*`, whatever their
    `q` values, and the quality of the range that applies is the
    offer's quality. Offers of equal quality are taken in the server's
    order. `text/*;q=0.9, */*;q=1` therefore ranks JSON above HTML.
11. **`q=0` is a refusal.** `*/*;q=0` means nothing is acceptable and
    `mimeaccept.best` answers `None`, which is a 406. An **empty**
    header is the opposite: anything is acceptable, and the server's
    first offer wins.
12. **A quality value is carried as thousandths.** `q=0.8` is 800 and
    an absent `q` is 1000. RFC 9110 section 12.4.2 allows at most three
    decimal places, and two floating-point values that should compare
    equal sometimes do not, which in a negotiator reorders two equally
    acceptable types.
13. **Send `Vary: Accept` with a negotiated response.**
    `mimeaccept.vary_header()` is that value. Without it a shared cache
    stores a JSON response under a URL and hands it to the next client
    that asked for HTML.

## Running on a microcontroller

`mimecode` and `mimesniff_core` build for a microcontroller with no
heap allocator. Every function in them carries `@tier(embedded)`, so
the compiler refuses an allocation written there.

A firmware HTTP server answering `GET /logo.png` off a flash filesystem
needs the nine bytes `image/png` and cannot build a `MimeType`, which
holds ranges into a string. The device path is integers instead: a code
from the first bytes, and `mimecode.code_name` at the end, a constant
that lives in flash.

`MimeSniff` is the table walk as a `@value` struct the caller carries.
A device feeds it the bytes it is already reading and stops when
`sniff_settled` answers `true`. `mimesniff.sniff` is the same walk fed
from a buffer, so the host and the device answer from one table.

```bash
novo build --target=nrf52-qemu tests/embedded_probe.nv
```

That command builds a Cortex-M4 executable, and under
`qemu-system-arm -machine mps2-an386` it prints
`PASS: mime-embedded` after fifteen checks. `tests/alloc_scan.sh`
reads the emitted LLVM and checks that no function in the two modules
calls the allocator.

`mimetype`, `mimeext`, `mimesniff` and `mimeaccept` are outside the
claim. They take `Str` and `Bytes`, which the embedded runtime does not
define, and a parsed type, the extension table and a negotiation all
build lists.

## What is not included

- **Reading a file.** This package declares no effects and is handed
  the first bytes.
- **The MP3-without-ID3 signature** (MIME Sniffing Standard section
  6.2.3). As written it compares the frame size with `s - length`,
  which is never positive, so it never matches. An MP3 with an ID3 tag
  is recognised.
- **The font, plugin, style, script, text track and cache manifest
  contexts** (sections 8.4 to 8.9). Each is chosen by how a browser
  requested the resource, and all but the font context keep the
  supplied type.
- **Charset decoding.** A charset name is a label here. Turning
  Windows-1252 bytes into text belongs to an encoding package.
- **Multipart bodies.** This package answers the `boundary` parameter.
  [form-nv](https://novo-lang.org/packages/form-nv) parses what it
  delimits.
- **`Content-Disposition`.** A different header with a different
  grammar, whose filename rules are RFC 6266's.
- **`Accept-Encoding`, `Accept-Language` and `Accept-Charset`.** Their
  elements are not media ranges.
- **A mirror of the IANA media type registry.** It is thousands of
  types with its own update cadence.
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
novo test tests/mimetype_tests.nv      # the grammar, the essence, the printer
novo test tests/mimecode_tests.nv      # the codes and their names
novo test tests/mimeext_tests.nv       # the extension table, every entry
novo test tests/mimesniff_tests.nv     # the pattern tables, the supplied type, nosniff
novo test tests/mimeaccept_tests.nv    # Accept and negotiation
novo test tests/differential_tests.nv  # against Python's email and mimetypes
bash tests/coverage.sh                 # line coverage over src/
bash tests/alloc_scan.sh               # no allocation in the device modules
```

The sniffing vectors are the MIME Sniffing Standard's own rows, one
resource per row, plus the cases where two rows compete and the order
decides. The negotiation vectors are RFC 9110 section 12.5.1's
examples. Its quality table gives `text/html;level=3` the value 0.7,
which the rule stated above the table does not; the suite asserts 0.3,
the rule's answer.

The extension table is the Rust crate `mime_guess`'s, and
`tools/ext_table.py` writes it into `src/mimeext.nv` from a pinned
commit. `tools/differential.py` writes `tests/differential_tests.nv`
from Python's standard library: the essence, charset and boundary its
`email` package reads from twenty headers, the type its `mimetypes`
gives the 118 extensions on which the two tables agree, and the
extension it prefers for 83 types. The 30 extensions on which they
disagree are listed in that file.

## Licence

Apache-2.0. See `LICENSE`. The extension table is taken from
`mime_guess`, which is MIT-licensed.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
