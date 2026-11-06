import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from distribution.install import HOST_DIRS, install, read_archive, RECEIPT
from scripts.build_skills import build, payload, release_ready, ROOT
from tests.test_preparation import fixture_payload


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.project = self.workspace / "project"
        self.project.mkdir()
        self.archive = self.workspace / "skills.zip"
        self.manifest = build(self.archive, "first")

    def rewrite(self, edits=None, extras=None, update_hashes=True):
        with zipfile.ZipFile(self.archive) as archive:
            contents = {entry.filename: archive.read(entry) for entry in archive.infolist()}
        contents.update(edits or {})
        manifest = json.loads(contents["manifest.json"])
        manifest["version"] = "second"
        if update_hashes:
            manifest["files"] = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items() if name != "manifest.json"}
        contents["manifest.json"] = json.dumps(manifest).encode()
        target = self.workspace / "changed.zip"
        with zipfile.ZipFile(target, "w") as archive:
            for name, content in contents.items():
                archive.writestr(name, content)
            for name, content in extras or []:
                archive.writestr(name, content)
        return target

    def test_export_reproducible_and_exact_inventory(self):
        second = self.workspace / "second.zip"
        build(second, "first")
        self.assertEqual(self.archive.read_bytes(), second.read_bytes())
        self.assertEqual([entry["name"] for entry in self.manifest["skills"]], ["develop", "review", "research"])
        self.assertEqual(len(json.loads((ROOT / "inventory.json").read_text())["capabilities"]), 8)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertNotIn("evaluations/expected.json", archive.namelist())
            self.assertFalse(any(".ai-state" in path or "__pycache__" in path for path in archive.namelist()))
        read_archive(self.archive)

    def test_only_parent_skills_are_discovered_and_exported(self):
        names = {entry['name'] for entry in self.manifest['skills']}
        self.assertEqual(names, {'develop', 'review', 'research'})
        discovery = ROOT / '.agents/skills'
        actual = {entry.name for entry in discovery.iterdir() if entry.is_symlink() or entry.is_dir()}
        self.assertEqual(actual, names)
        for name in names:
            link = discovery / name
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), ROOT / name)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertFalse(any(path.startswith(('skills/iterate/', 'skills/debate/'))
                                 for path in archive.namelist()))
            self.assertIn('skills/develop/iterate.md', archive.namelist())
            self.assertIn('skills/develop/scripts/manifest.py', archive.namelist())
            self.assertIn('skills/review/debate.md', archive.namelist())

    def test_parent_upgrade_preserves_separately_installed_skills(self):
        install(self.archive, self.project)
        markers = {}
        for name in ['iterate', 'debate']:
            marker = self.project / '.agents/skills' / name / 'SKILL.md'
            marker.parent.mkdir()
            marker.write_text('Separately installed; preserve this content.\n')
            markers[marker] = marker.read_bytes()
        with zipfile.ZipFile(self.archive) as bundle:
            original = bundle.read('skills/develop/prd.md')
        changed = self.rewrite({'skills/develop/prd.md': original + b'\nUpdated fixture.\n'})
        result = install(changed, self.project, upgrade=True)
        self.assertEqual(result['installed'], ['develop'])
        for marker, content in markers.items():
            self.assertEqual(marker.read_bytes(), content)

    def test_preview_install_reinstall_and_standalone_helper(self):
        marker = self.project / "keep.txt"
        marker.write_text("unchanged")
        preview = install(self.archive, self.project, selected=["develop"], dry_run=True)
        self.assertEqual(preview["installed"], [])
        self.assertEqual(preview["planned"], ["develop"])
        self.assertFalse((self.project / ".agents").exists())
        result = install(self.archive, self.project, selected=["develop"])
        self.assertEqual(result["installed"], ["develop"])
        self.assertEqual(install(self.archive, self.project, selected=["develop"])["installed"], [])
        helper = self.project / ".agents/skills/develop/scripts/manifest.py"
        self.archive.unlink()
        outcome = subprocess.run([sys.executable, str(helper), "init", "standalone", "--impact", "Installed helper survives"],
                                 cwd=self.project, capture_output=True, text=True)
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        self.assertEqual(marker.read_text(), "unchanged")
        self.assertTrue((self.project / ".ai-state/standalone.json").is_file())
        self.assertFalse((self.project / ".agents/skills/iterate").exists())

    def test_required_skill_documents_are_beside_entrypoints_and_not_ignored(self):
        inventory = json.loads((ROOT / "inventory.json").read_text())
        sources = []
        for name in inventory["parents"]:
            sources.append(name + "/SKILL.md")
            for relative in inventory["owned_resources"][name]:
                self.assertNotIn("references", Path(relative).parts)
                if relative.endswith(".md"):
                    self.assertEqual(Path(relative).parent, Path("."))
                sources.append(name + "/" + relative)
        result = subprocess.run(["git", "check-ignore", "--no-index", *sources],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_export_is_complete_without_local_reference_directories(self):
        inventory, expected, inputs = payload(ROOT)
        source_root = self.workspace / "canonical"
        for relative in inputs:
            self.assertNotIn("references", Path(relative).parts)
            target = source_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        self.assertFalse(any(source_root.rglob("references")))
        actual_inventory, actual, actual_inputs = fixture_payload(source_root)
        self.assertEqual(actual_inventory, inventory)
        self.assertEqual(actual, expected)
        self.assertEqual(actual_inputs, inputs)
        for name in inventory["parents"]:
            directory = source_root / name / "references"
            directory.mkdir()
            for relative in inventory["owned_resources"][name]:
                (directory / Path(relative).name).write_text("Local-only source; do not export.\n")
        ignored_inventory, ignored, ignored_inputs = fixture_payload(source_root)
        self.assertEqual(ignored_inventory, inventory)
        self.assertEqual(ignored, expected)
        self.assertEqual(ignored_inputs, inputs)
        self.assertFalse(any("references" in Path(relative).parts for relative in ignored))

    def test_claude_layout_is_installation_not_invocation(self):
        result = install(self.archive, self.project, host="claude", selected=["research"])
        self.assertTrue((self.project / ".claude/skills/research/SKILL.md").is_file())
        self.assertFalse((self.project / ".agents").exists())
        self.assertEqual(result["qualification"]["hosts"]["claude"]["invocation"], "not_run")

    def test_standalone_review_preserves_methods_and_source_coverage(self):
        inventory = json.loads((ROOT / "inventory.json").read_text())
        references = inventory["owned_resources"]["review"]
        for host, host_directory in HOST_DIRS.items():
            with self.subTest(host=host):
                project = self.workspace / ("review-" + host)
                project.mkdir()
                install(self.archive, project, host=host, selected=["review"])
                directory = project / host_directory / "review"
                installed = {path.name for path in directory.parent.iterdir() if path.is_dir()}
                self.assertEqual(installed, {"review"})
                for relative in references:
                    source = ROOT / "review" / relative
                    target = directory / relative
                    with zipfile.ZipFile(self.archive) as bundle:
                        self.assertEqual(target.read_bytes(), bundle.read('skills/review/' + relative))
                    self.assertEqual(self.manifest["source_inputs"]["review/" + relative],
                                     hashlib.sha256(source.read_bytes()).hexdigest())
                for document in directory.rglob("*.md"):
                    for reference in re.findall(r"\]\(([^)]+)\)", document.read_text()):
                        if "://" in reference or reference.startswith("#"):
                            continue
                        target = (document.parent / reference.split("#", 1)[0]).resolve()
                        self.assertTrue(target.is_relative_to(directory.resolve()), reference)
                        self.assertTrue(target.is_file(), reference)
                self.assertEqual(install(self.archive, project, host=host, selected=["review"])["installed"], [])
                self.assertEqual(self.manifest["qualification"]["model_quality"], "not_run")

    def test_external_checksum_fails_without_writes(self):
        with self.assertRaisesRegex(ValueError, "Archive SHA"):
            install(self.archive, self.project, expected_sha256="0" * 64)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_file_corruption_rejected_before_writes(self):
        changed = self.rewrite({"skills/develop/SKILL.md": b"corrupt"}, update_hashes=False)
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            install(changed, self.project)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_traversal_absolute_backslash_and_case_collision(self):
        for path in ("../outside", "/outside", "skills\\escape", "Skills/develop/SKILL.md"):
            with self.subTest(path=path):
                changed = self.rewrite(extras=[(path, b"bad")])
                with self.assertRaises(ValueError):
                    install(changed, self.project)
                self.assertEqual(list(self.project.iterdir()), [])

    def test_duplicate_entries_and_symlink_payload(self):
        changed = self.rewrite(extras=[("README.md", b"duplicate")])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            install(changed, self.project)
        symbolic = zipfile.ZipInfo("skills/develop/link")
        symbolic.external_attr = (stat.S_IFLNK | 0o777) << 16
        changed = self.rewrite(extras=[(symbolic, b"/outside")])
        with self.assertRaisesRegex(ValueError, "regular files"):
            install(changed, self.project)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_missing_bundled_reference(self):
        changed = self.rewrite({"skills/develop/SKILL.md": (ROOT / "develop/SKILL.md").read_bytes() + b"\n[missing](resources/absent.md)"})
        with self.assertRaisesRegex(ValueError, "bundled reference"):
            install(changed, self.project)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_target_parent_symlink_rejected(self):
        outside = self.workspace / "outside"
        outside.mkdir()
        (self.project / ".agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            install(self.archive, self.project)
        self.assertEqual(list(outside.iterdir()), [])

    def test_entrypoint_name_must_match_declared_inventory(self):
        content = (ROOT / "develop/SKILL.md").read_bytes().replace(b"name: develop", b"name: other")
        changed = self.rewrite({"skills/develop/SKILL.md": content})
        with self.assertRaisesRegex(ValueError, "metadata"):
            install(changed, self.project)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_existing_skill_symlink_rejected(self):
        destination = self.project / ".agents/skills"
        destination.mkdir(parents=True)
        outside = self.workspace / "outside"
        outside.mkdir()
        (destination / "develop").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            install(self.archive, self.project)
        self.assertEqual(list(outside.iterdir()), [])

    def test_unmanaged_conflict_leaves_unrelated_work(self):
        destination = self.project / ".agents/skills/develop"
        destination.mkdir(parents=True)
        (destination / "SKILL.md").write_text("my skill")
        with self.assertRaisesRegex(ValueError, "Conflict"):
            install(self.archive, self.project)
        self.assertEqual((destination / "SKILL.md").read_text(), "my skill")
        self.assertFalse((destination.parent / "review").exists())

    def test_upgrade_only_unchanged_managed_skill(self):
        install(self.archive, self.project, selected=["develop"])
        entry = "skills/develop/prd.md"
        with zipfile.ZipFile(self.archive) as bundle:
            original = bundle.read(entry)
        changed = self.rewrite({entry: original + b"\nUpdated fixture.\n"})
        with self.assertRaises(ValueError):
            install(changed, self.project, selected=["develop"])
        result = install(changed, self.project, selected=["develop"], upgrade=True)
        self.assertEqual(result["installed"], ["develop"])
        target = self.project / ".agents/skills/develop/prd.md"
        self.assertIn(b"Updated fixture", target.read_bytes())
        target.write_text("local edit")
        with self.assertRaisesRegex(ValueError, "local modifications"):
            install(self.archive, self.project, selected=["develop"], upgrade=True)
        self.assertEqual(target.read_text(), "local edit")

    def test_added_local_file_blocks_upgrade(self):
        install(self.archive, self.project, selected=["develop"])
        marker = self.project / ".agents/skills/develop/my-notes.md"
        marker.write_text("keep")
        with self.assertRaises(ValueError):
            install(self.archive, self.project, selected=["develop"], upgrade=True)
        self.assertEqual(marker.read_text(), "keep")

    def test_failed_second_replacement_rolls_back_and_preserves_receipt(self):
        install(self.archive, self.project)
        before = {path.relative_to(self.project): path.read_bytes() for path in self.project.rglob("*") if path.is_file()}
        changed = self.rewrite({"skills/develop/prd.md": b"Changed first",
                                "skills/review/code.md": b"Changed second"})
        original_replace = os.replace

        def fail_second(source, target):
            if str(source).endswith("/new/review"):
                raise OSError("simulated second-write failure")
            return original_replace(source, target)

        with patch("distribution.install.os.replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "second-write"):
                install(changed, self.project, upgrade=True)
        after = {path.relative_to(self.project): path.read_bytes() for path in self.project.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_invalid_receipts_and_existing_lock(self):
        install(self.archive, self.project)
        receipt = self.project / ".agents/skills" / RECEIPT
        original = receipt.read_bytes()
        for content in (b"null", b"[]", b'{"schema_version":1,"schema_version":2}'):
            receipt.write_bytes(content)
            with self.assertRaises(ValueError):
                install(self.archive, self.project)
        receipt.write_bytes(original)
        lock = receipt.parent / ".mdbecker-skills.lock"
        lock.write_text("another installer")
        with self.assertRaises(FileExistsError):
            install(self.archive, self.project)
        self.assertEqual(lock.read_text(), "another installer")
        self.assertEqual(receipt.read_bytes(), original)

    def test_unknown_host_and_selection_are_read_only(self):
        with self.assertRaises(ValueError):
            install(self.archive, self.project, host="unknown")
        with self.assertRaises(ValueError):
            install(self.archive, self.project, selected=["missing"])
        self.assertEqual(list(self.project.iterdir()), [])

    def test_unverified_quality_blocks_stable_release_readiness(self):
        self.assertFalse(release_ready(self.manifest["qualification"], self.manifest["source_inputs"]))
        status = {key: "passed" for key in ("release_approval", "model_protocol_approval", "manual_acceptance", "deterministic", "model_quality", "reference_fidelity", "transfer")}
        status["hosts"] = {host: {key: "passed" for key in ("installation", "invocation", "debate")} for host in ("codex", "claude")}
        self.assertFalse(release_ready(status, self.manifest["source_inputs"]))
        status["source_inputs_sha256"] = hashlib.sha256(json.dumps(self.manifest["source_inputs"], sort_keys=True).encode()).hexdigest()
        self.assertTrue(release_ready(status, self.manifest["source_inputs"]))
        status["hosts"]["claude"]["debate"] = "not_run"
        self.assertFalse(release_ready(status, self.manifest["source_inputs"]))
        status["hosts"]["claude"]["debate"] = "passed"
        status["hosts"]["claude"]["invocation"] = "not_run"
        self.assertFalse(release_ready(status, self.manifest["source_inputs"]))

    def test_fixture_expectations_are_evaluator_only(self):
        fixtures = json.loads((ROOT / "evaluations/fixtures.json").read_text())
        expected = json.loads((ROOT / "evaluations/expected.json").read_text())
        self.assertEqual({entry["id"] for entry in fixtures["cases"]}, set(expected["cases"]))
        self.assertTrue(expected["evaluator_only"])
        self.assertFalse(any("expected" in entry for entry in fixtures["cases"]))
        artifacts = json.loads((ROOT / "evaluations/artifacts.json").read_text())
        self.assertEqual(set(artifacts["cases"]), set(expected["cases"]))
        self.assertTrue(artifacts["synthetic_only"])
        with zipfile.ZipFile(self.archive) as archive:
            self.assertFalse(any(path.startswith("evaluations/") for path in archive.namelist()))

    def test_archive_limits_and_file_directory_collision(self):
        for limits in ({"MAX_FILES": 1}, {"MAX_BYTES": 1}):
            with self.subTest(limits=limits), patch.multiple("distribution.install", **limits):
                with self.assertRaisesRegex(ValueError, "limit"):
                    install(self.archive, self.project)
        changed = self.rewrite(extras=[("skills/develop/resources", b"file, not directory")])
        with self.assertRaisesRegex(ValueError, "parent directory"):
            install(changed, self.project)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_stable_build_blocked_but_explicit_preview_can_build(self):
        output = self.workspace / "release.zip"
        original_run = subprocess.run

        def clean_source(command, *arguments, **kwargs):
            if command == ['git', 'rev-parse', 'HEAD']:
                return SimpleNamespace(stdout='a' * 40)
            if command == ['git', 'status', '--porcelain']:
                return SimpleNamespace(stdout='')
            return original_run(command, *arguments, **kwargs)
        with patch("scripts.build_skills.subprocess.run", side_effect=clean_source):
            with self.assertRaisesRegex(ValueError, "release blocked"):
                build(output, "v0.1.0", release=True)
        self.assertFalse(output.exists())
        status = dict(self.manifest['qualification'])
        status['release_approval'] = 'passed'
        status['source_inputs_sha256'] = hashlib.sha256(json.dumps(self.manifest['source_inputs'], sort_keys=True).encode()).hexdigest()
        with patch("scripts.build_skills.subprocess.run", side_effect=clean_source), \
                patch('scripts.build_skills.qualification', return_value=status):
            manifest = build(output, "v0.1.0-rc.1", release=True, prerelease=True)
        self.assertTrue(manifest["prerelease"])
        self.assertEqual(manifest["qualification"]["model_quality"], "not_run")

    def test_release_workflow_pins_and_no_asset_clobber(self):
        import yaml
        workflow = yaml.load((ROOT / ".github/workflows/release.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertIn("push", workflow["on"])
        self.assertIn("workflow_dispatch", workflow["on"])
        self.assertEqual(workflow["permissions"]["contents"], "read")
        steps = workflow["jobs"]["release"]["steps"]
        for step in steps:
            if "uses" in step:
                self.assertRegex(step["uses"], r"@[0-9a-f]{40}$")
        publication = next(step["run"] for step in steps if "gh release create" in step.get("run", ""))
        self.assertNotIn("--clobber", publication)
        self.assertLess(publication.index("gh release upload"), publication.index("--draft=false"))

    def copied_sources(self):
        root = self.workspace / "source-copy"
        unused_inventory, unused_files, inputs = payload(ROOT)
        for identity in inputs:
            target = root / identity
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / identity).read_bytes())
        return root

    def test_explicit_inventory_does_not_sweep_private_files(self):
        root = self.copied_sources()
        (root / "resources/credentials.env").write_text("synthetic secret")
        (root / "resources/restricted-data.json").write_text("synthetic restricted payload")
        unused_inventory, files, inputs = fixture_payload(root)
        self.assertFalse(any("credentials.env" in name or "restricted-data.json" in name for name in files))
        self.assertNotIn("resources/credentials.env", inputs)
        self.assertNotIn("resources/restricted-data.json", inputs)

    def test_source_mutation_during_export_is_rejected(self):
        root = self.copied_sources()
        source = root / "resources/policy.md"
        original_read = Path.read_bytes
        changed = False

        def mutate_after_capture(path):
            nonlocal changed
            content = original_read(path)
            if path == source and not changed:
                changed = True
                path.write_bytes(content + b"\nConcurrent edit.\n")
            return content

        with patch.object(Path, "read_bytes", mutate_after_capture):
            with self.assertRaisesRegex(ValueError, "changed during export"):
                fixture_payload(root)

    def test_checksum_symlink_does_not_modify_outside_target(self):
        output = self.workspace / "target.zip"
        outside = self.workspace / "keep.txt"
        outside.write_text("unchanged")
        output.with_suffix(".zip.sha256").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            build(output)
        self.assertEqual(outside.read_text(), "unchanged")
        self.assertFalse(output.exists())

    def test_synthetic_report_graph_preserves_evidence_and_failed_output(self):
        artifacts = json.loads((ROOT / "evaluations/artifacts.json").read_text())["cases"]["report-transfer"]
        project = self.workspace / "report-project"
        for relative, content in artifacts.items():
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        evidence = project / "evidence/cohorts.json"
        original_evidence = evidence.read_bytes()
        (project / "failure.json").unlink()
        result = subprocess.run([sys.executable, "scripts/assemble_report.py"], cwd=project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, "scripts/check_report.py"], cwd=project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = (project / "report.html").read_bytes()
        (project / "failure.json").write_text('{"simulate_assembly_failure":true}')
        result = subprocess.run([sys.executable, "scripts/assemble_report.py"], cwd=project, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(evidence.read_bytes(), original_evidence)
        self.assertEqual((project / "report.html").read_bytes(), before)

    def test_exported_helpers_preserve_registry_boundary_and_recovery_policy(self):
        canonical = (ROOT / 'develop/scripts/manifest.py').read_bytes()
        for name, relative in [('develop', 'scripts/manifest.py')]:
            with self.subTest(package=name):
                project = self.workspace / ('installed-' + name)
                project.mkdir()
                install(self.archive, project, selected=[name])
                helper = project / '.agents/skills' / name / relative
                self.assertEqual(helper.read_bytes(), canonical)
                (project / 'tool.py').write_text('inert')
                outside = self.workspace / ('outside-' + name)
                outside.mkdir()
                (project / 'testbed').symlink_to(outside, target_is_directory=True)
                result = subprocess.run([sys.executable, str(helper), 'tool', 'add', '--name', 'inert',
                                         '--path', 'tool.py', '--desc', 'inert'], cwd=project, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('unsafe registry storage', result.stderr)
                self.assertEqual(list(outside.iterdir()), [])
                result = subprocess.run([sys.executable, str(helper), 'init', 'demo', '--impact', 'restoration'],
                                        cwd=project, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                state = project / '.ai-state/demo.json'
                valid = state.read_bytes()
                damaged = json.loads(valid)
                del damaged['architecture_decisions']
                state.write_text(json.dumps(damaged))
                before = state.read_bytes()
                result = subprocess.run([sys.executable, str(helper), 'status', 'demo'], cwd=project, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('restore a known-good local copy', result.stderr)
                self.assertNotIn('fix by hand', result.stderr)
                self.assertEqual(state.read_bytes(), before)
                state.write_bytes(valid)
                result = subprocess.run([sys.executable, str(helper), 'status', 'demo'], cwd=project, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
