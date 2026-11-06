import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from distribution import install as installer
from research.scripts import report_checks
from scripts import build_skills, validate_skills
from tests import test_portability_hardening as portability


def synthetic_archive(root, version, content=None):
    files = {name: b'Independently synthetic fixture' for name in ['README.md', 'install.py', 'LICENSE', 'NOTICE']}
    for name in ['one', 'two']:
        text = content if content is not None else version
        files[f'skills/{name}/SKILL.md'] = f'---\nname: {name}\ndescription: Synthetic fixture\n---\n{text}\n'.encode()
        files[f'skills/{name}/guide name.md'] = b'# Guide\n'
    record = {'schema_version': 1, 'package': installer.PACKAGE, 'version': version,
              'commit': '0' * 40, 'host_profiles': installer.HOST_DIRS, 'qualification': {},
              'skills': [{'name': name, 'path': f'skills/{name}',
                          'required_files': ['SKILL.md', 'guide name.md']} for name in ['one', 'two']],
              'files': {name: hashlib.sha256(value).hexdigest() for name, value in files.items()}}
    path = root / (version + '.zip')
    with zipfile.ZipFile(path, 'w') as output:
        for name, value in files.items():
            output.writestr(name, value)
        output.writestr('manifest.json', json.dumps(record))
    return path


class AccessRemediationTests(unittest.TestCase):
    setUp = portability.SourceContractTests.setUp
    git = portability.SourceContractTests.git
    write = portability.SourceContractTests.write

    def test_local_exclusions_block_document_anchor_and_policy_reads(self):
        for excluded in ['README.md', 'docs/guide.md', '.gitignore']:
            with self.subTest(excluded=excluded):
                (self.root / '.git/info/exclude').write_text(excluded + '\n')
                identity = self.git('hash-object', excluded)
                original = subprocess.run
                reads = []

                def observe(command, *arguments, **kwargs):
                    if 'cat-file' in command and identity in command:
                        reads.append(command)
                    return original(command, *arguments, **kwargs)

                with patch('subprocess.run', side_effect=observe):
                    errors = validate_skills.validate_source(self.root, 'index')
                self.assertTrue(errors, 'Blocked access cannot be reported as complete source validation')
                self.assertEqual(reads, [], 'Locally excluded content must not be acquired')

    def test_exact_excluded_policy_is_not_opened(self):
        self.write('.gitignore', 'rules/.gitignore\n')
        self.write('rules/.gitignore', 'Synthetic excluded policy\n')
        self.git('add', '.gitignore')
        self.git('add', '-f', 'rules/.gitignore')
        identity = self.git('hash-object', 'rules/.gitignore')
        original = subprocess.run
        reads = []

        def observe(command, *arguments, **kwargs):
            if 'cat-file' in command and identity in command:
                reads.append(command)
            return original(command, *arguments, **kwargs)

        with patch('subprocess.run', side_effect=observe):
            self.assertTrue(validate_skills.validate_source(self.root, 'index'))
        self.assertEqual(reads, [])

    def test_inventory_and_qualification_symlinks_are_rejected_before_reads(self):
        inventory = {'schema_version': 1, 'package': installer.PACKAGE, 'parents': ['example'],
                     'common_resources': [], 'owned_resources': {'example': []}}
        self.write('inventory.json', json.dumps(inventory))
        self.write('example/SKILL.md', '---\nname: example\ndescription: Synthetic fixture\n---\n')
        self.write('evaluations/status.json', json.dumps({'schema_version': 1, 'hosts': {}}))
        for relative in build_skills.source_paths(inventory):
            if relative in ['inventory.json', '.gitignore', 'example/SKILL.md']:
                continue
            self.write(relative, (build_skills.ROOT / relative).read_text())
        self.git('add', '.')
        for relative in ['inventory.json', 'evaluations/status.json']:
            with self.subTest(relative=relative):
                target = self.root / relative
                original_content = target.read_bytes()
                private = self.write('private/context.json', original_content.decode())
                target.unlink()
                target.symlink_to(private)
                original = Path.read_bytes
                reads = []

                def observe(path):
                    if path == target:
                        reads.append(path)
                    return original(path)

                with patch.object(Path, 'read_bytes', observe):
                    with self.assertRaises(ValueError):
                        if relative == 'inventory.json':
                            build_skills.payload(self.root)
                        else:
                            build_skills.qualification(self.root)
                self.assertEqual(reads, [])
                target.unlink()
                target.write_bytes(original_content)

    def test_captured_preparation_rejects_repository_descendants(self):
        self.write('.gitignore', 'child/private/\n')
        child = self.root / 'child'
        target = self.write('child/private/context.txt', 'Synthetic excluded input')
        original = Path.read_bytes
        reads = []

        def observe(path):
            if path == target:
                reads.append(path)
            return original(path)

        with patch.object(Path, 'read_bytes', observe):
            with self.assertRaises(ValueError):
                build_skills.prepare_captured(child, {'package': installer.PACKAGE, 'parents': ['example']},
                    {'skills/example/resources/policy.md': b'Inert output'},
                    {'private/context.txt': hashlib.sha256(b'Synthetic excluded input').hexdigest()})
        self.assertEqual(reads, [])
        self.assertFalse((child / 'dist').exists())


