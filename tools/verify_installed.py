import sys,json,pathlib,subprocess,importlib
root=pathlib.Path(sys.argv[1]);expected=json.loads(pathlib.Path(sys.argv[2]).read_text());modules=['unifylab','unifylab.core','unifylab.verify','unifylab.__main__'];origins={}
for name in modules:
 p=pathlib.Path(importlib.import_module(name).__file__).resolve();assert not p.is_relative_to(root),p;origins[name]=str(p)
from unifylab import solve,verify
for item in expected:
 data=item['input'];r=item['report'];assert solve(data)==r;assert verify(r)
 for command in [[sys.executable,'-m','unifylab'],['unifylab']]:
  out=subprocess.run(command+['-'],input=json.dumps(data),text=True,capture_output=True,check=True);assert json.loads(out.stdout)==r
  out=subprocess.run(command+['--verify','-'],input=json.dumps(r),text=True,capture_output=True,check=True);assert json.loads(out.stdout)=={'valid':True}
print(json.dumps({'installed_reports':len(expected),'module_origins':origins,'CLIs':2,'modes':['solve','verify']}))
