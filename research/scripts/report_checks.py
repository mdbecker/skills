"""Bounded checks for a mapped saved-evidence report, not a reporting pipeline."""

import ast
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET


class ReportCheckError(ValueError):
    pass


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def same_evidence(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_evidence(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(same_evidence(first, second) for first, second in zip(left, right))
    return left == right


def bounded_path(root, relative):
    root = Path(root).absolute()
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ReportCheckError('Expected a project-relative path')
    path = root / relative
    if root.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ReportCheckError('Path escapes project or uses a symlink')
    if any(part.is_symlink() for part in (path, *path.parents) if part.is_relative_to(root)):
        raise ReportCheckError('Symlinks are not report inputs or outputs')
    if path.exists() and not path.is_file():
        raise ReportCheckError('Expected a regular file')
    return path


def source_value(root, source):
    required = {'artifact', 'version', 'sha256', 'locator'}
    if not isinstance(source, dict) or not required <= source.keys():
        raise ReportCheckError('Source needs artifact, version, full hash and locator')
    if not source['version'] or not re.fullmatch(r'[0-9a-f]{64}', source['sha256']):
        raise ReportCheckError('Source version or full SHA-256 is missing')
    path = bounded_path(root, source['artifact'])
    if not path.is_file():
        raise ReportCheckError(f'Missing source: {source["artifact"]}')
    content = path.read_bytes()
    if sha256(content) != source['sha256']:
        raise ReportCheckError(f'Source hash mismatch: {source["artifact"]}')
    locator = source['locator']
    if not isinstance(locator, str) or not locator.startswith('/'):
        raise ReportCheckError('This checker requires a precise saved JSON pointer')
    try:
        value = json.loads(content)
        for token in locator[1:].split('/'):
            token = token.replace('~1', '/').replace('~0', '~')
            value = value[int(token)] if isinstance(value, list) else value[token]
        return value
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise ReportCheckError(f'Unavailable JSON source locator: {locator}') from error


LEDGER_FIELDS = {'id', 'source', 'cohort', 'selection', 'unit', 'denominator',
                 'derivation', 'value', 'status', 'editable_source', 'output_location',
                 'permitted_change', 'verification'}
PROTECTED_FIELDS = {'source', 'cohort', 'selection', 'unit', 'denominator',
                    'derivation', 'value', 'status'}
OPERATIONAL_FIELDS = {'editable_source', 'output_location', 'permitted_change', 'verification'}
STATUSES = {'exact', 'reconstructed', 'suppressed', 'unavailable', 'disputed'}


def validate_ledger(ledger, root):
    identities = set()
    for entry in ledger:
        if not isinstance(entry, dict) or not LEDGER_FIELDS <= entry.keys():
            raise ReportCheckError('Incomplete evidence ledger entry')
        if not entry['id'] or entry['id'] in identities:
            raise ReportCheckError('Missing or duplicate claim identity')
        identities.add(entry['id'])
        if entry['status'] not in STATUSES:
            raise ReportCheckError('Unknown evidence status')
        for field in ('cohort', 'selection', 'unit', 'derivation', 'editable_source',
                      'output_location', 'permitted_change'):
            if not entry[field]:
                raise ReportCheckError(f'Missing evidence meaning: {field}')
        if type(entry['denominator']) is not int or entry['denominator'] <= 0:
            raise ReportCheckError('Denominator must be an explicit positive count')
        value = entry['value']
        if entry['status'] == 'suppressed' and (not isinstance(value, str) or not value.strip()):
            raise ReportCheckError('Suppressed cells must remain nonnumeric')
        if entry['status'] == 'unavailable' and value is not None:
            raise ReportCheckError('Unavailable intersections cannot be derived')
        if entry['status'] in {'exact', 'reconstructed'}:
            if type(value) not in {int, float} or not math.isfinite(value):
                raise ReportCheckError('Exact/reconstructed cells need saved finite numbers')
            if value < 0 or value > entry['denominator']:
                raise ReportCheckError('Count is outside its row-specific denominator')
            if re.search(r'bar[- ]height|estimated|subtraction|marginal', entry['derivation'], re.I):
                raise ReportCheckError('Unsupported quantitative reconstruction')
        saved = source_value(root, entry['source'])
        if not same_evidence(saved, value):
            raise ReportCheckError(f'Saved evidence does not support {entry["id"]}')
    return {entry['id']: entry for entry in ledger}


def compare_ledger(before, after, root, corrections=()):
    original = validate_ledger(before, root)
    revised = validate_ledger(after, root)
    if original.keys() != revised.keys():
        raise ReportCheckError('Claims or figures were silently added or omitted')
    authorized = {}
    for correction in corrections:
        identity = correction.get('id')
        if identity not in original or identity in authorized:
            raise ReportCheckError('Unknown or duplicate correction authorization')
        if not same_evidence(correction.get('before_value'), original[identity]['value']):
            raise ReportCheckError('Correction does not match the protected baseline')
        saved = source_value(root, correction.get('source'))
        if not same_evidence(saved, correction.get('after_value')):
            raise ReportCheckError('Correction lacks supplied saved supporting evidence')
        if original[identity]['status'] not in {'exact', 'reconstructed'}:
            raise ReportCheckError('A correction cannot recover suppressed/unavailable evidence')
        authorized[identity] = correction
    for identity, entry in original.items():
        expected = {field: value for field, value in entry.items() if field not in OPERATIONAL_FIELDS}
        if identity in authorized:
            expected.update(value=authorized[identity]['after_value'],
                            source=authorized[identity]['source'])
        actual = {field: value for field, value in revised[identity].items() if field not in OPERATIONAL_FIELDS}
        if not same_evidence(expected, actual):
            raise ReportCheckError(f'Unauthorized protected value or meaning change: {identity}')


def disclosure_policy(policy):
    for field in ('min_observations', 'min_subjects'):
        if type(policy.get(field)) is not int or policy[field] <= 0:
            raise ReportCheckError('Both observation and distinct-subject thresholds are required')
    if type(policy.get('round_digits')) is not int or not 0 <= policy['round_digits'] <= 8:
        raise ReportCheckError('Explicit centroid rounding is required')
    if set(policy.get('permitted_fields', ())) != {'count', 'centroid'}:
        raise ReportCheckError('Only approved counts and rounded centroids can be published')
    if policy.get('complementary_disclosure') != 'withhold-partition':
        raise ReportCheckError('Complementary-disclosure policy must be mapped explicitly')


def aggregate_spatial(observations, policy):
    disclosure_policy(policy)
    records = []
    for observation in observations:
        if not isinstance(observation, dict) or not observation.get('subject'):
            raise ReportCheckError('Private subject identity is needed for diversity accounting')
        coordinates = observation.get('coordinates')
        if not isinstance(coordinates, (list, tuple)) or len(coordinates) != 2:
            raise ReportCheckError('This adapter supports mapped two-dimensional coordinates')
        if any(type(value) not in {int, float} or not math.isfinite(value) for value in coordinates):
            raise ReportCheckError('Coordinates must be finite numbers')
        if not isinstance(observation['subject'], str):
            raise ReportCheckError('Subject identities must be stable strings')
        records.append((tuple(coordinates), observation['subject']))
    records.sort()

    def publishable(group):
        return (len(group) >= policy['min_observations'] and
                len({subject for coordinates, subject in group}) >= policy['min_subjects'])

    if not records or not publishable(records):
        return []

    def partition(group):
        spans = [max(point[dimension] for point, subject in group) -
                 min(point[dimension] for point, subject in group) for dimension in range(2)]
        dimension = max(range(2), key=lambda index: (spans[index], -index))
        ordered = sorted(group, key=lambda item: (item[0][dimension], item[0], item[1]))
        middle = len(ordered) // 2
        left, right = ordered[:middle], ordered[middle:]
        if spans[dimension] > 0 and publishable(left) and publishable(right):
            return partition(left) + partition(right)
        centroid = [round(math.fsum(point[index] for point, subject in ordered) / len(ordered),
                          policy['round_digits']) for index in range(2)]
        return [{'count': len(ordered), 'centroid': centroid}]

    return partition(records)


def validate_spatial(observations, groups, policy):
    if not isinstance(groups, list) or any(not isinstance(group, dict) or
                                          set(group) != {'count', 'centroid'} for group in groups):
        raise ReportCheckError('Record-level or unapproved aggregate output fields')
    if not same_evidence(groups, aggregate_spatial(observations, policy)):
        raise ReportCheckError('Aggregate accounting, diversity, rounding or input identity changed')


def literal_assignment(source, name):
    try:
        tree = ast.parse(source)
        matches = []
        for statement in tree.body:
            targets = statement.targets if isinstance(statement, ast.Assign) else (
                [statement.target] if isinstance(statement, ast.AnnAssign) else [])
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                matches.append(statement.value)
        if len(matches) != 1:
            raise ReportCheckError('Need one unambiguous saved top-level literal assignment')
        return ast.literal_eval(matches[0])
    except (SyntaxError, ValueError, TypeError) as error:
        raise ReportCheckError('Saved assignment is not a literal; never execute it') from error


def archive_record(text, kind, expected_hash=None, complete=False):
    kinds = {'complete-original', 'hash-verified-reconstruction', 'partial-excerpt', 'unavailable'}
    if kind not in kinds:
        raise ReportCheckError('Unknown archive completeness status')
    if kind == 'unavailable':
        if text is not None or complete or expected_hash is not None:
            raise ReportCheckError('Unavailable historical wording cannot be substituted')
        return {'kind': kind, 'text': None, 'sha256': None, 'complete': False}
    if not isinstance(text, str) or not text:
        raise ReportCheckError('Available archive material needs saved text')
    digest = sha256(text.encode('utf-8'))
    if kind in {'complete-original', 'hash-verified-reconstruction'} and not complete:
        raise ReportCheckError('An insertion without its original wrapper is a partial excerpt')
    if kind == 'partial-excerpt' and complete:
        raise ReportCheckError('Partial text cannot be claimed complete')
    if kind == 'hash-verified-reconstruction' and expected_hash is None:
        raise ReportCheckError('Exact reconstruction requires the expected full artifact hash')
    if expected_hash is not None and (not re.fullmatch(r'[0-9a-f]{64}', expected_hash) or
                                      digest != expected_hash):
        raise ReportCheckError('Complete archive SHA-256 mismatch; prefixes are not exact proof')
    return {'kind': kind, 'text': text, 'sha256': digest, 'complete': complete}


SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
SVG_ELEMENTS = {'svg', 'g', 'defs', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline',
                'polygon', 'text', 'tspan', 'title', 'desc', 'marker', 'clipPath', 'mask',
                'linearGradient', 'radialGradient', 'stop', 'use', 'symbol', 'style'}
SVG_ATTRIBUTES = {'id', 'role', 'aria-label', 'aria-labelledby', 'aria-describedby', 'tabindex',
                  'viewBox', 'preserveAspectRatio', 'width', 'height', 'x', 'y', 'x1', 'y1',
                  'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'points', 'd', 'transform',
                  'fill', 'fill-opacity', 'fill-rule', 'stroke', 'stroke-width', 'stroke-opacity',
                  'stroke-linecap', 'stroke-linejoin', 'stroke-dasharray', 'stroke-dashoffset',
                  'opacity', 'marker-start', 'marker-mid', 'marker-end', 'markerWidth',
                  'markerHeight', 'markerUnits', 'refX', 'refY', 'orient', 'clip-path', 'clip-rule',
                  'mask', 'maskUnits', 'maskContentUnits', 'gradientUnits', 'gradientTransform',
                  'href', 'class', 'style', 'font-size', 'font-family', 'font-weight', 'font-style',
                  'text-anchor', 'dominant-baseline', 'dy', 'dx', 'rotate', 'textLength',
                  'lengthAdjust', 'offset', 'stop-color', 'stop-opacity', 'vector-effect',
                  'display', 'visibility', 'color', 'overflow', 'space'}
SVG_CSS_PROPERTIES = {'fill', 'fill-opacity', 'fill-rule', 'stroke', 'stroke-width',
                      'stroke-opacity', 'stroke-linecap', 'stroke-linejoin', 'stroke-dasharray',
                      'stroke-dashoffset', 'opacity', 'marker-start', 'marker-mid', 'marker-end',
                      'clip-path', 'font-size', 'font-family', 'font-weight', 'font-style',
                      'text-anchor', 'dominant-baseline', 'color', 'stop-color', 'stop-opacity'}


def safe_css(value):
    if '\\' in value or re.search(r'expression\s*\(|javascript:|https?:|//|<!--', value, re.I):
        raise ReportCheckError('Active, escaped or external styles are not allowed')
    if any(rule.lower() not in {'media', 'supports', 'page', 'container', 'layer'}
           for rule in re.findall(r'@([\w-]+)', value)):
        raise ReportCheckError('External or active CSS rule is not allowed')
    if re.search(r'(?:image-set|image|paint|element|expression)\s*\(', value, re.I):
        raise ReportCheckError('Unsupported resource-bearing CSS function')
    matches = list(re.finditer(r'url\s*\((.*?)\)', value, re.I | re.S))
    if len(matches) != len(re.findall(r'url\s*\(', value, re.I)):
        raise ReportCheckError('Incomplete CSS resource reference')
    for match in matches:
        target = match.group(1).strip().strip('\"\'')
        if not re.fullmatch(r'#[A-Za-z_][\w.-]*', target):
            raise ReportCheckError('Styles must be self-contained with local references')


def svg_declarations(value):
    safe_css(value)
    if any(token in value for token in ('{', '}', '@', '!')):
        raise ReportCheckError('Unsupported SVG presentation declaration')
    for declaration in value.split(';'):
        if not declaration.strip():
            continue
        name, separator, setting = declaration.partition(':')
        if not separator or name.strip().lower() not in SVG_CSS_PROPERTIES or not setting.strip():
            raise ReportCheckError('Unapproved SVG presentation property')
        if any(function.lower() not in {'url', 'rgb', 'rgba', 'hsl', 'hsla'}
               for function in re.findall(r'([\w-]+)\s*\(', setting)):
            raise ReportCheckError('Unapproved SVG presentation function')


def namespace_svg(svg, prefix):
    if not re.fullmatch(r'[A-Za-z_][\w.-]*', prefix):
        raise ReportCheckError('SVG namespace must be an identifier')
    if re.search(r'<!DOCTYPE|<!ENTITY|<\?', svg, re.I):
        raise ReportCheckError('SVG declarations and processing instructions are not allowed')
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as error:
        raise ReportCheckError('Malformed SVG') from error
    if root.tag != f'{{{SVG_NAMESPACE}}}svg':
        raise ReportCheckError('Expected an SVG namespace root')
    identifiers = {}
    for element in root.iter():
        if not element.tag.startswith('{' + SVG_NAMESPACE + '}') or element.tag.split('}')[-1] not in SVG_ELEMENTS:
            raise ReportCheckError('SVG must be static and self-contained')
        identity = element.get('id')
        if identity:
            if identity in identifiers or not re.fullmatch(r'[A-Za-z_][\w.-]*', identity):
                raise ReportCheckError('Duplicate or invalid SVG identifier')
            identifiers[identity] = prefix if element is root else prefix + '-' + identity
        for name, value in element.attrib.items():
            local = name.split('}')[-1].lower()
            if name.startswith('{') and name not in {
                    '{http://www.w3.org/1999/xlink}href', '{http://www.w3.org/XML/1998/namespace}space'}:
                raise ReportCheckError('Unsupported SVG attribute namespace')
            if name.split('}')[-1] not in SVG_ATTRIBUTES:
                raise ReportCheckError('Unknown SVG attribute is not approved by this adapter')
            if local.startswith('on') or local in {'src', 'base'}:
                raise ReportCheckError('SVG event handlers and external content are forbidden')
            if local == 'href' and not re.fullmatch(r'#[A-Za-z_][\w.-]*', value):
                raise ReportCheckError('External SVG references are forbidden')
            safe_css(value)
            if local == 'style':
                svg_declarations(value)
        if element.tag.endswith('}style') and element.text:
            safe_css(element.text)
    title = root.find('{' + SVG_NAMESPACE + '}title')
    description = root.find('{' + SVG_NAMESPACE + '}desc')
    if title is None or description is None or not ''.join(title.itertext()).strip() or not ''.join(description.itertext()).strip():
        raise ReportCheckError('SVG needs a meaningful title and description')
    for element, suffix in ((title, 'title'), (description, 'description')):
        if not element.get('id'):
            identity = suffix
            while identity in identifiers:
                identity += '-a11y'
            element.set('id', identity)
            identifiers[identity] = prefix + '-' + identity

    def rewrite(value, reference=False):
        if reference:
            tokens = value.split()
            if any(token not in identifiers for token in tokens):
                raise ReportCheckError('Broken SVG accessibility reference')
            return ' '.join(identifiers[token] for token in tokens)
        if value.startswith('#') and re.fullmatch(r'#[A-Za-z_][\w.-]*', value):
            if value[1:] not in identifiers:
                raise ReportCheckError('Broken SVG internal reference')
            return '#' + identifiers[value[1:]]
        for target in re.findall(r'url\s*\(\s*[\"\']?#([\w.-]+)', value, re.I):
            if target not in identifiers:
                raise ReportCheckError('Broken SVG paint reference')
        return re.sub(r'(url\s*\(\s*[\"\']?)#([A-Za-z_][\w.-]*)',
                      lambda match: match.group(1) + '#' + identifiers[match.group(2)], value, flags=re.I)

    def rewrite_stylesheet(value):
        if re.sub(r'[^{}]+\{[^{}]*\}', '', value).strip():
            raise ReportCheckError('Unsupported SVG stylesheet grammar')
        def rule(match):
            selector, declarations = match.groups()
            selections = []
            for selected in selector.split(','):
                selected = selected.strip()
                token = re.fullmatch(r'#([A-Za-z_][\w-]*)(\.[A-Za-z_][\w-]*)*', selected)
                if token is None or token.group(1) not in identifiers:
                    raise ReportCheckError('SVG styles must select defined instance-local IDs')
                selections.append('#' + identifiers[token.group(1)] + selected[len(token.group(1)) + 1:])
            selector = ', '.join(selections)
            svg_declarations(declarations)
            return selector + '{' + rewrite(declarations) + '}'
        return re.sub(r'([^{}]+)\{([^{}]*)\}', rule, value)

    for element in root.iter():
        for name, value in list(element.attrib.items()):
            if name == 'id':
                element.set(name, identifiers[value])
            elif name in {'aria-labelledby', 'aria-describedby'}:
                element.set(name, rewrite(value, reference=True))
            elif name.split('}')[-1] == 'href':
                element.set(name, rewrite(value))
            else:
                element.set(name, rewrite(value) if re.search(r'url\s*\(', value, re.I) else value)
        if element.tag.endswith('}style') and element.text:
            element.text = rewrite_stylesheet(element.text)
    root.set('id', prefix)
    root.set('role', 'img')
    root.set('aria-labelledby', title.get('id'))
    root.set('aria-describedby', description.get('id'))
    ET.register_namespace('', SVG_NAMESPACE)
    return ET.tostring(root, encoding='unicode')


def diagram_contract(graph):
    try:
        nodes = {node['id']: node['label'] for node in graph['nodes']}
        if len(nodes) != len(graph['nodes']) or not nodes or any(not label for label in nodes.values()):
            raise ReportCheckError('Diagram needs unique labeled authoritative nodes')
        edges = Counter((edge['from'], edge['to'], edge['label'], edge['kind']) for edge in graph['edges'])
        if not edges or any(origin not in nodes or destination not in nodes for origin, destination, label, kind in edges):
            raise ReportCheckError('Diagram edges need intact node references')
        if any(kind not in {'decision', 'loop', 'optional', 'proposed', 'required'} for origin, destination, label, kind in edges):
            raise ReportCheckError('Diagram connection meaning is unspecified')
        return nodes, edges
    except (KeyError, TypeError) as error:
        raise ReportCheckError('Diagram needs mapped nodes and labeled typed edges') from error


def verify_diagram(authoritative, candidate):
    if diagram_contract(authoritative) != diagram_contract(candidate):
        raise ReportCheckError('Diagram lost or changed a decision, loop, label or optional connection')


def diagram_text(graph):
    nodes, edges = diagram_contract(graph)
    return '\n'.join(f'{nodes[origin]} → {nodes[destination]}: {label} ({kind})'
                     for origin, destination, label, kind in edges)


def checked_asset(root, source_manifest):
    for field in ('source', 'asset'):
        record = source_manifest[field]
        path = bounded_path(root, record['artifact'])
        if not path.is_file() or sha256(path.read_bytes()) != record['sha256']:
            raise ReportCheckError(f'Diagram {field} identity changed; regenerate and verify assets')
    return bounded_path(root, source_manifest['asset']['artifact']).read_text(encoding='utf-8')


class ReportHTML(HTMLParser):
    def __init__(self, allowed_scripts):
        super().__init__(convert_charrefs=True)
        self.allowed_scripts = set(allowed_scripts)
        self.identifiers = set()
        self.references = []
        self.script = None
        self.style = False
        self.capture = ''

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {'iframe', 'object', 'embed', 'base', 'form', 'foreignobject',
                   'animate', 'animatetransform', 'animatemotion', 'set', 'image',
                   'audio', 'video', 'frame', 'frameset', 'portal'}:
            raise ReportCheckError('Active or external report content')
        for name, value in attrs:
            if name.lower().startswith('on') or name in {'srcdoc', 'srcset', 'poster', 'background'}:
                raise ReportCheckError('Unapproved active report attribute')
            if name in {'src', 'data'} and value:
                raise ReportCheckError('Offline report cannot request external assets')
            if name == 'style':
                safe_css(value or '')
            if name == 'href' and value:
                if value.startswith('#'):
                    self.references.append(value[1:])
                elif tag != 'a' or not re.match(r'https?://|mailto:', value, re.I):
                    raise ReportCheckError('External resource or unsafe navigation link')
            if name in {'aria-labelledby', 'aria-describedby'} and value:
                self.references.extend(value.split())
        if tag == 'meta' and attributes.get('http-equiv', '').lower() == 'refresh':
            raise ReportCheckError('Offline report cannot redirect')
        identity = attributes.get('id')
        if identity:
            if identity in self.identifiers:
                raise ReportCheckError('Duplicate report anchor')
            self.identifiers.add(identity)
        if tag == 'script':
            self.script = attributes.get('type', 'text/javascript')
            self.capture = ''
        if tag == 'style':
            self.style = True
            self.capture = ''

    def handle_data(self, data):
        if self.script is not None or self.style:
            self.capture += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            if sha256(self.capture.encode()) not in self.allowed_scripts:
                raise ReportCheckError('Unapproved embedded script/data; review indirect disclosure')
            self.script = None
            self.capture = ''
        if tag == 'style' and self.style:
            safe_css(self.capture)
            self.style = False
            self.capture = ''


def inspect_html(content, allowed_scripts=()):
    parser = ReportHTML(allowed_scripts)
    parser.feed(content)
    parser.close()
    if parser.script is not None or parser.style:
        raise ReportCheckError('Incomplete report script or style')
    if any(reference not in parser.identifiers for reference in parser.references):
        raise ReportCheckError('Broken report link or accessibility reference')
    return {'status': 'completed', 'anchors': len(parser.identifiers),
            'evidence': 'Static anchor/resource inspection only; browser behavior not tested'}


def verification_claims(claimed, observed):
    outcomes = {'completed', 'failed', 'blocked', 'not-run'}
    if set(observed) - set(claimed):
        raise ReportCheckError('Observed failed/blocked/not-run checks cannot be silently omitted')
    for name, status in claimed.items():
        if status not in outcomes:
            raise ReportCheckError('Checks need completed, failed, blocked or not-run status')
        actual = observed.get(name)
        if actual is not None and actual.get('status') == 'completed' and actual.get('result', 'pass') != 'pass':
            raise ReportCheckError(f'Completed check contains an explicit failed result: {name}')
        if actual is None:
            if status != 'not-run':
                raise ReportCheckError(f'No observed evidence for check: {name}')
        elif status != actual.get('status') or (status != 'not-run' and not actual.get('evidence')):
            raise ReportCheckError(f'False verification claim: {name}')


def transactional_build(root, sources, output, build, checks=()):
    target = bounded_path(root, output)
    lock = target.parent / ('.' + target.name + '.report-lock')
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise ReportCheckError('Report output is owned by another build; do not steal its lock') from error
    try:
        return _transactional_build(root, sources, output, build, checks)
    finally:
        lock.rmdir()


def _transactional_build(root, sources, output, build, checks):
    root = Path(root)
    target = bounded_path(root, output)
    paths = [bounded_path(root, source) for source in sources]
    if target in paths or len(set(paths)) != len(paths):
        raise ReportCheckError('Build mapping duplicates inputs or edits a generated input')
    if any(not path.is_file() for path in paths):
        raise ReportCheckError('Missing build dependency blocks the affected operation')
    snapshot = {path: sha256(path.read_bytes()) for path in paths}
    previous = target.read_bytes() if target.exists() else None
    parent_identity = (target.parent.stat().st_dev, target.parent.stat().st_ino)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.report-stage-', suffix=target.suffix,
                                     delete=False) as temporary:
        staged = Path(temporary.name)
    committed = False
    destructive = False

    def output_unchanged():
        try:
            bounded_path(root, output)
        except ReportCheckError:
            return False
        return (target.read_bytes() if target.exists() else None) == previous

    def staged_identity():
        if staged.is_symlink() or not staged.is_file() or not staged.stat().st_size:
            raise ReportCheckError('Staged output was swapped, removed or truncated')
        metadata = staged.stat()
        return metadata.st_dev, metadata.st_ino, sha256(staged.read_bytes())

    try:
        try:
            build(staged)
        except BaseException:
            destructive = not output_unchanged()
            raise
        if not output_unchanged():
            destructive = True
            raise ReportCheckError('Destructive build changed the live report instead of staged output')
        generated_identity = staged_identity()
        results = []
        for check in checks:
            result = check(staged)
            if result is False or isinstance(result, dict) and (
                    result.get('status') != 'completed' or result.get('result', 'pass') != 'pass'):
                raise ReportCheckError('Staged report verification failed or was blocked')
            if staged_identity() != generated_identity:
                raise ReportCheckError('A verification check changed the staged artifact')
            results.append(result if result is not None else {
                'status': 'completed', 'evidence': f'Mapped check {check.__name__} returned without errors'})
        changed = [str(path.relative_to(root)) for path, digest in snapshot.items()
                   if not bounded_path(root, path.relative_to(root)).is_file() or sha256(path.read_bytes()) != digest]
        if changed:
            raise ReportCheckError('Concurrent source changes detected: ' + ', '.join(changed))
        if not output_unchanged():
            raise ReportCheckError('Concurrent/destructive live output change detected')
        if staged_identity() != generated_identity:
            raise ReportCheckError('Staged artifact changed before replacement')
        with staged.open('rb') as stream:
            os.fsync(stream.fileno())
        os.replace(staged, target)
        committed = True
        return {'status': 'completed', 'output_sha256': sha256(target.read_bytes()),
                'source_hashes': {str(path.relative_to(root)): digest for path, digest in snapshot.items()},
                'checks': results}
    finally:
        safe_parent = (target.parent.is_dir() and not target.parent.is_symlink() and
                       target.parent.resolve().is_relative_to(root.resolve()) and
                       all(not ancestor.is_symlink() for ancestor in target.parent.parents if ancestor.is_relative_to(root)) and
                       (target.parent.stat().st_dev, target.parent.stat().st_ino) == parent_identity)
        if destructive and not committed and safe_parent:
            if not output_unchanged():
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.report-restore-',
                                                     delete=False) as recovery:
                        recovery.write(previous)
                        recovery.flush()
                        os.fsync(recovery.fileno())
                        recovery_path = Path(recovery.name)
                    os.replace(recovery_path, target)
        staged.unlink(missing_ok=True)