class NavigationRemediationTests(unittest.TestCase):
    def test_case_variant_markdown_is_relocated_by_the_real_assembler(self):
        inventory = {'schema_version': 1, 'package': installer.PACKAGE, 'parents': ['one'],
                     'common_resources': ['resources/guide.md'], 'owned_resources': {'one': ['CONTEXT.MARKDOWN']}}
        contents = {path: b'Synthetic support fixture' for path in build_skills.source_paths(inventory)}
        contents['inventory.json'] = json.dumps(inventory).encode()
        contents['one/SKILL.md'] = b'---\nname: one\ndescription: Synthetic fixture\n---\n'
        contents['resources/guide.md'] = b'# Guide\n'
        contents['one/CONTEXT.MARKDOWN'] = b'[Read](../resources/guide.md#guide "Title")\n'
        files = build_skills.assemble_payload(contents)[1]
        self.assertEqual(files['skills/one/CONTEXT.MARKDOWN'], b'[Read](resources/guide.md#guide "Title")\n')

    def test_non_navigation_attributes_are_not_edges_or_relocated(self):
        for text in ['<div data-href="missing.md">Text</div>', '<img data-src="missing.svg">',
                     '<div title=\'href="missing.md"\'>Text</div>']:
            with self.subTest(text=text):
                self.assertEqual(validate_skills.markdown_navigation(text)[0], [])
        text = '<img src="../resources/picture.svg" data-src="keep.svg" title=\'src="keep.svg"\'>'
        expected = '<img src="resources/picture.svg" data-src="keep.svg" title=\'src="keep.svg"\'>'
        self.assertEqual(validate_skills.relocate_markdown(text, 'review/code.md', 'skills/review/code.md',
            {'resources/picture.svg': 'skills/review/resources/picture.svg'}), expected)

    def test_duplicate_navigation_attributes_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_skills.markdown_navigation('<a href="private/missing.md" href="guide.md">Read</a>')

    def test_supported_inline_forms_survive_standalone_archive_and_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for number, text in enumerate(['[Read](<guide name.md> "Title")',
                '[Read](guide%20name.md?view=1#guide "Title")', '`[Example](missing.md)`',
                '```md\n[Example](missing.md)\n```', '<!-- [Example](missing.md) -->']):
                with self.subTest(text=text):
                    archive = synthetic_archive(root, f'syntax-{number}', text)
                    installer.read_archive(archive)
                    project = root / f'project-{number}'
                    project.mkdir()
                    self.assertEqual(installer.install(archive, project)['installed'], ['one', 'two'])

    def test_cli_dependencies_are_one_way(self):
        tree = ast.parse((build_skills.ROOT / 'scripts/build_skills.py').read_text())
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertNotIn('scripts.validate_skills', imports, 'Builder must consume neutral services, not the validator command')


class InstallRemediationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        self.old = synthetic_archive(self.root, 'old')
        self.new = synthetic_archive(self.root, 'new')
        installer.install(self.old, self.project)
        self.destination = self.project / '.agents/skills'

    def test_missing_or_changed_selected_output_cannot_commit(self):
        original = os.replace

        def change(source, target):
            result = original(source, target)
            if str(source).endswith('/new/two'):
                original(self.destination / 'one', self.project / 'external-save')
            return result

        before = (self.destination / installer.RECEIPT).read_bytes()
        with patch('distribution.install.os.replace', side_effect=change):
            with self.assertRaises((OSError, ValueError)):
                installer.install(self.new, self.project, upgrade=True)
        self.assertEqual((self.destination / installer.RECEIPT).read_bytes(), before)
        self.assertTrue(list(self.destination.glob('.skills-install-*/backup/one/SKILL.md')))

    def test_cleanup_preserves_unknown_staging_entries_after_commit(self):
        original = os.replace
        additions = []

        def change(source, target):
            result = original(source, target)
            if Path(target).name == installer.RECEIPT:
                path = Path(source).parent / 'other-writer.txt'
                path.write_text('Synthetic competing edit')
                additions.append(path)
            return result

        with patch('distribution.install.os.replace', side_effect=change):
            result = installer.install(self.new, self.project, upgrade=True)
        self.assertTrue(result['committed'])
        self.assertTrue(additions[0].exists())
        self.assertEqual(result.get('recovery_location'), str(additions[0].parent))


