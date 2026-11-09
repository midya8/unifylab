import copy,itertools,json,random,unittest,tempfile,subprocess,sys
from pathlib import Path
from unittest.mock import patch
from unifylab.generalization import generalize,verify_generalization
from unifylab.core import apply
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/generalization-controls.json').read_text())

def bank(n,seed):
    rng=random.Random(seed)
    def term(d):
        if not d or rng.random()<.4:return [rng.choice(['amber','blue','clay'])]
        return ['box',term(d-1)] if rng.random()<.5 else ['pair',term(d-1),term(d-1)]
    return [{'terms':[term(3),term(3)]} for _ in range(n)]

def match(pattern,target):
    env={}
    def go(p,t):
        if isinstance(p,str):
            if p in env:return env[p]==t
            env[p]=t;return True
        return isinstance(t,list) and len(p)==len(t) and p[0]==t[0] and all(go(x,y) for x,y in zip(p[1:],t[1:]))
    return env if go(pattern,target) else None

class GeneralizationTests(unittest.TestCase):
    def check(self,d):
        before=copy.deepcopy(d);r=generalize(d);self.assertEqual(before,d);self.assertTrue(verify_generalization(r));self.assertEqual(r,generalize(d))
        self.assertEqual(apply(r['generalization'],r['left_substitution']),d['terms'][0]);self.assertEqual(apply(r['generalization'],r['right_substitution']),d['terms'][1])
        # Swap changes instances, not the normalized generalized shape.
        reverse=generalize({'terms':list(reversed(d['terms']))});self.assertEqual(reverse['generalization'],r['generalization']);self.assertEqual(reverse['left_substitution'],r['right_substitution'])
        return r
    def test_controls_and_seeded_reconstruction(self):
        for c in CONTROLS:self.check(c['input'])
        for d in bank(600,8197):self.check(d)
    def test_reuse_order_and_more_than_six_output_variables(self):
        r=self.check(CONTROLS[0]['input']);self.assertEqual(r['generalization'],['pair','?g0','?g0']);self.assertEqual(r['steps'][1]['source_step'],0)
        for i in [2,3]:self.assertEqual(self.check(CONTROLS[i]['input'])['generalization'],['pair','?g0','?g1'])
        self.assertEqual(len(self.check(CONTROLS[7]['input'])['pairs']),8)
    def test_bounded_common_generalizer_factorization(self):
        # Matcher is independent of the memoized paired traversal. Not a universal proof.
        atoms=['?u','?v',['amber'],['blue'],['clay']]
        pool=atoms+[['box',a] for a in atoms]+[['pair',a,b] for a,b in itertools.product(atoms,repeat=2)]
        pool+= [['pair',['box',a],b] for a,b in itertools.product(atoms,repeat=2)]
        cases=0
        for d in [c['input'] for c in CONTROLS]+bank(150,663):
            g=generalize(d)['generalization']
            for p in pool:
                if match(p,d['terms'][0]) is not None and match(p,d['terms'][1]) is not None:
                    self.assertIsNotNone(match(p,g),(p,g,d));cases+=1
        self.assertGreater(cases,300)
    def test_exhaustive_small_ground_pairs_and_pattern_candidates(self):
        pool=[['amber'],['blue'],['box',['amber']],['box',['blue']],['pair',['amber'],['amber']],['pair',['amber'],['blue']],['pair',['blue'],['amber']],['pair',['blue'],['blue']]]
        for a,b in itertools.product(pool,repeat=2):self.check({'terms':[a,b]})
    def test_every_certificate_field_and_record_forgery(self):
        for c in CONTROLS:
            r=generalize(c['input'])
            for key in r:
                bad=copy.deepcopy(r);bad[key]=None;self.assertFalse(verify_generalization(bad),key)
            for i,s in enumerate(r['steps']):
                for key in s:
                    bad=copy.deepcopy(r);bad['steps'][i][key]=42;self.assertFalse(verify_generalization(bad),(i,key))
            bad=copy.deepcopy(r);bad['extra']=True;self.assertFalse(verify_generalization(bad))
        r=generalize(CONTROLS[0]['input']);r['steps'][0]['index']=False;self.assertFalse(verify_generalization(r))
    def test_reconstruction_alone_does_not_certify_lgg(self):
        r=generalize(CONTROLS[0]['input']);r['generalization']=['pair','?g0','?g1'];r['left_substitution']['?g1']=['amber'];r['right_substitution']['?g1']=['blue']
        self.assertEqual(apply(r['generalization'],r['left_substitution']),r['input']['terms'][0]);self.assertEqual(apply(r['generalization'],r['right_substitution']),r['input']['terms'][1]);self.assertFalse(verify_generalization(r))
        # A fully coherent naive trace still reconstructs, but illegally splits a repeated pair.
        r=generalize(CONTROLS[0]['input']);r['generalization']=['pair','?g0','?g1'];r['left_substitution']['?g1']=['amber'];r['right_substitution']['?g1']=['blue'];r['pairs'].append({'variable':'?g1','left':['amber'],'right':['blue'],'first_step':1});r['steps'][1].update(rule='fresh',output='?g1',variable='?g1',source_step=1);r['steps'][2]['output']=r['generalization'];self.assertFalse(verify_generalization(r))
    def test_checker_does_not_call_generator_and_bad_inputs(self):
        r=generalize(CONTROLS[1]['input'])
        with patch('unifylab.generalization.generalize',side_effect=AssertionError('called')):self.assertTrue(verify_generalization(r))
        for d in [{},[],{'terms':[]},{'terms':[['a']]},{'terms':['?x',['a']]},{'terms':[[True],['a']]},{'terms':[['f'],['f',['a']]]},{'terms':[['a'],['b']],'extra':1}]:
            with self.assertRaises(ValueError):generalize(d)
        for d in [None,False,[],{},42,'certificate']:self.assertFalse(verify_generalization(d))
    def test_cli_generalize_verify_and_atomic_failure(self):
        d=CONTROLS[0]['input'];r=generalize(d)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'r.json';proc=subprocess.run([sys.executable,'-m','unifylab','--generalize','-','-o',str(out)],input=json.dumps(d),text=True,capture_output=True);self.assertEqual(proc.returncode,0,proc.stderr);self.assertEqual(json.loads(out.read_text()),r)
            proc=subprocess.run([sys.executable,'-m','unifylab','--verify-generalization',str(out)],text=True,capture_output=True);self.assertEqual(proc.returncode,0);self.assertEqual(json.loads(proc.stdout),{'valid':True});old=out.read_bytes()
            for flags,raw in [(['--generalize'],'{}'),(['--generalize','--verify'],json.dumps(d)),(['--generalize','--subsets'],json.dumps(d)),(['--generalize'],'{"terms":[],"terms":[]}')]:
                proc=subprocess.run([sys.executable,'-m','unifylab',*flags,'-','-o',str(out)],input=raw,text=True,capture_output=True);self.assertEqual(proc.returncode,2);self.assertEqual(out.read_bytes(),old)
