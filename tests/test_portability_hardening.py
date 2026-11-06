import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from distribution import install as installer
from scripts import build_skills, validate_skills
from tests import test_distribution as distribution_tests


class SourceContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git('init', '-q')
        self.write('.gitignore', 'private/\n*.secret\n')
        self.write('README.md', '# Start\n[Guide](docs/guide.md#details)\n')
        self.write('docs/guide.md', '# Details\n')
        self.git('add', '.')

    def git(self, *arguments):
        return subprocess.run(['git', *arguments], cwd=self.root, check=True,
                              text=True, capture_output=True).stdout.strip()

    def write(self, relative, text):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def check(self, snapshot='index'):
        function = getattr(validate_skills, 'validate_source', None)
        self.assertTrue(callable(function), 'Source validation must be implemented, not replaced by prepared-file checks')
        return function(self.root, snapshot)

    def test_valid_index_graph_needs_no_preparation(self):
        self.assertEqual(self.check(), [])
        self.assertFalse((self.root / 'dist').exists())

    def test_nested_markdown_and_case_variants_are_checked(self):
        self.write('docs/nested.MARKDOWN', '[Missing](absent.md)\n')
        self.git('add', '.')
        self.assertTrue(any('nested.MARKDOWN' in error for error in self.check()))

    def test_ignored_and_untracked_targets_fail_even_when_present(self):
        for target in ['private/context.md', 'new.md']:
            with self.subTest(target=target):
                self.write(target, 'SYNTHETIC NONPUBLIC TEST INPUT\n')
                self.write('README.md', f'[Target]({target})\n')
                self.git('add', 'README.md')
                self.assertTrue(self.check())

    def test_force_added_excluded_file_fails_without_blob_read(self):
        self.write('private/context.md', 'SYNTHETIC NONPUBLIC TEST INPUT\n')
        self.git('add', '-f', 'private/context.md')
        identity = self.git('hash-object', 'private/context.md')
        original = subprocess.run
        observed = []

        def inspect(command, *arguments, **kwargs):
            if 'cat-file' in command and identity in command:
                observed.append(command)
            return original(command, *arguments, **kwargs)

        with patch('subprocess.run', side_effect=inspect):
            self.assertTrue(self.check())
        self.assertEqual(observed, [], 'Ignored contents must not be loaded to diagnose exclusion')

    def test_excluded_directory_ignore_file_is_not_read(self):
        self.write('private/.gitignore', 'Synthetic nonpublic policy fixture\n')
        self.git('add', '-f', 'private/.gitignore')
        identity = self.git('hash-object', 'private/.gitignore')
        original = subprocess.run
        reads = []

        def observe(command, *arguments, **kwargs):
            if 'cat-file' in command and identity in command:
                reads.append(command)
            return original(command, *arguments, **kwargs)

        with patch('subprocess.run', side_effect=observe):
            self.assertTrue(self.check())
        self.assertEqual(reads, [], 'An excluded parent cannot be rescued by reading private nested rules')

    def test_staged_bytes_not_unstaged_repairs_determine_result(self):
        self.write('README.md', '[Target](missing.md)\n')
        self.git('add', 'README.md')
        self.write('README.md', '[Target](docs/guide.md)\n')
        self.assertTrue(self.check())
        self.git('add', 'README.md')
        self.assertEqual(self.check(), [])
        self.git('rm', '--cached', 'docs/guide.md')
        self.assertTrue(self.check())

    def test_committed_tree_and_index_have_separate_contents(self):
        tree = self.git('write-tree')
        (self.root / '.git/HEAD').write_text(tree + '\n')
        self.write('README.md', '[Target](missing.md)\n')
        self.git('add', 'README.md')
        self.assertEqual(self.check('HEAD'), [])
        self.assertTrue(self.check('index'))

    def test_negation_and_staged_ignore_rules_are_respected(self):
        self.write('.gitignore', '*.md\n!README.md\n!docs/\n!docs/guide.md\n')
        self.git('add', '.gitignore')
        self.assertEqual(self.check(), [])
        self.write('.gitignore', '*.md\n!README.md\n')
        self.git('add', '.gitignore')
        self.assertTrue(self.check())
        self.write('.gitignore', '')
        self.assertTrue(self.check(), 'Unstaged ignore edits must not change the proposed commit')

    def test_local_exclusions_do_not_change_publication_verdict(self):
        (self.root / '.git/info/exclude').write_text('*.md\n')
        snapshot = validate_skills.SourceSnapshot(self.root, 'index')
        self.assertEqual(snapshot.ignored(['README.md', 'docs/guide.md']), set())
        self.assertTrue(self.check(), 'Publication eligibility is distinct from blocked local inspection')

    def test_references_images_html_and_anchors_are_checked(self):
        self.write('README.md', '''# Start
[guide]: docs/guide.md#details "Title"

[full][guide] [guide][] [guide]
![Image](docs/picture.svg)
<a href="docs/guide.md#details">HTML</a>
<img src="docs/picture.svg">
''')
        self.write('docs/picture.svg', '<svg/>')
        self.git('add', '.')
        self.assertEqual(self.check(), [])
        self.write('docs/guide.md', '# Renamed\n')
        self.git('add', 'docs/guide.md')
        self.assertTrue(self.check())

    def test_code_comments_frontmatter_and_external_links_are_not_local_edges(self):
        self.write('README.md', '''---
example: "[not navigation](private/example.md)"
---
# Start
`[Example](private/example.md)`
<!-- <img src="private/example.md"> -->
    [Example](private/example.md)
```md
[Example](private/example.md)
```
[External](https://example.invalid/docs) [Email](mailto:example@example.invalid)
''')
        self.git('add', 'README.md')
        self.assertEqual(self.check(), [])

    def test_encoded_paths_duplicate_anchors_and_explicit_ids(self):
        self.write('docs/space name.md', '# Details\n# Details\n<a id="stable"></a>\n')
        self.write('README.md', '[One](docs/space%20name.md#details-1)\n[Two](<docs/space name.md#stable>)\n')
        self.git('add', '.')
        self.assertEqual(self.check(), [])

    def test_table_escapes_do_not_make_code_examples_navigation(self):
        self.write('README.md', '| Example | Guide |\n|---|---|\n| `edge\\|hardening` | [Read](docs/guide.md) |\n')
        self.git('add', 'README.md')
        self.assertEqual(self.check(), [])

    def test_unsafe_case_directory_and_symlink_targets_fail(self):
        self.write('docs/linked.md', 'Ordinary synthetic file\n')
        self.git('add', '.')
        (self.root / 'alias').symlink_to('docs', target_is_directory=True)
        self.git('add', 'alias')
        for target in ['../outside.md', '%2e%2e/outside.md', 'docs/Guide.md', 'docs/',
                       'alias/guide.md', 'file:///tmp/private.md', 'javascript:alert(1)',
                       'docs/%zz.md', 'docs/%00.md']:
            with self.subTest(target=target):
                self.write('README.md', f'[Target]({target})\n')
                self.git('add', 'README.md')
                self.assertTrue(self.check())

    def test_unmerged_index_is_rejected(self):
        identity = self.git('hash-object', 'README.md')
        self.git('update-index', '--force-remove', 'README.md')
        subprocess.run(['git', 'update-index', '--index-info'], cwd=self.root,
                       input=f'100644 {identity} 1\tREADME.md\n', text=True, check=True)
        self.assertTrue(self.check())

    def test_current_locator_mapping_is_explicit_and_complete(self):
        ledger = {'requirements': [{'instruction_or_reference': ['old/references/guide.md'], 'worked_case': []}]}
        content = json.dumps(ledger)
        self.write('evaluations/workflow-methods/traceability.json', content)
        mapping = {'schema_version': 1, 'path_base': 'repository_root',
                   'historical_ledger': {'path': 'traceability.json', 'sha256': hashlib.sha256(content.encode()).hexdigest()},
                   'aliases': {'old/references/guide.md': 'docs/guide.md'}}
        self.write('evaluations/workflow-methods/current-locators.json', json.dumps(mapping))
        self.git('add', '.')
        self.assertEqual(self.check(), [])
        mapping['aliases'] = {}
        self.write('evaluations/workflow-methods/current-locators.json', json.dumps(mapping))
        self.git('add', '.')
        self.assertTrue(self.check())

    def test_real_export_inputs_reject_local_privacy_exclusions(self):
        function = getattr(validate_skills, 'validate_inputs', None)
        self.assertTrue(callable(function), 'Real exports require a pre-read eligibility boundary')
        (self.root / '.git/info/exclude').write_text('docs/guide.md\n')
        with self.assertRaises(ValueError):
            function(self.root, ['docs/guide.md'])

    def test_captured_fixture_api_cannot_bypass_real_repository_read_guards(self):
        target = self.write('private/context.md', 'Synthetic nonpublic fixture')
        original = Path.read_bytes
        reads = []

        def observe(path):
            if path == target:
                reads.append(path)
            return original(path)

        with patch.object(Path, 'read_bytes', observe):
            with self.assertRaisesRegex(ValueError, 'exclusion'):
                build_skills.prepare_captured(
                    self.root, {'package': 'mdbecker-skills', 'parents': ['example']},
                    {'skills/example/resources/policy.md': b'Synthetic candidate'},
                    {'private/context.md': hashlib.sha256(b'Synthetic nonpublic fixture').hexdigest()})
        self.assertEqual(reads, [])
        self.assertFalse((self.root / 'dist').exists())

    def test_real_payload_rejects_ignored_inventory_input_before_read(self):
        inventory = {'schema_version': 1, 'package': 'mdbecker-skills', 'parents': ['example'],
                     'common_resources': ['private/context.md'], 'owned_resources': {'example': []}}
        self.write('inventory.json', json.dumps(inventory))
        self.write('example/SKILL.md', '---\nname: example\ndescription: Public synthetic example\n---\n')
        for relative in ['scripts/build_skills.py', 'scripts/validate_skills.py', 'requirements-dev.txt',
                         'scripts/inventory.py', 'scripts/source_access.py', 'scripts/navigation.py',
                         'distribution/__init__.py', 'distribution/README.md', 'distribution/install.py', 'LICENSE', 'NOTICE']:
            self.write(relative, (build_skills.ROOT / relative).read_text())
        target = self.write('private/context.md', 'Synthetic nonpublic fixture')
        self.git('add', '.')
        original = Path.read_bytes
        reads = []

        def observe(path):
            if path == target:
                reads.append(path)
            return original(path)

        with patch.object(Path, 'read_bytes', observe):
            with self.assertRaisesRegex(ValueError, 'exclusion'):
                build_skills.payload(self.root)
        self.assertEqual(reads, [])
        self.assertFalse((self.root / 'dist').exists())

    def test_current_matrix_and_workflow_paths_are_not_silently_accepted(self):
        for source, content in [
            ('evaluations/matrix.json', json.dumps({'rows': [{'method': 'missing.py'}]})),
            ('.github/workflows/checks.yml', 'jobs:\n  check:\n    steps:\n      - run: python scripts/missing.py\n')]:
            with self.subTest(source=source):
                if source.startswith('.github/'):
                    self.git('rm', '--cached', 'evaluations/matrix.json')
                self.write(source, content)
                self.git('add', source)
                self.assertTrue(self.check())

    def test_source_reverification_does_not_read_through_replaced_ancestor(self):
        inventory = {'schema_version': 1, 'package': 'mdbecker-skills', 'parents': ['example'],
                     'common_resources': ['resources/public.md'], 'owned_resources': {'example': []}}
        self.write('inventory.json', json.dumps(inventory))
        self.write('example/SKILL.md', '---\nname: example\ndescription: Synthetic example\n---\n')
        self.write('resources/public.md', '# Public\n')
        self.write('private/public.md', 'Synthetic nonpublic fixture')
        for relative in ['scripts/build_skills.py', 'scripts/validate_skills.py', 'requirements-dev.txt',
                         'scripts/inventory.py', 'scripts/source_access.py', 'scripts/navigation.py',
                         'distribution/__init__.py', 'distribution/README.md', 'distribution/install.py', 'LICENSE', 'NOTICE']:
            self.write(relative, (build_skills.ROOT / relative).read_text())
        self.git('add', '.')
        original_assemble = build_skills.assemble_payload
        original_read = Path.read_bytes
        redirected = []
        reads = []

        def redirect(contents):
            result = original_assemble(contents)
            (self.root / 'resources').rename(self.root / 'saved-public')
            (self.root / 'resources').symlink_to('private', target_is_directory=True)
            redirected.append(True)
            return result

        def observe(path):
            if redirected and path == self.root / 'resources/public.md':
                reads.append(path)
            return original_read(path)

        with patch('scripts.build_skills.assemble_payload', side_effect=redirect), \
                patch.object(Path, 'read_bytes', observe):
            with self.assertRaises(ValueError):
                build_skills.payload(self.root)
        self.assertEqual(reads, [], 'Verification must repeat ancestor checks before reads')

    def test_relocation_only_changes_parsed_destinations(self):
        function = getattr(validate_skills, 'relocate_markdown', None)
        self.assertTrue(callable(function), 'Exports require explicit parsed source-to-package relocation')
        source = 'review/discuss.md'
        destination = 'skills/review/discuss.md'
        mapping = {'resources/guide.md': 'skills/review/resources/guide.md'}
        text = '# Topic\n`[Example](../resources/guide.md)`\n[Read](../resources/guide.md#details "Keep title")\n'
        expected = '# Topic\n`[Example](../resources/guide.md)`\n[Read](resources/guide.md#details "Keep title")\n'
        self.assertEqual(function(text, source, destination, mapping), expected)
        reference = '[Read][guide]\n\n[guide]: ../resources/guide.md#details "Keep title"\n'
        self.assertEqual(function(reference, source, destination, mapping),
                         '[Read][guide]\n\n[guide]: resources/guide.md#details "Keep title"\n')
        with self.assertRaises(ValueError):
            function('[Private](../private/absent.md)', source, destination, mapping)


