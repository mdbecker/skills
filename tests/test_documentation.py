from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReadmeTests(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / 'README.md').read_text()

    def test_each_skill_has_the_same_documentation_structure_and_all_modes(self):
        expected = {
            'Develop': {'iterate', 'bdd', 'prd', 'prompt', 'backlog', 'validate-repo'},
            'Review': {'code', 'smells', 'discuss'},
            'Research': {'report create', 'report update'},
        }
        sections = re.findall(r'^### (Develop|Review|Research)\n(.*?)(?=^### |^## |\Z)',
                              self.readme, re.M | re.S)
        self.assertEqual([name for name, content in sections], list(expected))
        for name, content in sections:
            with self.subTest(skill=name):
                self.assertEqual(re.findall(r'^#### (.+)$', content, re.M),
                                 ['Purpose', 'Modes', 'Examples', 'Boundaries'])
                self.assertEqual(set(re.findall(r'^\| `([^`]+)` \|', content, re.M)), expected[name])
                self.assertIn('```text\n/' + name.lower(), content)

    def test_local_links_and_fragments_resolve_to_current_sources(self):
        for target in re.findall(r'\]\(([^)]+)\)', self.readme):
            if '://' in target:
                continue
            relative, separator, fragment = target.partition('#')
            source = ROOT / relative if relative else ROOT / 'README.md'
            with self.subTest(target=target):
                self.assertTrue(source.resolve().is_relative_to(ROOT))
                self.assertTrue(source.is_file())
                if separator:
                    content = source.read_text()
                    headings = re.findall(r'^#{1,6} (.+)$', content, re.M)
                    anchors = {re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
                               for heading in headings}
                    anchors.update(re.findall(r'<a id="([^"]+)"', content))
                    self.assertIn(fragment, anchors)

    def test_retired_entrypoints_are_not_documented_as_commands_or_skills(self):
        self.assertNotRegex(self.readme, r'(?m)^#{1,6} (?:Iterate|Debate)$')
        self.assertNotRegex(self.readme, r'`/(?:iterate|debate)(?:[ `])')
        self.assertNotRegex(self.readme, r'(?m)^/(?:iterate|debate)(?:\s|$)')
        self.assertNotIn('skills/iterate/', self.readme)
        self.assertNotIn('skills/debate/', self.readme)


if __name__ == '__main__':
    unittest.main()
