import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_skills import ROOT, payload, prepare


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.source = self.workspace / 'source'
        self.source.mkdir()
        self.inventory, unused_files, inputs = payload(ROOT)
        for relative in inputs:
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        self.receipt = self.source / 'dist/.prepared-resources.json'
        self.lock = self.source / 'dist/.prepared-resources.lock'
        self.policy = self.source / 'develop/resources/policy.md'

    def write_inventory(self):
        (self.source / 'inventory.json').write_text(json.dumps(self.inventory))

    def add_resource(self, name='retired-note.md'):
        relative = 'resources/' + name
        (self.source / relative).write_text('Canonical temporary resource.\n')
        self.inventory['common_resources'].append(relative)
        self.write_inventory()
        return relative

    def snapshot(self):
        result = {}
        paths = [self.receipt]
        for name in self.inventory['parents']:
            directory = self.source / name / 'resources'
            paths.extend(directory.rglob('*'))
        for path in paths:
            relative = path.relative_to(self.source).as_posix()
            if path.is_symlink():
                result[relative] = {'link': os.readlink(path)}
            elif path.is_file():
                result[relative] = {'bytes': path.read_bytes(), 'mode': stat.S_IMODE(path.stat().st_mode)}
        return result

    def seed_receipt(self):
        record = {'schema_version': 1, 'package': 'mdbecker-skills', 'skills': {}}
        for name in self.inventory['parents']:
            files = {}
            for path in (self.source / name / 'resources').rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:
                    files[path.relative_to(self.source / name).as_posix()] = {
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'mode': stat.S_IMODE(path.stat().st_mode),
                    }
            record['skills'][name] = {'files': files}
        self.receipt.parent.mkdir(exist_ok=True)
        self.receipt.write_text(json.dumps(record))
        return record

    def change_source_policy(self):
        source = self.source / 'resources/policy.md'
        source.write_text(source.read_text() + '\nChanged canonical policy.\n')
        return source

    def test_fresh_preparation_records_ownership_and_second_run_is_unchanged(self):
        result = prepare(self.source)
        self.assertEqual(result, self.inventory)
        self.assertTrue(self.receipt.is_file(), 'Preparation must record generated-file ownership')
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['schema_version'], 1)
        self.assertEqual(set(receipt['skills']), set(self.inventory['parents']))
        for name, record in receipt['skills'].items():
            for relative, metadata in record['files'].items():
                path = self.source / name / relative
                self.assertEqual(metadata['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(metadata['mode'], stat.S_IMODE(path.stat().st_mode))
        before = self.snapshot()
        prepare(self.source)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.lock.exists())

    def test_retired_and_relocated_resources_are_removed_only_from_owned_views(self):
        original = self.add_resource()
        prepare(self.source)
        self.inventory['common_resources'].remove(original)
        moved = self.add_resource('moved-note.md')
        self.write_inventory()
        prepare(self.source)
        for name in self.inventory['parents']:
            self.assertFalse((self.source / name / original).exists())
            self.assertEqual((self.source / name / moved).read_bytes(), (self.source / moved).read_bytes())
        self.assertTrue((self.source / original).is_file())

    def test_modified_content_and_modes_conflict_before_any_output_changes(self):
        for change in ['content', 'mode']:
            with self.subTest(change=change):
                prepare(self.source)
                self.seed_receipt()
                if change == 'content':
                    self.policy.write_text('User-edited generated content.\n')
                else:
                    self.policy.chmod(0o400)
                before = self.snapshot()
                self.change_source_policy()
                try:
                    with self.assertRaises(ValueError):
                        prepare(self.source)
                except OSError as error:
                    self.fail(f'Preparation attempted an unsafe write instead of reporting a conflict: {type(error).__name__}')
                self.assertEqual(self.snapshot(), before)
                self.policy.chmod(0o644)
                self.policy.write_bytes((self.source / 'resources/policy.md').read_bytes())
                self.seed_receipt()

    def test_unknown_file_and_missing_receipt_never_authorize_cleanup(self):
        prepare(self.source)
        self.seed_receipt()
        unknown = self.source / 'develop/resources/unowned-notes.txt'
        unknown.write_text('User notes.\n')
        before = self.snapshot()
        with self.assertRaises(ValueError):
            prepare(self.source)
        self.assertEqual(self.snapshot(), before)
        self.receipt.unlink()
        before = self.snapshot()
        with self.assertRaises(ValueError):
            prepare(self.source)
        self.assertEqual(self.snapshot(), before)

    def test_matching_existing_views_can_be_adopted_without_rewriting_files(self):
        prepare(self.source)
        self.receipt.unlink(missing_ok=True)
        before = self.snapshot()
        prepare(self.source)
        self.assertTrue(self.receipt.is_file())
        after = self.snapshot()
        after.pop('dist/.prepared-resources.json')
        self.assertEqual(after, before)

    def test_malformed_receipts_fail_before_replacing_resources(self):
        prepare(self.source)
        original = self.seed_receipt()
        invalid = ['{', '[]', json.dumps(dict(original, schema_version=True)),
                   json.dumps(dict(original, package='wrong-package'))]
        for index, content in enumerate(invalid):
            with self.subTest(case=index):
                self.receipt.write_text(content)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    prepare(self.source)
                self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.lock.exists())

    def test_symlinks_are_rejected_before_other_resources_are_updated(self):
        prepare(self.source)
        self.seed_receipt()
        external = self.workspace / 'external.md'
        external.write_text('Outside content.\n')
        linked = self.source / 'research/resources/project-profile.md'
        linked.unlink()
        linked.symlink_to(external)
        before = self.snapshot()
        self.change_source_policy()
        with self.assertRaises(ValueError):
            prepare(self.source)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(external.read_text(), 'Outside content.\n')

    def test_linked_bookkeeping_and_existing_locks_are_preserved(self):
        external = self.workspace / 'external'
        external.mkdir()
        marker = external / 'keep.txt'
        marker.write_text('Keep.\n')
        (self.source / 'dist').symlink_to(external, target_is_directory=True)
        with self.assertRaises(ValueError):
            prepare(self.source)
        self.assertEqual(list(external.iterdir()), [marker])
        (self.source / 'dist').unlink()
        self.lock.parent.mkdir()
        self.lock.write_text('Other preparer owns this lock.\n')
        with self.assertRaises((ValueError, FileExistsError)):
            prepare(self.source)
        self.assertEqual(self.lock.read_text(), 'Other preparer owns this lock.\n')

    def test_receipt_commit_failure_rolls_back_applied_changes(self):
        prepare(self.source)
        self.seed_receipt()
        before = self.snapshot()
        self.change_source_policy()
        original_replace = os.replace

        def fail_receipt(source, target):
            if Path(target) == self.receipt:
                raise OSError('Receipt commit denied')
            return original_replace(source, target)

        with patch('scripts.build_skills.os.replace', side_effect=fail_receipt):
            with self.assertRaises(OSError):
                prepare(self.source)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.lock.exists())

    def test_concurrent_source_changes_are_preserved_and_generation_is_rolled_back(self):
        prepare(self.source)
        self.seed_receipt()
        before = self.snapshot()
        canonical = self.change_source_policy()
        original_link = os.link
        injected = False

        def change_source(source, target):
            nonlocal injected
            result = original_link(source, target)
            if Path(target) == self.policy and not injected:
                injected = True
                canonical.write_text('Concurrent source edit.\n')
            return result

        with patch('scripts.build_skills.os.link', side_effect=change_source):
            with self.assertRaises(ValueError):
                prepare(self.source)
        self.assertTrue(injected)
        self.assertEqual(canonical.read_text(), 'Concurrent source edit.\n')
        self.assertEqual(self.snapshot(), before)

    def test_concurrent_output_edits_and_recoverable_originals_are_preserved(self):
        prepare(self.source)
        self.seed_receipt()
        original_policy = self.policy.read_bytes()
        original_receipt = self.receipt.read_bytes()
        self.change_source_policy()
        original_link = os.link
        injected = False

        def change_output(source, target):
            nonlocal injected
            result = original_link(source, target)
            if Path(target) == self.policy and not injected:
                injected = True
                self.policy.write_text('Concurrent user edit.\n')
            return result

        with patch('scripts.build_skills.os.link', side_effect=change_output):
            with self.assertRaisesRegex(ValueError, 'recover'):
                prepare(self.source)
        self.assertEqual(self.policy.read_text(), 'Concurrent user edit.\n')
        self.assertEqual(self.receipt.read_bytes(), original_receipt)
        recovered = [path for path in (self.source / 'dist').rglob('*')
                     if path.is_file() and path.read_bytes() == original_policy]
        self.assertTrue(recovered, 'Original generated bytes must remain recoverable')

    def test_caches_are_preserved_but_never_recorded_as_owned(self):
        relative = self.add_resource()
        prepare(self.source)
        cache = self.source / 'develop/resources/__pycache__/cached.pyc'
        cache.parent.mkdir()
        cache.write_bytes(b'Unowned cache')
        self.inventory['common_resources'].remove(relative)
        self.write_inventory()
        prepare(self.source)
        self.assertFalse((self.source / 'develop' / relative).exists())
        self.assertEqual(cache.read_bytes(), b'Unowned cache')
        self.assertTrue(self.receipt.exists())
        self.assertNotIn('__pycache__', self.receipt.read_text())

    def test_prior_ownership_is_not_overridden_by_matching_new_source_bytes(self):
        prepare(self.source)
        self.seed_receipt()
        canonical = self.change_source_policy()
        self.policy.write_bytes(canonical.read_bytes())
        before = self.snapshot()
        with self.assertRaises(ValueError):
            prepare(self.source)
        self.assertEqual(self.snapshot(), before)

    def test_receipt_rejects_escaping_paths_invalid_modes_and_non_json_numbers(self):
        prepare(self.source)
        original = self.seed_receipt()
        invalid = []
        escaped = json.loads(json.dumps(original))
        escaped['skills']['develop']['files']['resources/../../README.md'] = {
            'sha256': '0' * 64, 'mode': 0o644}
        invalid.append(escaped)
        wrong_mode = json.loads(json.dumps(original))
        wrong_mode['skills']['develop']['files']['resources/policy.md']['mode'] = True
        invalid.append(wrong_mode)
        invalid.append(dict(original, extension=float('nan')))
        for index, receipt in enumerate(invalid):
            with self.subTest(case=index):
                self.receipt.write_text(json.dumps(receipt))
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    prepare(self.source)
                self.assertEqual(self.snapshot(), before)

    def test_undeclared_skill_receipts_are_retained_without_touching_their_paths(self):
        prepare(self.source)
        receipt = self.seed_receipt()
        external = self.workspace / 'external'
        external.mkdir()
        marker = external / 'keep.txt'
        marker.write_text('Do not access this retired skill.\n')
        (self.source / 'retired').symlink_to(external, target_is_directory=True)
        receipt['skills']['retired'] = {'files': {'resources/keep.txt': {
            'sha256': '0' * 64, 'mode': 0o644}}}
        self.receipt.write_text(json.dumps(receipt))
        prepare(self.source)
        self.assertEqual(json.loads(self.receipt.read_text())['skills']['retired'], receipt['skills']['retired'])
        self.assertEqual(marker.read_text(), 'Do not access this retired skill.\n')
