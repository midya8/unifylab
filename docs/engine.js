// Independent browser implementation of composed finite-tree equation rewrites.
const clone=x=>JSON.parse(JSON.stringify(x));
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export const MAX_NODES=4096,MAX_STEPS=256;
export function validate(data){
 if(data===null||Array.isArray(data)||typeof data!=='object'||Object.keys(data).length!==1||!Object.hasOwn(data,'equations'))throw Error('expected only equations');
 if(!Array.isArray(data.equations)||data.equations.length>8)throw Error('at most 8 equations');
 let nodes=0;const variables=new Set(),signature=new Map();
 function term(t,d=0){
  if(++nodes>96||d>6)throw Error('input exceeds 96 nodes or depth 6');
  if(typeof t==='string'&&/^\?[a-z][a-z0-9_]{0,15}$/.test(t)){variables.add(t);return t;}
  if(!Array.isArray(t)||t.length<1||t.length>3||typeof t[0]!=='string'||!(/^[a-z][a-z0-9_]{0,15}$/).test(t[0]))throw Error('term must be ?variable or [constructor, ...0-2 arguments]');
  const arity=t.length-1;if(signature.has(t[0])&&signature.get(t[0])!==arity)throw Error('constructor arity must be fixed');signature.set(t[0],arity);
  return [t[0],...t.slice(1).map(x=>term(x,d+1))];
 }
 const equations=data.equations.map(p=>{if(!Array.isArray(p)||p.length!==2)throw Error('equation must have two terms');return p.map(t=>term(t));});
 if(variables.size>6)throw Error('at most 6 variables');
 return {input:{equations},variables:[...variables].sort(),signature:Object.fromEntries([...signature].sort(([a],[b])=>a<b?-1:a>b?1:0))};
}
function firstOccurrence(t,v){
 const stack=[[t,[]]];
 while(stack.length){const [x,p]=stack.pop();if(x===v)return p;if(Array.isArray(x))for(let i=x.length-1;i>=1;i--)stack.push([x[i],[...p,i-1]]);}
 return null;
}
function replace(t,env,budget){
 const copy=x=>{if(--budget.remaining<0)throw Error('BOUND');return typeof x==='string'?x:[x[0],...x.slice(1).map(copy)];};
 if(typeof t==='string')return copy(Object.hasOwn(env,t)?env[t]:t);
 if(--budget.remaining<0)throw Error('BOUND');return [t[0],...t.slice(1).map(x=>replace(x,env,budget))];
}
const sortEnv=e=>Object.fromEntries(Object.entries(e).sort(([a],[b])=>a<b?-1:a>b?1:0));
export function solve(data){
 const {input,variables,signature}=validate(data);let state={equations:clone(input.equations),bindings:{}},status='unified',failure=null,limit=null;const steps=[];
 while(state.equations.length){
  if(steps.length>=MAX_STEPS){status='limit';limit='steps';break;}
  const before=clone(state),[a,b]=state.equations[0],tail=clone(state.equations.slice(1));let env=clone(state.bindings),rule,witness={},after;
  try{
   if(same(a,b)){rule='delete';after={equations:tail,bindings:env};}
   else if(Array.isArray(a)&&typeof b==='string'){rule='orient';after={equations:[[b,clone(a)],...tail],bindings:env};}
   else if(typeof a==='string'){
    const p=firstOccurrence(b,a);
    if(p!==null){rule='occurs';witness={variable:a,path:p};after=clone(state);status='not_unifiable';failure='occurs';}
    else{
     rule='eliminate';witness={variable:a,term:clone(b)};const budget={remaining:MAX_NODES},equations=tail.map(pair=>pair.map(t=>replace(t,{[a]:b},budget)));
     env=Object.fromEntries(Object.entries(env).sort(([x],[y])=>x<y?-1:x>y?1:0).map(([v,t])=>[v,replace(t,{[a]:b},budget)]));env[a]=replace(b,{},budget);after={equations,bindings:sortEnv(env)};
    }
   }else if(a[0]!==b[0]){rule='clash';witness={left:a[0],right:b[0]};after=clone(state);status='not_unifiable';failure='clash';}
   else{rule='decompose';after={equations:a.slice(1).map((t,i)=>[clone(t),clone(b[i+1])]).concat(tail),bindings:env};}
  }catch(e){if(e.message!=='BOUND')throw e;status='limit';limit='nodes';break;}
  steps.push({index:steps.length,rule,before,after:clone(after),witness});state=after;if(failure)break;
 }
 let applied_equations=null;
 if(status==='unified')try{const budget={remaining:MAX_NODES};applied_equations=input.equations.map(pair=>pair.map(t=>replace(t,state.bindings,budget)));}catch(e){if(e.message!=='BOUND')throw e;status='limit';limit='result_nodes';}
 return {schema:'unifylab-v1',input,variables,signature,status,failure,limit,steps,final:state,substitution:status==='unified'?clone(state.bindings):null,applied_equations,free_variables:status==='unified'?variables.filter(v=>!Object.hasOwn(state.bindings,v)):null};
}
export function apply(t,env){return typeof t==='string'?(Object.hasOwn(env,t)?clone(env[t]):t):[t[0],...t.slice(1).map(x=>apply(x,env))];}
export function format(t){return typeof t==='string'?t:t.length===1?t[0]:`${t[0]}(${t.slice(1).map(format).join(', ')})`;}
