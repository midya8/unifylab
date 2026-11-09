"""Check supplied rewrite certificates without calling the unifier."""
from copy import deepcopy
from .core import validate,MAX_NODES,MAX_STEPS

def verify(report):
    try:
        if not isinstance(report,dict) or set(report)!={'schema','input','variables','signature','status','failure','limit','steps','final','substitution','applied_equations','free_variables'}:return False
        canonical,variables,signature=validate(report['input'])
        if any(type(v) is not int for v in report['signature'].values()):return False
        if report['schema']!='unifylab-v1' or report['variables']!=variables or report['signature']!=signature:return False
        state={'equations':canonical['equations'],'bindings':{}};terminal=None
        def count(t): return 1 if isinstance(t,str) else 1+sum(map(count,t[1:]))
        def measure(s):return sum(count(t) for p in s['equations'] for t in p)+sum(count(t) for t in s['bindings'].values())
        def replacement(t,bindings,budget):
            def walk(x):
                budget[0]+=1
                if budget[0]>MAX_NODES:raise OverflowError()
                return x if isinstance(x,str) else [x[0],*[walk(y) for y in x[1:]]]
            if isinstance(t,str):return walk(bindings.get(t,t))
            budget[0]+=1
            if budget[0]>MAX_NODES:raise OverflowError()
            return [t[0],*[replacement(y,bindings,budget) for y in t[1:]]]
        def path(t,v):
            todo=[(t,[])]
            while todo:
                x,p=todo.pop(0)
                if x==v:return p
                if isinstance(x,list):todo[0:0]=[(c,p+[i]) for i,c in enumerate(x[1:])]
            return None
        def transition(s):
            a,b=s['equations'][0];tail=deepcopy(s['equations'][1:]);env=deepcopy(s['bindings']);w={}
            if a==b:kind='delete';new={'equations':tail,'bindings':env}
            elif isinstance(b,str) and not isinstance(a,str):kind='orient';new={'equations':[[b,a]]+tail,'bindings':env}
            elif isinstance(a,str):
                p=path(b,a)
                if p is not None:return 'occurs',deepcopy(s),{'variable':a,'path':p}
                kind='eliminate';w={'variable':a,'term':b};budget=[0]
                tail=[[replacement(t,{a:b},budget) for t in pair] for pair in tail]
                env={v:replacement(t,{a:b},budget) for v,t in sorted(env.items())};env[a]=replacement(b,{},budget)
                new={'equations':tail,'bindings':dict(sorted(env.items()))}
            elif a[0]!=b[0]:return 'clash',deepcopy(s),{'left':a[0],'right':b[0]}
            else:kind='decompose';new={'equations':[[a[i],b[i]] for i in range(1,len(a))]+tail,'bindings':env}
            if measure(new)>MAX_NODES:raise OverflowError()
            return kind,new,w
        if not isinstance(report['steps'],list) or len(report['steps'])>MAX_STEPS:return False
        for i,step in enumerate(report['steps']):
            if terminal or not state['equations'] or set(step)!={'index','rule','before','after','witness'} or type(step['index']) is not int or step['index']!=i or step['before']!=state:return False
            kind,new,w=transition(state)
            if (step['rule'],step['after'],step['witness'])!=(kind,new,w):return False
            state=new
            if kind in ('occurs','clash'):terminal=kind
        if report['final']!=state:return False
        status=report['status']
        if status=='not_unifiable':return terminal is not None and report['failure']==terminal and report['limit'] is None and all(report[k] is None for k in ('substitution','applied_equations','free_variables'))
        if terminal or report['failure'] is not None:return False
        if status=='limit':
            if any(report[k] is not None for k in ('substitution','applied_equations','free_variables')):return False
            if report['limit']=='steps':return bool(state['equations']) and len(report['steps'])==MAX_STEPS
            try:
                if report['limit']=='nodes' and state['equations']:transition(state)
                elif report['limit']=='result_nodes' and not state['equations']:
                    budget=[0]
                    for pair in canonical['equations']:
                        for t in pair:replacement(t,state['bindings'],budget)
                else:return False
            except OverflowError:return True
            return False
        if status!='unified' or state['equations'] or report['limit'] is not None or report['substitution']!=state['bindings']:return False
        domain=set(state['bindings'])
        def vars_in(t):return {t} if isinstance(t,str) else set().union(*(vars_in(x) for x in t[1:]))
        if any(domain & vars_in(t) for t in state['bindings'].values()):return False
        budget=[0];applied=[[replacement(t,state['bindings'],budget) for t in pair] for pair in canonical['equations']]
        return all(a==b for a,b in applied) and report['applied_equations']==applied and report['free_variables']==sorted(set(variables)-domain)
    except (ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError,AttributeError):return False
