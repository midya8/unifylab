import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
v=lambda x:'?'+x
f=lambda name,*args:[name,*args]
def control(name,*pairs):return {'name':name,'input':{'equations':[list(p) for p in pairs]}}
x,y,z,w,q,r=map(v,['x','y','z','w','q','r']);a=f('amber');b=f('blue')
def tree(t,n):return t if n==0 else f('fork',tree(t,n-1),tree(t,n-1))
controls=[
control('Compose every earlier binding, not just the new one',(x,f('box',y)),(y,f('pair',z,z)),(z,a)),
control('Alias reversal is not an occurs-check failure',(x,y),(y,x),(y,a)),
control('A nested cycle has an explicit child-index path',(x,f('box',f('pair',a,x)))),
control('An indirect cycle appears after composition',(x,f('box',y)),(y,f('pair',a,x))),
control('Different constructors cannot be repaired by bindings',(f('box',x),f('crate',a))),
control('Repeated variable constraints expose a late clash',(f('pair',x,x),f('pair',a,b))),
control('Orientation precedes elimination',(f('box',a),x)),
control('An identical compound equation deletes as one step',(f('pair',x,a),f('pair',x,a))),
control('An unconstrained residual variable stays free',(x,f('pair',y,y))),
control('No equations means the identity substitution'),
control('Constants agree without inventing bindings',(a,a)),
control('Two constructor arguments decompose left to right',(f('pair',x,f('box',y)),f('pair',f('box',a),z))),
control('Six variable aliases end in a ground term',(x,y),(y,z),(z,w),(w,q),(q,r),(r,a)),
control('Resource bound is not a non-unifiability claim',(x,tree(y,4)),(y,tree(z,4)),(z,tree(w,4))),
control('Expanded applied originals have their own result budget',(x,tree(y,3)),(x,tree(y,3)),(y,tree(z,3)),(z,tree(w,3))),
control('Repeated equations remain individually auditable',(x,a),(x,a),(x,a)),
control('Variable and constructor namespaces are distinct',(v('amber'),a)),
]
(root/'docs/controls.json').write_text(json.dumps(controls,indent=2)+'\n')
(root/'examples/equations.json').write_text(json.dumps(controls[0]['input'],indent=2)+'\n')
print(len(controls),'original controls')