class MetadataBoundaryTests(unittest.TestCase):
    def test_complete_name_and_description_limits(self):
        for name in ['1', 'a' * 64, 'valid-name']:
            text = f'---\nname: {json.dumps(name)}\ndescription: Public instructions\n---\n'
            self.assertEqual(installer.parse_skill_metadata(text, name)['name'], name)
        for name in ['', 'a' * 65, 'Upper', '-bad', 'bad-', 'bad--name']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                installer.parse_skill_metadata(f'---\nname: {name}\ndescription: Public instructions\n---\n', name)
        for length in [1, 1024]:
            self.assertEqual(len(installer.parse_skill_metadata(
                '---\nname: valid\ndescription: ' + 'x' * length + '\n---\n', 'valid')['description']), length)
        with self.assertRaises(ValueError):
            installer.parse_skill_metadata('---\nname: valid\ndescription: ' + 'x' * 1025 + '\n---\n', 'valid')


class RecoveryContractTests(unittest.TestCase):
    rewrite = distribution_tests.DistributionTests.rewrite

    def setUp(self):
        distribution_tests.DistributionTests.setUp(self)
        installer.install(self.archive, self.project)
        self.destination = self.project / '.agents/skills'
        self.changed = self.rewrite({'skills/develop/prd.md': b'Changed first',
                                     'skills/review/code.md': b'Changed second'})

    def test_persistent_restore_failure_retains_original_backups(self):
        original = os.replace

        def fail(source, target):
            if str(source).endswith(('/new/review', '/backup/review')):
                raise OSError('Synthetic persistent recovery failure')
            return original(source, target)

        with patch('distribution.install.os.replace', side_effect=fail):
            with self.assertRaises(OSError):
                installer.install(self.changed, self.project, upgrade=True)
        backups = list(self.destination.glob('.skills-install-*/backup/review/code.md'))
        self.assertTrue(backups, 'Failed restoration must not erase recoverable originals')

    def test_backup_move_with_lost_acknowledgement_preserves_original(self):
        original = os.replace
        before = (self.destination / 'develop/SKILL.md').read_bytes()

        def lose_acknowledgement(source, target):
            result = original(source, target)
            if Path(source).parent == self.destination.resolve() and Path(source).name == 'develop' and Path(target).parent.name == 'backup':
                raise OSError('Synthetic lost backup acknowledgement')
            return result

        with patch('distribution.install.os.replace', side_effect=lose_acknowledgement):
            with self.assertRaises(OSError):
                installer.install(self.changed, self.project, upgrade=True)
        restored = self.destination / 'develop/SKILL.md'
        retained = list(self.destination.glob('.skills-install-*/backup/develop/SKILL.md'))
        self.assertTrue(restored.is_file() or retained, 'Backup movement failure must not destroy originals')
        self.assertEqual((restored if restored.is_file() else retained[0]).read_bytes(), before)

    def test_competing_edit_survives_rollback(self):
        original = os.replace
        marker = self.destination / 'develop/competing.txt'

        def fail(source, target):
            if str(source).endswith('/new/review'):
                marker.write_text('Preserve the synthetic competing edit')
                raise OSError('Synthetic second replacement failure')
            return original(source, target)

        with patch('distribution.install.os.replace', side_effect=fail):
            with self.assertRaises(OSError):
                installer.install(self.changed, self.project, upgrade=True)
        self.assertTrue(marker.is_file(), 'Rollback must not delete another writer\'s edits')
        self.assertTrue(list(self.destination.glob('.skills-install-*/backup/develop/SKILL.md')))

    def test_competing_receipt_is_not_overwritten(self):
        original = os.replace
        receipt = self.destination / installer.RECEIPT
        external = b'{"external":"preserve"}'

        def change(source, target):
            result = original(source, target)
            if str(source).endswith('/new/review'):
                receipt.write_bytes(external)
            return result

        with patch('distribution.install.os.replace', side_effect=change):
            with self.assertRaises((ValueError, OSError)):
                installer.install(self.changed, self.project, upgrade=True)
        self.assertEqual(receipt.read_bytes(), external)

    def test_post_commit_cleanup_failure_reports_committed_result(self):
        original = installer.shutil.rmtree

        def fail(path, *arguments, **kwargs):
            if Path(path).name.startswith('.skills-install-'):
                raise OSError('Synthetic cleanup failure')
            return original(path, *arguments, **kwargs)

        with patch('distribution.install.shutil.rmtree', side_effect=fail):
            result = installer.install(self.changed, self.project, upgrade=True)
        self.assertTrue(result.get('committed'))
        self.assertTrue(result.get('recovery_location'))
        self.assertEqual((self.destination / 'develop/prd.md').read_bytes(), b'Changed first')

    def test_replaced_lock_is_preserved(self):
        original = os.replace
        lock = self.destination / '.mdbecker-skills.lock'

        def change(source, target):
            result = original(source, target)
            if Path(target).name == installer.RECEIPT:
                lock.unlink()
                lock.write_text('Synthetic replacement lock')
            return result

        with patch('distribution.install.os.replace', side_effect=change):
            installer.install(self.changed, self.project, upgrade=True)
        self.assertTrue(lock.exists(), 'Only this invocation\'s unchanged lock may be removed')

    def test_successful_receipt_replace_with_lost_acknowledgement_is_not_rolled_back(self):
        original = os.replace

        def lose_acknowledgement(source, target):
            result = original(source, target)
            if Path(target).name == installer.RECEIPT:
                raise OSError('Synthetic lost commit acknowledgement')
            return result

        with patch('distribution.install.os.replace', side_effect=lose_acknowledgement):
            result = installer.install(self.changed, self.project, upgrade=True)
        self.assertTrue(result.get('committed'))
        self.assertEqual((self.destination / 'develop/prd.md').read_bytes(), b'Changed first')

    def test_failed_rollback_cleanup_reports_retained_location(self):
        original_replace = os.replace
        original_remove = installer.shutil.rmtree

        def fail_replace(source, target):
            if str(source).endswith('/new/review'):
                raise OSError('Synthetic replacement failure')
            return original_replace(source, target)

        def fail_remove(path, *arguments, **kwargs):
            if Path(path).name.startswith('.skills-install-'):
                raise OSError('Synthetic cleanup failure')
            return original_remove(path, *arguments, **kwargs)

        with patch('distribution.install.os.replace', side_effect=fail_replace), \
                patch('distribution.install.shutil.rmtree', side_effect=fail_remove):
            with self.assertRaisesRegex(OSError, 'recovery location'):
                installer.install(self.changed, self.project, upgrade=True)


if __name__ == '__main__':
    unittest.main()
