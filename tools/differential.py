#!/usr/bin/env python3
"""Write tests/differential_tests.nv from Python's standard library.

Two independent implementations answer the same questions this package
does, and the file this script writes holds their answers as vectors:

1. The `email` package parses a `Content-Type` value.  For each header
   below, its essence, its charset and its boundary are recorded.
2. `mimetypes`, with its built-in map only, maps an extension to a
   type, and a type to the extension it prefers.  The extensions on which it agrees with mime_guess's table
   are recorded.  Where the two tables disagree, the disagreement is
   listed in the file's header comment and not asserted, because the
   table this package ships is mime_guess's.

Run from the package root:  python3 tools/differential.py
The output is passed through `novo fmt`.
"""
import email.message
import mimetypes
import re
import subprocess

HEADERS = [
    'text/html',
    'TEXT/HTML',
    'text/html; charset=utf-8',
    'text/html; charset=UTF-8',
    'text/html;charset=ISO-8859-1',
    'text/html ;  charset="utf-8"',
    'text/plain; format=flowed; charset=us-ascii',
    'application/json',
    'application/vnd.api+json; charset=utf-8',
    'image/svg+xml',
    'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW',
    'multipart/form-data; boundary="---=_Part_0_1"',
    'multipart/mixed; boundary="simple boundary"',
    'multipart/alternative; boundary="a\\"b"',
    'Multipart/Related; boundary=xyz; type="text/html"',
    'text/plain; charset=utf-8; charset=latin1',
    'message/rfc822',
    'application/octet-stream',
    'text/csv; header=present; charset=utf-8',
    'application/x-www-form-urlencoded',
]


def nv(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$') + '"'


def email_vectors():
    out = []
    for h in HEADERS:
        m = email.message.Message()
        m['Content-Type'] = h
        out.append((h, m.get_content_type(), m.get_content_charset() or '',
                    m.get_boundary() or ''))
    return out


def table_rows():
    src = open('src/mimeext.nv').read()
    body = src[src.index('fn entry_ext'):]
    exts = dict(re.findall(r'^\s+(\d+)\s+=> "([^"]*)"$', body[:body.index('fn entry_types')], re.M))
    types = dict(re.findall(r'^\s+(\d+)\s+=> "([^"]*)"$',
                            body[body.index('fn entry_types'):body.index('fn preferred_of')], re.M))
    return [(exts[k], types[k].split(',')) for k in sorted(exts, key=int)]


def main():
    oracle = mimetypes.MimeTypes(filenames=())
    agree, differ = [], []
    rows = table_rows()
    by_type = {}
    for ext, types in rows:
        for t in types:
            by_type.setdefault(t.lower(), []).append(ext)
    preferred = []
    for t, exts in sorted(by_type.items()):
        g = oracle.guess_extension(t, strict=False)
        if g and g[1:] in exts:
            preferred.append((t, g))
    for ext, types in rows:
        ours = types[0]
        theirs = oracle.guess_type('x.' + ext, strict=False)[0]
        if theirs is None:
            continue
        (agree if theirs == ours else differ).append((ext, ours, theirs))
    lines = [
        '// differential_tests.nv — this package against Python\'s standard',
        '// library, which answers the same questions independently.',
        '//',
        '// Written by tools/differential.py; do not edit by hand.  The',
        '// `email` package supplies the essence, charset and boundary of each',
        '// header, and `mimetypes`, with its built-in map only, the type of',
        '// each extension both tables know.',
        '//',
        '// The two extension tables disagree on %d extensions, which are not' % len(differ),
        '// asserted.  This package answers mime_guess\'s type; Python\'s is second:',
        '//',
    ]
    for ext, ours, theirs in differ:
        lines.append('//   .%-8s %-32s %s' % (ext, ours, theirs))
    lines += ['', 'use std.test', 'use mimeext', 'use mimetype', '',
              '// Each header, and what Python\'s `email` package answers for it:',
              '// the essence, the charset, and the boundary.',
              'fn headers() -> [(Str, Str, Str, Str)]',
              '    [']
    for h, e, c, b in email_vectors():
        lines.append('        (%s, %s, %s, %s),' % (nv(h), nv(e), nv(c), nv(b)))
    lines[-1] = lines[-1].rstrip(',')
    lines += ['    ]', '',
              '// Each extension on which the two tables agree, with its type.',
              'fn extensions() -> [(Str, Str)]',
              '    [']
    for ext, ours, _ in agree:
        lines.append('        (%s, %s),' % (nv(ext), nv(ours)))
    lines[-1] = lines[-1].rstrip(',')
    lines += ['    ]', '',
              '// Each type whose preferred extension Python names, where the name',
              '// is one the table lists for the type.',
              'fn preferred() -> [(Str, Str)]',
              '    [']
    for t, g in preferred:
        lines.append('        (%s, %s),' % (nv(t), nv(g)))
    lines[-1] = lines[-1].rstrip(',')
    lines += ['    ]', '',
              '@test',
              'fn test_the_email_package_reads_each_header_the_same_way() [io]',
              '    for (h, essence, charset, boundary) in headers()',
              '        test.case(h)',
              '        match mimetype.parse(h)',
              '            Ok(m)  =>',
              '                test.assert(mimetype.essence(h, m) == essence)',
              '                test.assert(mimetype.charset(h, m) == charset)',
              '                test.assert(mimetype.boundary(h, m) == boundary)',
              '            Err(_) =>',
              '                test.assert(false)',
              '',
              '@test',
              'fn test_mimetypes_agrees_on_the_extensions_both_tables_know() [io]',
              '    test.case("%d extensions" )' % len(agree),
              '    for (ext, t) in extensions()',
              '        test.assert(mimeext.type_for_ext(ext) == t)',
              '',
              '@test',
              'fn test_mimetypes_prefers_the_same_extension() [io]',
              '    test.case("%d types")' % len(preferred),
              '    for (t, ext) in preferred()',
              '        test.assert(mimeext.preferred_ext(t) == ext)',
              '']
    path = 'tests/differential_tests.nv'
    open(path, 'w').write('\n'.join(lines))
    subprocess.run(['novo', 'fmt', path], check=True, capture_output=True)
    print('%d headers, %d extensions agreeing, %d differing, %d preferred -> %s'
          % (len(HEADERS), len(agree), len(differ), len(preferred), path))


if __name__ == '__main__':
    main()
