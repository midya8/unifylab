import copy,itertools,json,unittest,tempfile,subprocess,sys
from pathlib import Path
from unittest.mock import patch
from unifylab.subsets import analyze
from unifylab import solve,verify
from test_core import oracle,bank
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/subset-controls.json').read_text())

def proper_subsets(m):
    s=(m-1)&m
    while True:
        yield s
        if not s:break
        s=(s-1)&m

class SubsetTests(unittest.TestCase):
    def check(self,data):
        old=copy.deepcopy(data);r=analyze(data);self.assertEqual(old,data)
        n=len(data['equations']);full=(1<<n)-1
        self.assertEqual(len(r['records']),1<<n)
        truth=[]
        for row in r['records']:
            selected={'equations':[data['equations'][i] for i in range(n) if row['mask']&(1<<i)]}
            native=solve(selected);self.assertTrue(verify(native))
            self.assertEqual(row['status'],native['status']);self.assertEqual(row['rewrites'],len(native['steps']))
            # Lazy oracle can expand, so actual bound controls are compared only where decided.
            expected=None if row['status']=='limit' else oracle(selected)
            if row['status']!='limit':self.assertEqual(row['status']=='unified',expected is not None)
            truth.append(row['status'])
        self.assertEqual(r['complete'],all(s!='limit' for s in truth))
        self.assertEqual(r['unresolved_masks'],[m for m,s in enumerate(truth) if s=='limit'])
        for c in r['minimal_cores']:
            self.assertEqual(truth[c['mask']],'not_unifiable')
            for s in proper_subsets(c['mask']):self.assertEqual(truth[s],'unified')
            self.assertEqual([x['neighbor_mask'] for x in c['checks']],[c['mask']^(1<<i) for i in c['indices']])
        for repair in r['minimal_repairs']:
            removed=repair['removed_mask'];self.assertEqual(truth[full^removed],'unified')
            if removed:
                for s in proper_subsets(removed):self.assertEqual(truth[full^s],'not_unifiable')
        if r['complete']:
            # All-proper-subsets brute force, not production immediate-neighbor criterion.
            cores=[m for m,s in enumerate(truth) if s=='not_unifiable' and all(truth[t]=='unified' for t in proper_subsets(m))]
            repairs=[m for m in range(full+1) if truth[full^m]=='unified' and (m==0 or all(truth[full^s]=='not_unifiable' for s in proper_subsets(m)))]
            self.assertEqual([c['mask'] for c in r['minimal_cores']],cores)
            self.assertEqual([c['removed_mask'] for c in r['minimal_repairs']],repairs)
            self.assertEqual(r['minimum_core_size'],min((m.bit_count() for m in cores),default=None))
            self.assertEqual(r['minimum_repair_size'],min((m.bit_count() for m in repairs),default=None))
            # Independently enumerate minimal hitting sets of every known core.
            hits=[m for m in range(full+1) if all(m&c for c in cores)]
            minimal_hits=[m for m in hits if not any(s!=m and s&m==s for s in hits)]
            self.assertEqual(repairs,minimal_hits)
        else:self.assertIsNone(r['minimum_core_size']);self.assertIsNone(r['minimum_repair_size'])
        return r
    def test_controls_and_all_neighbor_certificates(self):
        for c in CONTROLS:self.check(c['input'])
    def test_seeded_lazy_oracle_and_bruteforce_frontiers(self):
        for d in bank(120,981):self.check(d)
    def test_duplicate_identity_minimal_not_minimum(self):
        r=self.check(CONTROLS[0]['input'])
        self.assertEqual([c['indices'] for c in r['minimal_cores']],[[0,1],[1,2],[3,4,5]])
        self.assertEqual({len(x['removed_indices']) for x in r['minimal_repairs']},{2,3})
        self.assertEqual(r['minimum_core_size'],2);self.assertEqual(r['minimum_repair_size'],2)
    def test_no_limit_promotion_or_inferred_neighbor(self):
        # A required unknown neighbor cannot certify a frontier, even when logically inferable.
        data={'equations':[['?x',['amber']],['?x',['blue']]]}
        def stub(d):
            r=solve(d)
            if len(d['equations'])==1 and d['equations'][0][1]==['blue']:
                r.update(status='limit',failure=None,limit='nodes')
            return r
        with patch('unifylab.subsets.solve',side_effect=stub):r=analyze(data)
        self.assertFalse(r['complete']);self.assertEqual(r['unresolved_masks'],[2]);self.assertEqual(r['minimal_cores'],[])
        self.assertEqual([x['removed_indices'] for x in r['minimal_repairs']],[[1]])
        self.assertIsNone(r['minimum_repair_size'])
    def test_invalid_full_universe_rejected_before_calls(self):
        bad=[{'equations':[[['f'],['f',['a']]]]},{'equations':[]}]
        with patch('unifylab.subsets.solve') as solver:
            with self.assertRaises(ValueError):analyze(bad[0])
            solver.assert_not_called()
    def test_order_and_relabeling(self):
        data=CONTROLS[0]['input'];old=analyze(data);perm=[5,2,1,4,0,3];new=analyze({'equations':[data['equations'][i] for i in perm]})
        translate=lambda mask:sum(1<<perm[i] for i in range(len(perm)) if mask&(1<<i))
        self.assertEqual({translate(c['mask']) for c in new['minimal_cores']},{c['mask'] for c in old['minimal_cores']})
        self.assertEqual({translate(c['removed_mask']) for c in new['minimal_repairs']},{c['removed_mask'] for c in old['minimal_repairs']})

    def test_cli_subset_output_modes_and_atomic_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'audit.json';data=CONTROLS[0]['input']
            proc=subprocess.run([sys.executable,'-m','unifylab','--subsets','-','-o',str(out)],input=json.dumps(data),text=True,capture_output=True)
            self.assertEqual(proc.returncode,0,proc.stderr);self.assertEqual(json.loads(out.read_text()),analyze(data));old=out.read_bytes()
            for flags,raw in [(['--subsets'],'{}'),(['--subsets'],'{"equations":[],"equations":[]}'),(['--subsets','--verify'],json.dumps(data)),(['--subsets'],' '*65537)]:
                proc=subprocess.run([sys.executable,'-m','unifylab',*flags,'-','-o',str(out)],input=raw,text=True,capture_output=True)
                self.assertEqual(proc.returncode,2);self.assertEqual(out.read_bytes(),old)
