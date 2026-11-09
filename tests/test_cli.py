import unittest,tempfile,subprocess,sys,json,os
from pathlib import Path
from unifylab import solve
ROOT=Path(__file__).resolve().parents[1]
class CLITests(unittest.TestCase):
 def test_file_stdin_and_verifier(self):
  data=json.loads((ROOT/'examples/equations.json').read_text());expected=solve(data)
  p=subprocess.run([sys.executable,'-m','unifylab',str(ROOT/'examples/equations.json')],capture_output=True,check=True);self.assertEqual(json.loads(p.stdout),expected)
  p=subprocess.run([sys.executable,'-m','unifylab','-'],input=json.dumps(data).encode(),capture_output=True,check=True);self.assertEqual(json.loads(p.stdout),expected)
  p=subprocess.run([sys.executable,'-m','unifylab','--verify','-'],input=json.dumps(expected).encode(),capture_output=True,check=True);self.assertEqual(json.loads(p.stdout),{'valid':True})
  p=subprocess.run([sys.executable,'-m','unifylab','--verify','-'],input=b'{}',capture_output=True,check=True);self.assertEqual(json.loads(p.stdout),{'valid':False})
 def test_invalid_atomic_output(self):
  with tempfile.TemporaryDirectory() as td:
   dest=Path(td)/'out.json';dest.write_text('retain me')
   for raw in [b'{"equations":[],"equations":[]}',b'{"equations":NaN}',b'\xff',b'['*1100,b' '*65537,b'{}']:
    p=subprocess.run([sys.executable,'-m','unifylab','-','-o',str(dest)],input=raw,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(dest.read_text(),'retain me');self.assertEqual(p.stdout,b'')
   p=subprocess.run([sys.executable,'-m','unifylab',str(ROOT/'examples/equations.json'),'-o',str(dest)],capture_output=True,check=True);self.assertEqual(json.loads(dest.read_text()),solve(json.loads((ROOT/'examples/equations.json').read_text())))
 def test_large_generated_certificate_verifies(self):
  c=json.loads((ROOT/'docs/controls.json').read_text())[13];r=solve(c['input']);raw=json.dumps(r,indent=2).encode();self.assertGreater(len(raw),65536)
  p=subprocess.run([sys.executable,'-m','unifylab','--verify','-'],input=raw,capture_output=True,check=True);self.assertEqual(json.loads(p.stdout),{'valid':True})
