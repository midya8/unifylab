// Separately written ground finite-term LGG. Canonical variable names follow first disagreement.
import {validate as validateEquations,apply} from './engine.js';
const clone=x=>JSON.parse(JSON.stringify(x));
export function validate(data){
 if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).length!==1||!Object.hasOwn(data,'terms')||!Array.isArray(data.terms)||data.terms.length!==2)throw Error('expected only terms, with exactly two ground terms');
 const r=validateEquations({equations:[data.terms]});if(r.variables.length)throw Error('generalization inputs must be ground: no variables');return {input:{terms:r.input.equations[0]},signature:r.signature};
}
export function generalize(data){
 const {input,signature}=validate(data),steps=[],pairs=[],memo=new Map(),left_substitution={},right_substitution={};
 function walk(a,b,path){let output,variable=null,source_step=null,rule;
  if(a[0]===b[0]){output=[a[0],...a.slice(1).map((c,i)=>walk(c,b[i+1],[...path,i]))];rule='retain';}
  else {const key=JSON.stringify([a,b]);if(memo.has(key)){({variable,source_step}=memo.get(key));rule='reuse';}
   else{variable='?g'+pairs.length;source_step=steps.length;rule='fresh';memo.set(key,{variable,source_step});pairs.push({variable,left:clone(a),right:clone(b),first_step:source_step});left_substitution[variable]=clone(a);right_substitution[variable]=clone(b);}output=variable;}
  steps.push({index:steps.length,path,rule,left:clone(a),right:clone(b),output:clone(output),variable,source_step});return output;
 }
 const generalization=walk(...input.terms,[]);
 return {schema:'unifylab-generalization-v1',input,signature,generalization,left_substitution,right_substitution,pairs,steps,reconstructed_left:apply(generalization,left_substitution),reconstructed_right:apply(generalization,right_substitution)};
}
