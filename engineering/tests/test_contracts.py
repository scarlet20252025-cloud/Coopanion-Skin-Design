"""Negative fixtures verify that the handoff rejects unsafe production changes."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('project', ROOT/'engineering/tools/project.py')
project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project)

class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'scratch').mkdir(exist_ok=True)
        cls.tmp = tempfile.TemporaryDirectory(prefix='contract-test-', dir=ROOT/'scratch')
        cls.pack = Path(cls.tmp.name)/'pack'
        shutil.copytree(ROOT/'packs/gpt-dragon-v005-r25', cls.pack)
        cls.originals = {name:(cls.pack/name).read_bytes() for name in ['figure.json','model.json','part-registration.json','figure.js']}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        for name, data in self.originals.items():
            (self.pack/name).write_bytes(data)

    def modify(self, file, fn):
        p = self.pack/file
        value = json.loads(p.read_text(encoding='utf-8'))
        fn(value)
        p.write_text(json.dumps(value), encoding='utf-8')

    def result(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = project.check(SimpleNamespace(pack=str(self.pack.relative_to(ROOT)), contract='engineering/current-project.json', strict_assets=True))
        return code, json.loads(out.getvalue())

    def reject(self, fragment):
        code, result = self.result()
        self.assertEqual(code, 1)
        self.assertTrue(any(fragment in e for e in result['errors']), result)

    def test_current_pack_passes(self):
        self.assertEqual(self.result()[0], 0)

    def test_missing_action_duration(self):
        self.modify('figure.json', lambda m:m['vocab'][0].pop('seconds'))
        self.reject('Invalid duration')

    def test_arm_shear_even_when_embedded_matches(self):
        self.modify('part-registration.json', lambda r:r['arm-left'].__setitem__(2, .2))
        reg = json.loads((self.pack/'part-registration.json').read_text())
        self.modify('model.json', lambda m:m.update(part_registration=reg))
        self.reject('Arm shear')

    def test_embedded_registration_drift(self):
        self.modify('part-registration.json', lambda r:r['arm-left'].__setitem__(4, 333))
        self.reject('Embedded registration')

    def test_extra_fetch_blocked_by_csp(self):
        with (self.pack/'figure.js').open('a', encoding='utf-8') as f:
            f.write("\nfetch(new URL('part-registration.json',base));\n")
        self.reject('blocked by host CSP')

    def test_missing_module(self):
        with (self.pack/'figure.js').open('a', encoding='utf-8') as f:
            f.write("\nimport {x} from './missing-module.js';\n")
        self.reject('Missing module dependency')

    def test_candidate_path_escape_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonreserved'):
            project.candidate(SimpleNamespace(id='../escape', name='test', author='test'))

if __name__ == '__main__':
    unittest.main()
