"""Ground finite-term anti-unification and independent canonical trace checking."""
from copy import deepcopy
import json
from .core import validate as validate_equations, apply


def validate(data):
    if not isinstance(data,dict) or set(data)!={'terms'} or not isinstance(data['terms'],list) or len(data['terms'])!=2:
        raise ValueError('expected only terms, with exactly two ground terms')
    canonical,variables,signature=validate_equations({'equations':[data['terms']]})
    if variables:raise ValueError('generalization inputs must be ground: no variables')
    return {'terms':canonical['equations'][0]},signature


def generalize(data):
    canonical,signature=validate(data);steps=[];pairs=[];memo={};left={};right={}
    def visit(a,b,path):
        variable=None;source_step=None
        if a[0]==b[0]:
            out=[a[0],*[visit(x,y,[*path,i]) for i,(x,y) in enumerate(zip(a[1:],b[1:]))]];rule='retain'
        else:
            key=json.dumps([a,b],separators=(',',':'))
            if key in memo:
                variable,source_step=memo[key];rule='reuse'
            else:
                variable='?g'+str(len(pairs));source_step=len(steps);memo[key]=(variable,source_step);rule='fresh'
                pairs.append({'variable':variable,'left':deepcopy(a),'right':deepcopy(b),'first_step':source_step})
                left[variable]=deepcopy(a);right[variable]=deepcopy(b)
            out=variable
        steps.append({'index':len(steps),'path':path,'rule':rule,'left':deepcopy(a),'right':deepcopy(b),
                      'output':deepcopy(out),'variable':variable,'source_step':source_step})
        return out
    result=visit(*canonical['terms'],[])
    return {'schema':'unifylab-generalization-v1','input':canonical,'signature':signature,'generalization':result,
            'left_substitution':left,'right_substitution':right,'pairs':pairs,'steps':steps,
            'reconstructed_left':apply(result,left),'reconstructed_right':apply(result,right)}


def verify_generalization(report):
    """Check each supplied node against postorder obligations, never generate().

    Uses an explicit obligation stack, structural pair-list search and a private
    instantiator, rather than generator recursion, memo keys or core.apply.
    """
    def equal(a,b):
        return json.dumps(a,sort_keys=True,allow_nan=False,separators=(',',':'))==json.dumps(b,sort_keys=True,allow_nan=False,separators=(',',':'))
    try:
        keys={'schema','input','signature','generalization','left_substitution','right_substitution','pairs','steps','reconstructed_left','reconstructed_right'}
        if type(report) is not dict or set(report)!=keys or report['schema']!='unifylab-generalization-v1':return False
        canonical,signature=validate(report['input'])
        if not equal(signature,report['signature']):return False
        obligations=[];stack=[([],canonical['terms'][0],canonical['terms'][1],False)]
        while stack:
            path,a,b,ready=stack.pop()
            if a[0]==b[0] and not ready:
                stack.append((path,a,b,True))
                for i in range(len(a)-2,-1,-1):stack.append(([*path,i],a[i+1],b[i+1],False))
            else:obligations.append((path,a,b))
        if type(report['steps']) is not list or len(report['steps'])!=len(obligations):return False
        outputs={};pairs=[];left={};right={}
        for index,((path,a,b),s) in enumerate(zip(obligations,report['steps'])):
            variable=None;source=None
            if a[0]==b[0]:
                rule='retain';out=[a[0],*[outputs[tuple([*path,i])] for i in range(len(a)-1)]]
            else:
                previous=next((p for p in pairs if p['left']==a and p['right']==b),None)
                if previous is None:
                    variable='?g'+str(len(pairs));source=index;rule='fresh'
                    pairs.append({'variable':variable,'left':a,'right':b,'first_step':index});left[variable]=a;right[variable]=b
                else:variable=previous['variable'];source=previous['first_step'];rule='reuse'
                out=variable
            expected={'index':index,'path':path,'rule':rule,'left':a,'right':b,'output':out,'variable':variable,'source_step':source}
            if not equal(s,expected):return False
            outputs[tuple(path)]=out
        g=outputs[()]
        if not all(equal(report[k],v) for k,v in [('generalization',g),('pairs',pairs),('left_substitution',left),('right_substitution',right)]):return False
        def instantiate(t,env):return deepcopy(env[t]) if isinstance(t,str) else [t[0],*[instantiate(c,env) for c in t[1:]]]
        l,r=instantiate(g,left),instantiate(g,right)
        return equal(l,canonical['terms'][0]) and equal(r,canonical['terms'][1]) and equal(l,report['reconstructed_left']) and equal(r,report['reconstructed_right'])
    except (ValueError,TypeError,KeyError,IndexError,RecursionError,OverflowError):return False
