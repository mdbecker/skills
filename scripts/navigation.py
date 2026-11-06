"""Development-only navigation parsing, validation and destination relocation."""

from pathlib import Path
from collections import Counter
from functools import lru_cache
from html.parser import HTMLParser
from html import unescape
import posixpath
import re
from urllib.parse import quote, unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.rules_inline.link import link
from markdown_it.rules_inline.image import image
from markdown_it.rules_inline.html_inline import html_inline
from distribution.install import resolve_link_target as resolve_target

def _capture(original, token_type):
    def rule(state, silent):
        start = state.pos
        count = len(state.tokens)
        label_start = start + (1 if token_type == 'image' else 0)
        label_end = state.md.helpers.parseLinkLabel(state, label_start, True) if token_type != 'html_inline' else -1
        result = original(state, silent)
        if result and not silent:
            for token in state.tokens[count:]:
                if token.type != token_type:
                    continue
                token.meta['source_start'] = start
                token.meta['source_end'] = state.pos
                token.meta['destination'] = None
                if label_end >= 0 and state.src[label_end + 1:label_end + 2] == '(' and 'label' not in token.meta:
                    position = label_end + 2
                    while position < len(state.src) and state.src[position].isspace():
                        position += 1
                    parsed = state.md.helpers.parseLinkDestination(state.src, position, len(state.src))
                    if parsed.ok:
                        token.meta['destination'] = (position + (state.src[position:position + 1] == '<'),
                                                     parsed.pos - (state.src[position:position + 1] == '<'))
                break
        return result
    return rule


def _positions(content, text, start, end):
    position = text.find(content, start, end)
    if position >= 0:
        return list(range(position, position + len(content))) + [position + len(content)]
    normalized = []
    locations = []
    cursor = start
    while cursor < end:
        if text[cursor:cursor + 2] == '\\|':
            cursor += 1
        normalized.append(text[cursor])
        locations.append(cursor)
        cursor += 1
    position = ''.join(normalized).find(content)
    if position >= 0:
        selected = locations[position:position + len(content)]
        return selected + [selected[-1] + 1 if selected else start]
    result = []
    cursor = start
    for part in content.splitlines(keepends=True):
        body = part.rstrip('\r\n')
        position = text.find(body, cursor, end)
        if position < 0:
            raise ValueError('Cannot safely locate parsed Markdown source span')
        result.extend(range(position, position + len(body)))
        cursor = position + len(body)
        if part.endswith('\n'):
            newline = text.find('\n', cursor, end)
            if newline < 0:
                raise ValueError('Cannot safely locate Markdown newline')
            result.append(newline)
            cursor = newline + 1
    return result + [cursor]


class _HTMLNavigation(HTMLParser):
    def __init__(self, content, positions, edges, anchors):
        super().__init__(convert_charrefs=True)
        self.content = content
        self.positions = positions
        self.edges = edges
        self.anchors = anchors
        self.lines = [0]
        for match in re.finditer('\n', content):
            self.lines.append(match.end())

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get('id'):
            self.anchors.add(attributes['id'])
        raw = self.get_starttag_text()
        line, column = self.getpos()
        base = self.lines[line - 1] + column
        position = re.match(r'<\s*[^\s/>]+', raw).end()
        seen = set()
        while position < len(raw):
            while position < len(raw) and raw[position].isspace():
                position += 1
            if position >= len(raw) or raw[position] in '/>':
                break
            start = position
            while position < len(raw) and not raw[position].isspace() and raw[position] not in '=/>':
                position += 1
            name = raw[start:position].lower()
            if not name:
                raise ValueError('Malformed HTML attribute')
            while position < len(raw) and raw[position].isspace():
                position += 1
            if position >= len(raw) or raw[position] != '=':
                continue
            position += 1
            while position < len(raw) and raw[position].isspace():
                position += 1
            delimiter = raw[position] if position < len(raw) and raw[position] in '\"\x27' else None
            if delimiter:
                position += 1
            value_start = position
            while position < len(raw) and (raw[position] != delimiter if delimiter else not raw[position].isspace() and raw[position] != '>'):
                position += 1
            value_end = position
            if delimiter:
                if position >= len(raw):
                    raise ValueError('Unterminated HTML attribute')
                position += 1
            if name not in {'href', 'src'}:
                continue
            if name in seen:
                raise ValueError('Duplicate HTML navigation attribute')
            seen.add(name)
            span = (self.positions[base + value_start], self.positions[base + value_end])
            self.edges.append({'target': unescape(raw[value_start:value_end]), 'span': span})

    handle_startendtag = handle_starttag