class LocalTransactionRemediationTests(unittest.TestCase):
    def test_preparation_cleanup_preserves_unknown_empty_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'source.txt').write_bytes(b'Synthetic source')
            original = os.replace
            additions = []

            def add_directory(source, target):
                result = original(source, target)
                if Path(target).name == '.prepared-resources.json':
                    path = Path(source).parent / 'other-writer-directory'
                    path.mkdir()
                    additions.append(path)
                return result

            with patch('scripts.build_skills.os.replace', side_effect=add_directory):
                build_skills.prepare_captured(root, {'package': installer.PACKAGE, 'parents': ['one']},
                    {'skills/one/resources/policy.md': b'Public synthetic output'},
                    {'source.txt': hashlib.sha256(b'Synthetic source').hexdigest()})
            self.assertTrue(additions[0].exists(), 'Unknown staging directories are not transaction-owned')

    def test_preparation_receipt_publication_prevents_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source.txt'
            source.write_bytes(b'Synthetic source')
            inputs = {'source.txt': hashlib.sha256(source.read_bytes()).hexdigest()}
            inventory = {'package': installer.PACKAGE, 'parents': ['example']}
            build_skills.prepare_captured(root, inventory, {'skills/example/resources/policy.md': b'old'}, inputs)
            original = os.replace

            def lose_ack(source, target):
                result = original(source, target)
                if Path(target).name == '.prepared-resources.json':
                    raise OSError('Synthetic lost receipt acknowledgement')
                return result

            with patch('scripts.build_skills.os.replace', side_effect=lose_ack):
                build_skills.prepare_captured(root, inventory, {'skills/example/resources/policy.md': b'new'}, inputs)
            self.assertEqual((root / 'example/resources/policy.md').read_bytes(), b'new')
            receipt = json.loads((root / 'dist/.prepared-resources.json').read_text())
            self.assertEqual(receipt['skills']['example']['files']['resources/policy.md']['sha256'], hashlib.sha256(b'new').hexdigest())

    def test_report_rejects_unsupported_check_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'source.txt').write_text('Synthetic source')
            target = root / 'report.html'
            target.write_text('old')
            for value in ['failed', [], 0]:
                with self.subTest(value=value), self.assertRaises(report_checks.ReportCheckError):
                    report_checks.transactional_build(root, ['source.txt'], 'report.html',
                        lambda staged: staged.write_text('new'), [lambda staged: value])
                self.assertEqual(target.read_text(), 'old')

    def test_report_recovery_preserves_competing_live_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'source.txt').write_text('Synthetic source')
            target = root / 'report.html'
            target.write_text('old')
            original = os.fsync

            def destructive(staged):
                target.write_text('builder-owned modification')
                raise RuntimeError('Synthetic builder failure')

            def other_writer(fd):
                target.write_text('Synthetic competing editor output')
                return original(fd)

            with patch('research.scripts.report_checks.os.fsync', side_effect=other_writer):
                with self.assertRaises((RuntimeError, report_checks.ReportCheckError)):
                    report_checks.transactional_build(root, ['source.txt'], 'report.html', destructive)
            self.assertEqual(target.read_text(), 'Synthetic competing editor output')
            self.assertTrue(list(root.glob('.report-restore-*')))

    def test_unattributed_live_change_during_builder_is_not_claimed_as_owned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'source.txt').write_text('Synthetic source')
            target = root / 'report.html'
            target.write_text('old')

            def builder(staged):
                staged.write_text('partial candidate')
                target.write_text('Synthetic unrelated live editor output')
                raise RuntimeError('Synthetic builder failure')

            with self.assertRaises((RuntimeError, report_checks.ReportCheckError)):
                report_checks.transactional_build(root, ['source.txt'], 'report.html', builder)
            self.assertEqual(target.read_text(), 'Synthetic unrelated live editor output')
            recovery = list(root.glob('.report-restore-*'))
            self.assertTrue(recovery)
            self.assertEqual(recovery[0].read_text(), 'old')

    def test_report_commit_lost_acknowledgement_reports_committed_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'source.txt').write_text('Synthetic source')
            target = root / 'report.html'
            target.write_text('old')
            original = os.replace

            def lose_ack(source, destination):
                result = original(source, destination)
                if Path(destination) == target:
                    raise OSError('Synthetic lost report acknowledgement')
                return result

            with patch('research.scripts.report_checks.os.replace', side_effect=lose_ack):
                result = report_checks.transactional_build(root, ['source.txt'], 'report.html',
                    lambda staged: staged.write_text('new'))
            self.assertEqual(result['status'], 'completed')
            self.assertEqual(target.read_text(), 'new')

    def test_failed_builder_directory_replacement_preserves_baseline_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'source.txt').write_text('Synthetic source')
            target = root / 'report.html'
            target.write_text('old')

            def replace_with_directory(staged):
                target.unlink()
                target.mkdir()
                raise RuntimeError('Synthetic builder failure')

            with self.assertRaises((RuntimeError, report_checks.ReportCheckError)):
                report_checks.transactional_build(root, ['source.txt'], 'report.html', replace_with_directory)
            self.assertTrue(target.is_dir())
            recovery = list(root.glob('.report-restore-*'))
            self.assertTrue(recovery)
            self.assertEqual(recovery[0].read_text(), 'old')


if __name__ == '__main__':
    unittest.main()
