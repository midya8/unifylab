import json,random,unittest,copy,itertools,subprocess,sys
from pathlib import Path
from unifylab import solve,verify
from unifylab.core import validate,apply
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/controls.json').read_text())

def oracle(data):
    # Lazy environment plus recursive dereferencing, not composed pending rewrites.
    env={}
    def deref(t):
        while isinstance(t,str) and t in env:t=env[t]
        return t
    def contains(v,t):
        t=deref(t)
        return t==v if isinstance(t,str) else any(contains(v,c) for c in t[1:])
    def pair(a,b):
        a,b=deref(a),deref(b)
        if a==b:return True
        if isinstance(a,str):
            if contains(a,b):return False
            env[a]=b;return True
        if isinstance(b,str):return pair(b,a)
        return a[0]==b[0] and len(a)==len(b) and all(pair(x,y) for x,y in zip(a[1:],b[1:]))
    if not all(pair(a,b) for a,b in data['equations']):return None
    def expand(t):
        t=deref(t)
        return t if isinstance(t,str) else [t[0],*[expand(c) for c in t[1:]]]
    return {v:expand(t) for v,t in sorted(env.items())}

def bank(n,seed):
    rng=random.Random(seed)
    def term(d):
        if d==0 or rng.random()<.45:return rng.choice(['?x','?y','?z',['amber'],['blue']])
        return ['box',term(d-1)] if rng.random()<.5 else ['pair',term(d-1),term(d-1)]
    return [{'equations':[[term(2),term(2)] for _ in range(rng.randrange(5))]} for _ in range(n)]

class UnificationTests(unittest.TestCase):
    def check(self,data):
        r=solve(data);self.assertTrue(verify(r));self.assertEqual(r,solve(data))
        if r['status']!='limit':
            expected=oracle(data);self.assertEqual(r['status']=='unified',expected is not None)
            if expected is not None:self.assertEqual(r['substitution'],expected)
        return r
    def test_original_and_seeded_oracle(self):
        for c in CONTROLS:self.check(c['input'])
        for d in bank(600,72193):self.check(d)
    def test_all_two_variable_term_pairs(self):
        pool=['?x','?y',['amber'],['blue'],['box','?x'],['box','?y'],['pair','?x','?y'],['pair','?y','?x']]
        for a,b in itertools.product(pool,repeat=2):self.check({'equations':[[a,b]]})
    def test_bounded_ground_factorization(self):
        # Finite ground candidates are regression evidence, not a proof of generality.
        ground=[['amber'],['blue'],['box',['amber']],['box',['blue']]]
        tasks=bank(60,812)
        cases=unifiers=0
        def ev(t,e):return e[t] if isinstance(t,str) else [t[0],*[ev(c,e) for c in t[1:]]]
        for d in tasks:
            _,vs,_=validate(d);r=solve(d)
            for vals in itertools.product(ground,repeat=len(vs)):
                e=dict(zip(vs,vals));truth=all(ev(a,e)==ev(b,e) for a,b in d['equations']);cases+=1
                if truth:
                    unifiers+=1;self.assertEqual(r['status'],'unified')
                    for v in vs:self.assertEqual(ev(r['substitution'].get(v,v),e),e[v])
                if r['status']=='unified':
                    self.assertTrue(all(a==b for a,b in r['applied_equations']))
        self.assertGreater(cases,500);self.assertGreater(unifiers,5)
    def test_composition_alias_and_cycle(self):
        r=self.check(CONTROLS[0]['input']);self.assertEqual(r['substitution']['?x'],['box',['pair',['amber'],['amber']]])
        self.assertEqual(self.check(CONTROLS[1]['input'])['status'],'unified')
        self.assertEqual(self.check(CONTROLS[2]['input'])['steps'][-1]['witness'],{'variable':'?x','path':[0,1]})
        self.assertEqual(self.check(CONTROLS[3]['input'])['status'],'not_unifiable')
        self.assertEqual(self.check(CONTROLS[13]['input'])['status'],'limit')
        self.assertEqual(self.check(CONTROLS[14]['input'])['limit'],'result_nodes')
    def test_verifier_forgery_and_json_types(self):
        for c in CONTROLS:
            r=solve(c['input']);self.assertTrue(verify(r))
            for key in ['schema','variables','signature','status','failure','limit','final','substitution','applied_equations','free_variables']:
                bad=copy.deepcopy(r);bad[key]=42;self.assertFalse(verify(bad),key)
            for i,s in enumerate(r['steps']):
                for k in s:
                    bad=copy.deepcopy(r);bad['steps'][i][k]=None;self.assertFalse(verify(bad),(i,k))
            bad=copy.deepcopy(r);bad['steps'].append({});self.assertFalse(verify(bad))
        for x in [None,False,[],42,'report',{}, {'schema':'unifylab-v1'},*bank(50,91)]:self.assertFalse(verify(x))
        r=solve({'equations':[['?x',['box',['amber']]]]});r['signature']['box']=True;self.assertFalse(verify(r))
    def test_step_limit_and_no_false_failure(self):
        from unittest.mock import patch
        import importlib
        with patch('unifylab.core.MAX_STEPS',1),patch.object(importlib.import_module('unifylab.verify'),'MAX_STEPS',1):
            r=solve(CONTROLS[0]['input']);self.assertEqual(r['limit'],'steps');self.assertEqual(r['status'],'limit');self.assertTrue(verify(r));self.assertIsNone(r['substitution']);r['failure']='occurs';self.assertFalse(verify(r))
    def test_strict_shapes_and_bounds(self):
        bad=[{},[],{'equations':None},{'equations':[[1,2]]},{'equations':[['x',['a']]]},{'equations':[[True,['a']]]},{'equations':[[['f'],['f',['a']]]]},{'equations':[[['f',1],['a']]]},{'equations':[[['f',[],[]],['a']]]},{'equations':[['?Upper',['a']]]},{'equations':[],'other':1},{'equations':[['?x',['a']]]*9},{'equations':[['?'+chr(97+i),['a']] for i in range(7)]}]
        t='?x'
        for _ in range(8):t=['box',t]
        bad.append({'equations':[['?y',t]]})
        for x in bad:
            with self.assertRaises(ValueError):solve(x)
    def test_input_not_mutated_and_simultaneous(self):
        d=copy.deepcopy(CONTROLS[0]['input']);old=copy.deepcopy(d);solve(d);self.assertEqual(d,old)
        self.assertEqual(apply('?x',{'?x':'?y','?y':['amber']}),'?y')
    def test_all_rule_and_outcome_controls(self):
        rs=[solve(c['input']) for c in CONTROLS];self.assertEqual({s['rule'] for r in rs for s in r['steps']},{'delete','orient','decompose','eliminate','occurs','clash'})
        self.assertEqual({r['status'] for r in rs},{'unified','not_unifiable','limit'})
        print(json.dumps({'controls':len(rs),'rewrites':sum(len(r['steps']) for r in rs),'outcomes':{k:sum(r['status']==k for r in rs) for k in ['unified','not_unifiable','limit']}}))

if __name__=='__main__':unittest.main()
