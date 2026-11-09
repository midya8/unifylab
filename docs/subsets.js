// Enumerate every indexed subsystem independently; never infer an unknown status.
import {validate,solve} from './engine.js';
export function analyze(data){
 const {input}=validate(data),eq=input.equations,n=eq.length,full=(1<<n)-1;
 const indices=mask=>Array.from({length:n},(_,i)=>i).filter(i=>mask&(1<<i));
 const records=Array.from({length:full+1},(_,mask)=>{const is=indices(mask),r=solve({equations:is.map(i=>eq[i])});return {mask,indices:is,status:r.status,failure:r.failure,limit:r.limit,rewrites:r.steps.length};});
 const minimal_cores=[],minimal_repairs=[];
 for(const r of records){
  if(r.status==='not_unifiable'){
   const checks=r.indices.map(i=>({equation:i,neighbor_mask:r.mask^(1<<i),status:records[r.mask^(1<<i)].status}));
   if(checks.every(c=>c.status==='unified'))minimal_cores.push({mask:r.mask,indices:r.indices,checks});
  }
  if(r.status==='unified'){
   const removed_mask=full^r.mask,removed_indices=indices(removed_mask),checks=removed_indices.map(i=>({equation:i,neighbor_mask:r.mask|(1<<i),status:records[r.mask|(1<<i)].status}));
   if(checks.every(c=>c.status==='not_unifiable'))minimal_repairs.push({removed_mask,removed_indices,kept_mask:r.mask,checks});
  }
 }
 minimal_repairs.sort((a,b)=>a.removed_mask-b.removed_mask);
 const unresolved_masks=records.filter(r=>r.status==='limit').map(r=>r.mask),complete=unresolved_masks.length===0;
 return {schema:'unifylab-subsets-v1',input,records,complete,unresolved_masks,minimal_cores,minimal_repairs,minimum_core_size:complete&&minimal_cores.length?Math.min(...minimal_cores.map(c=>c.indices.length)):null,minimum_repair_size:complete&&minimal_repairs.length?Math.min(...minimal_repairs.map(r=>r.removed_indices.length)):null};
}
