"""Catch actual handoff hazards: stale evidence, distorted registration, incomplete QA."""
from pathlib import Path
import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engineering/tools'))
import project,flow,qa

class EvidenceTests(unittest.TestCase):
    def valid_data(self):
        samples=[{'key':f'{d}:{phase}','phase':phase,'facing':d,'layout':{'mode':'drag' if phase=='held' else 'idle'}} for d in [1,-1] for phase in ['held','recovery']]
        return {'schema':2,'pack_fingerprint':'fixture','expected':[s['key'] for s in samples],'samples':samples,'checks':[{'accepted':True}]}

    def test_missing_sample_rejected(self):
        d=self.valid_data();d['samples'].pop();self.assertIn('Missing/duplicate/unexpected sample coverage',qa.validate_data(d))

    def test_no_checks_rejected(self):
        d=self.valid_data();d['checks']=[];self.assertTrue(qa.validate_data(d))

    def test_fake_drag_rejected(self):
        d=self.valid_data()
        for s in d['samples']:s['layout']['mode']='idle'
        self.assertIn('Missing actual dragged state',qa.validate_data(d))

    def test_nan_rejected(self):
        d=self.valid_data();d['samples'][0]['layout']['x']=float('nan');self.assertIn('Nonfinite values',qa.validate_data(d))

    def test_stale_and_missing_evidence(self):
        (ROOT/'scratch').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'scratch') as tmp:
            p=Path(tmp);pack=p/'pack';pack.mkdir();(pack/'a.js').write_text('old')
            raw=p/'raw.json';flow.write(raw,self.valid_data())
            flow.write(p/'qa.json',{'pack_fingerprint':flow.fingerprint(pack),'input_file':raw.relative_to(ROOT).as_posix(),'input_sha256':project.sha(raw)})
            self.assertTrue(flow.current_evidence(p,pack)['qa']['current'])
            (pack/'a.js').write_text('new');self.assertFalse(flow.current_evidence(p,pack)['qa']['current'])
            (pack/'a.js').write_text('old');raw.unlink();self.assertFalse(flow.current_evidence(p,pack)['qa']['current'])

    def test_repair_registration_updates_both_files_and_keeps_scale(self):
        job='test-registration-fixture';p=ROOT/'scratch/jobs'/job;candidate=ROOT/'scratch/candidates'/job
        self.assertFalse(p.exists());self.assertFalse(candidate.exists())
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                flow.start(SimpleNamespace(job=job,part='arm',kind='motion',request='test'))
                flow.registration(SimpleNamespace(job=job,part='arm-left',dx=2,dy=-1,scale=1,angle=0))
            m=project.read(candidate/'model.json');r=project.read(candidate/'part-registration.json')
            self.assertEqual(m['part_registration'],r);self.assertEqual(r['arm-left'][0],r['arm-left'][3])
            self.assertNotEqual(flow.fingerprint(candidate),project.read(p/'job.json')['baseline_fingerprint'])
            with self.assertRaisesRegex(ValueError,'QA|qa'):
                flow.package(SimpleNamespace(job=job))
        finally:
            # Only exact fixture paths created above, inside the repository scratch directory.
            for target in [p,candidate]:
                assert target.resolve().is_relative_to((ROOT/'scratch').resolve())
                if target.exists():shutil.rmtree(target)

class RegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:import numpy
        except ImportError:raise unittest.SkipTest('NumPy optional; uv run --project engineering for image-math tests')

    def test_similarity_recovers_uniform_rotation_translation(self):
        from asset import similarity
        import numpy as np
        x=np.array([[0,0],[10,0],[0,10],[5,5]])
        rotation=np.array([[0,1],[-1,0]])
        y=x@rotation*2+[30,40]
        matrix,metrics=similarity(x,y,.001)
        self.assertTrue(np.allclose(matrix,[0,2,-2,0,30,40]));self.assertLess(metrics['max_residual_px'],.001)

    def test_collinear_or_mismatched_landmarks_fail(self):
        from asset import similarity
        with self.assertRaises(ValueError):similarity([[0,0],[1,1],[2,2]],[[0,0],[1,1],[2,2]],2)
        with self.assertRaises(ValueError):similarity([[0,0],[10,0],[0,10]],[[0,0],[40,0],[0,10]],.1)

    def test_blank_and_wrong_size_qa_images_fail(self):
        from PIL import Image
        import base64
        for size,fill in [((32,32),(0,0,0,0)),((8,8),(255,255,255,255))]:
            d=EvidenceTests().valid_data();d['viewport']=[32,32]
            buf=io.BytesIO();Image.new('RGBA',size,fill).save(buf,format='PNG')
            for s in d['samples']:s['png']='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
            with tempfile.TemporaryDirectory(dir=ROOT/'scratch') as tmp:
                p=Path(tmp);flow.write(p/'raw.json',d)
                self.assertFalse(qa.build(p/'raw.json',p/'qa')['machine_passed'])

    def test_new_character_rejects_missing_expression_before_writing(self):
        from make_layer_fixture import make
        from layered import compile_spec
        with tempfile.TemporaryDirectory(dir=ROOT/'scratch') as tmp:
            spec_path=make(tmp);spec=project.read(spec_path)
            spec['parts'][-1]['variants'].pop('dizzy');flow.write(spec_path,spec)
            with self.assertRaisesRegex(ValueError,'Head needs'):
                compile_spec(spec_path,'rejected-new-character-test')
            self.assertFalse((ROOT/'scratch/candidates/rejected-new-character-test').exists())

if __name__=='__main__':unittest.main()