@lru_cache(maxsize=256)
def markdown_navigation(text):
    masked = text
    frontmatter = re.match(r'\A---\r?\n.*?\r?\n---(?:\r?\n|$)', text, re.S)
    if frontmatter:
        masked = ''.join(character if character in '\r\n' else ' ' for character in frontmatter.group()) + text[frontmatter.end():]
    parser = MarkdownIt('commonmark', {'html': True, 'store_labels': True}).enable('table')
    parser.normalizeLink = lambda target: target
    parser.validateLink = lambda target: True
    parser.inline.ruler.at('link', _capture(link, 'link_open'))
    parser.inline.ruler.at('image', _capture(image, 'image'))
    parser.inline.ruler.at('html_inline', _capture(html_inline, 'html_inline'))
    environment = {}
    tokens = parser.parse(masked, environment)
    offsets = [0]
    offsets.extend(match.end() for match in re.finditer('\n', text))
    offsets.append(len(text))
    edges = []
    anchors = set()
    counts = Counter()
    cursors = {}
    for number, block in enumerate(tokens):
        if block.type not in {'inline', 'html_block'}:
            continue
        start_line, end_line = block.map or (0, len(offsets) - 2)
        start = max(offsets[start_line], cursors.get(start_line, 0))
        positions = _positions(block.content, text, start, offsets[min(end_line, len(offsets) - 1)])
        cursors[start_line] = positions[-1]
        if block.type == 'html_block':
            _HTMLNavigation(block.content, positions, edges, anchors).feed(block.content)
            continue
        if number and tokens[number - 1].type == 'heading_open':
            heading = ''.join(token.content for token in block.children or [] if token.type in {'text', 'code_inline', 'image'})
            slug = re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-')
            suffix = counts[slug]
            candidate = slug if not suffix else f'{slug}-{suffix}'
            while candidate in anchors:
                suffix += 1
                candidate = f'{slug}-{suffix}'
            counts[slug] = suffix + 1
            anchors.add(candidate)
        for token in block.children or []:
            if token.type == 'html_inline':
                base = token.meta['source_start']
                _HTMLNavigation(token.content, positions[base:], edges, anchors).feed(token.content)
            if token.type not in {'link_open', 'image'}:
                continue
            target = token.attrGet('href' if token.type == 'link_open' else 'src')
            span = token.meta.get('destination')
            if span is not None:
                span = (positions[span[0]], positions[span[1]])
            elif token.meta.get('label') in environment.get('references', {}):
                reference = environment['references'][token.meta['label']]
                first, last = reference['map']
                fragment = text[offsets[first]:offsets[last]]
                definition = re.search(r'\[[^\n]*?\]:\s*', fragment)
                if definition is None:
                    raise ValueError('Cannot safely locate Markdown reference definition')
                position = offsets[first] + definition.end()
                parsed = parser.helpers.parseLinkDestination(text, position, offsets[last])
                if not parsed.ok:
                    raise ValueError('Cannot safely locate reference destination')
                angle = text[position:position + 1] == '<'
                span = (position + angle, parsed.pos - angle)
            edges.append({'target': target, 'span': span, 'line': start_line + 1})
    for edge in edges:
        edge['line'] = text.count('\n', 0, edge['span'][0]) + 1 if edge['span'] else edge.get('line', 1)
    return edges, anchors


def validate_documents(files):
    errors = []
    for source, content in files.items():
        if Path(source).suffix.lower() not in {'.md', '.markdown'}:
            continue
        try:
            edges, unused_anchors = markdown_navigation(content.decode('utf-8'))
            for edge in edges:
                target, fragment = resolve_target(source, edge['target'])
                if target is None:
                    continue
                prefix = '/'.join(source.split('/')[:2]) + '/' if source.startswith('skills/') else ''
                if prefix and not target.startswith(prefix):
                    raise ValueError('Package link escapes its owning skill')
                if target not in files:
                    raise ValueError('Missing declared package member')
                if fragment and fragment not in markdown_navigation(files[target].decode('utf-8'))[1]:
                    raise ValueError('Missing target anchor')
        except (ValueError, UnicodeError, KeyError) as error:
            errors.append(f'{source}: {error}')
    return errors


def relocate_markdown(text, source, destination, mapping):
    replacements = {}
    for edge in markdown_navigation(text)[0]:
        target, unused_fragment = resolve_target(source, edge['target'])
        if target is None or not urlsplit(edge['target']).path:
            continue
        if target not in mapping or edge['span'] is None:
            raise ValueError(f'{source}: unmapped or unlocatable local export dependency')
        parsed = urlsplit(edge['target'])
        relative = quote(posixpath.relpath(mapping[target], posixpath.dirname(destination)), safe='/._-~@')
        relative += ('?' + parsed.query if parsed.query else '') + ('#' + parsed.fragment if parsed.fragment else '')
        replacements[edge['span']] = relative
    for (start, end), replacement in sorted(replacements.items(), reverse=True):
        text = text[:start] + replacement + text[end:]
    return text
