"""Finite syntactic unification with explicit rewrite certificates."""
from copy import deepcopy
import re

MAX_NODES=4096
MAX_STEPS=256
class Limit(Exception): pass

def validate(data):
    if not isinstance(data,dict) or set(data)!={'equations'}: raise ValueError('expected only equations')
    eq=data['equations']
    if not isinstance(eq,list) or len(eq)>8: raise ValueError('at most 8 equations')
    variables=set(); signature={}; nodes=0
    def term(t,depth=0):
        nonlocal nodes
        nodes+=1
        if nodes>96 or depth>6: raise ValueError('input exceeds 96 nodes or depth 6')
        if isinstance(t,str) and re.fullmatch(r'\?[a-z][a-z0-9_]{0,15}',t): variables.add(t); return t
        if not isinstance(t,list) or not 1<=len(t)<=3 or not isinstance(t[0],str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,15}',t[0]): raise ValueError('term must be ?variable or [constructor, ...0-2 arguments]')
        arity=len(t)-1
        if t[0] in signature and signature[t[0]]!=arity: raise ValueError('constructor arity must be fixed')
        signature[t[0]]=arity
        return [t[0],*[term(x,depth+1) for x in t[1:]]]
    out=[]
    for pair in eq:
        if not isinstance(pair,list) or len(pair)!=2: raise ValueError('equation must have two terms')
        out.append([term(pair[0]),term(pair[1])])
    if len(variables)>6: raise ValueError('at most 6 variables')
    return {'equations':out},sorted(variables),dict(sorted(signature.items()))

def occurrences(t,var):
    if isinstance(t,str): return [[]] if t==var else []
    return [[i,*p] for i,c in enumerate(t[1:]) for p in occurrences(c,var)]

def apply(t,subst):
    """Simultaneous substitution: never reapply within a replacement term."""
    if isinstance(t,str): return deepcopy(subst.get(t,t))
    return [t[0],*[apply(c,subst) for c in t[1:]]]

def size(t): return 1 if isinstance(t,str) else 1+sum(size(c) for c in t[1:])
def state_size(s): return sum(size(t) for p in s['equations'] for t in p)+sum(size(t) for t in s['bindings'].values())
def bounded_copy(t,subst,budget):
    # Traverse replacements too to budget allocation before constructing them.
    def clone(x):
        budget[0]-=1
        if budget[0]<0: raise Limit()
        return x if isinstance(x,str) else [x[0],*[clone(c) for c in x[1:]]]
    if isinstance(t,str): return clone(subst.get(t,t))
    budget[0]-=1
    if budget[0]<0: raise Limit()
    return [t[0],*[bounded_copy(c,subst,budget) for c in t[1:]]]

def solve(data):
    canonical,variables,signature=validate(data)
    state={'equations':deepcopy(canonical['equations']),'bindings':{}}; steps=[]; status='unified'; failure=None; limited=None
    while state['equations']:
        if len(steps)>=MAX_STEPS: status='limit';limited='steps';break
        before=deepcopy(state);a,b=state['equations'][0];rest=state['equations'][1:];bindings=deepcopy(state['bindings']); witness={}
        try:
            if a==b: rule='delete';after={'equations':deepcopy(rest),'bindings':bindings}
            elif not isinstance(a,str) and isinstance(b,str): rule='orient';after={'equations':[[b,deepcopy(a)],*deepcopy(rest)],'bindings':bindings}
            elif isinstance(a,str):
                paths=occurrences(b,a)
                if paths: rule='occurs';witness={'variable':a,'path':paths[0]};after=deepcopy(state);status='not_unifiable';failure='occurs'
                else:
                    rule='eliminate';witness={'variable':a,'term':deepcopy(b)};budget=[MAX_NODES]
                    equations=[[bounded_copy(t,{a:b},budget) for t in p] for p in rest]
                    bindings={k:bounded_copy(t,{a:b},budget) for k,t in sorted(bindings.items())}
                    bindings[a]=bounded_copy(b,{},budget);bindings=dict(sorted(bindings.items()));after={'equations':equations,'bindings':bindings}
            elif a[0]!=b[0]: rule='clash';witness={'left':a[0],'right':b[0]};after=deepcopy(state);status='not_unifiable';failure='clash'
            else: rule='decompose';after={'equations':[[deepcopy(x),deepcopy(y)] for x,y in zip(a[1:],b[1:])]+deepcopy(rest),'bindings':bindings}
            if state_size(after)>MAX_NODES: raise Limit()
        except Limit: status='limit';limited='nodes';break
        steps.append({'index':len(steps),'rule':rule,'before':before,'after':deepcopy(after),'witness':witness});state=after
        if failure:break
    applied=None
    if status=='unified':
        try:
            budget=[MAX_NODES];applied=[[bounded_copy(t,state['bindings'],budget) for t in p] for p in canonical['equations']]
        except Limit: status='limit';limited='result_nodes';applied=None
    return {'schema':'unifylab-v1','input':canonical,'variables':variables,'signature':signature,'status':status,'failure':failure,'limit':limited,'steps':steps,'final':state,'substitution':deepcopy(state['bindings']) if status=='unified' else None,'applied_equations':applied,'free_variables':sorted(set(variables)-set(state['bindings'])) if status=='unified' else None}
