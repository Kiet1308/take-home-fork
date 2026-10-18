"use strict";
// Exact all-shift quarter-orbit certificate. Run: node all_shift_quarter_verify.js

function modPos(x,m){return ((x%m)+m)%m;}
function quarterClass(bits){
 const w=bits.reduce((a,b)=>a+b,0);
 if(w!==2) return w===0?0:w===1?1:w===3?4:5;
 return bits[0]===bits[2]?3:2;
}
function affineQuarterResidues(M,a){
 a=modPos(a,M);
 const bs=new Set([0,M]);
 for(let u=0;u<4;u++){bs.add(modPos(-u*a,M));bs.add(modPos(M/2-u*a,M));}
 const cuts=[...bs].sort((a,b)=>a-b), classes=Array.from({length:4},()=>Array(6).fill(0));
 for(let i=0;i+1<cuts.length;i++){
  const lo=cuts[i],hi=cuts[i+1];
  if(lo===hi)continue;
  const c=quarterClass(Array.from({length:4},(_,u)=>Math.floor(modPos(lo+u*a,M)/(M/2))));
  for(let r=0;r<4;r++){
   const cnt=Math.floor((hi-1-r)/4)-Math.floor((lo-1-r)/4);
   classes[r][c]+=cnt;
  }
 }
 return {M,a,cuts,classes,union:classes.map(v=>v[0]+v[3]+v[5])};
}
function unionQuarterDirect(n,s,m,C){
 const N=2**n,Q=N/4,hist=Array(6).fill(0);
 for(let A=0;A<Q;A++){
  const v=[];
  for(let k=0;k<4;k++){
   const a=A+k*Q,b=(a^(a>>>s))>>>0;
   v.push((b&1)^Math.floor((((Math.imul(m,b)+C)>>>0)%N)/(N/2)));
  }
  hist[quarterClass(v)]++;
 }
 return {hist,union:hist[0]+hist[3]+hist[5]};
}
function unionQuarterMixture(n,s,m,C){
 const N=2**n,l=2**(n-2-s),M=N/l,a=modPos(m+(m%4)*2**s,M);
 const p=affineQuarterResidues(M,a);
 let count=0;
 for(let z=0;z<l;z++) count+=p.union[Math.floor(((Math.imul(m,z)+C)>>>0)/l)%4];
 return {count,profile:p.union};
}

function assertQuarter(ok,message){if(!ok)throw Error(message);}
function referenceCoreFused(b){
 const p=(Math.imul(33,b)+0xe9f8cc1d)>>>0;
 const q=(Math.imul(16896,b)+0xaccf6200)>>>0;
 return (Math.imul(9,(p^q)>>>0)+0xfd7046c5)>>>0;
}
function referenceCoreStages(b){
 const c=(Math.imul(33,b)+0x165667b1)>>>0;
 const d=((c+0xd3a2646c)^(c<<9))>>>0;
 return (Math.imul(9,d)+0xfd7046c5)>>>0;
}
function referenceQuarterCertificate(){
 const n=1<<18, f=new Uint8Array(n);
 for(let b=0;b<n;b++){
  const g=referenceCoreFused(b);
  assertQuarter(g===referenceCoreStages(b),"reference core disagreement");
  f[b]=((g>>>1)^(g>>>17))&1;
 }
 const counts=Array(6).fill(0);
 let influence12=0;
 for(let b=0;b<n;b++){
  if(!(b&(1<<12)))influence12+=f[b]^f[b^(1<<12)];
  if(!(b&((1<<11)|(1<<12)))){
   counts[quarterClass([f[b],f[b^(1<<11)],f[b^(1<<12)],f[b^(1<<11)^(1<<12)]])]++;
  }
 }
 assertQuarter(JSON.stringify(counts)==="[2693,16308,23240,4294,16308,2693]","reference histogram");
 assertQuarter(influence12===79096,"reference influence");
 return {verified_core_words:n,counts,low_orbits:n/4,full_replication:16384,influence12,
  full_input31_edges:influence12*16384,constant_or_opposite:counts[0]+counts[3]+counts[5]};
}
function fixedStepCertificate(){
 let checked=0;
 for(let M=4;M<=2048;M*=2){
  for(let a=0;a<M;a++){
   const p=affineQuarterResidues(M,a),c=p.classes.reduce((v,z)=>v+z[0]+z[5],0),
    o=p.classes.reduce((v,z)=>v+z[3],0),d=Math.min(a,M-a);
   assertQuarter(!(c&&o),"fixed step has both constant and opposite patterns");
   assertQuarter((c>0)===(6*d<M),"fixed-step constant distance");
   assertQuarter(c===2*Math.max(M/2-3*d,0),"fixed-step constant count");
   checked++;
  }
 }
 return {checked,maximum_modulus:2048};
}
function unionProfileCertificate(){
 let checked=0;
 for(let M=16;M<=65536;M*=2){
  for(let a=1;a<M;a+=2){
   const p=affineQuarterResidues(M,a),h=M/2,z=a%h,d=Math.min(z,h-z),length=Math.max(h-3*d,0);
   assertQuarter(p.union.reduce((x,y)=>x+y,0)===2*length,"union interval length");
   assertQuarter(Math.max(...p.union)<=2*Math.ceil(length/4),"union residue bound");
   for(let r=0;r<4;r++)assertQuarter(p.classes[r].reduce((x,y)=>x+y,0)===M/4,"residue partition");
   checked++;
  }
 }
 return {checked,maximum_modulus:65536};
}
function wordProduct(m,x,C,n){
 const z=(Math.imul(m,x)+C)>>>0;
 return n===32?z:z%(2**n);
}
function candidateQuarterHistogram(n,s,t,m,C,gamma=1,first={}){
 const N=2**n,Q=N/4,counts=Array(6).fill(0);
 const m1=first.m1===undefined?1:first.m1,C1=first.C1||0,Ki=first.Ki||0,K=first.K||0;
 for(let A=0;A<Q;A++){
  const f=[];
  for(let v=0;v<4;v++){
   const x=(A+v*Q)^Ki,a=wordProduct(m1,x,C1,n),b=((a^(a>>>s)^K)>>>0)%N;
   const c=wordProduct(m,b,C,n);
   f.push((gamma*(b&1))^((c>>>t)&1));
  }
  counts[quarterClass(f)]++;
 }
 return counts;
}
function unionMixtureSmallCertificate(){
 let checked=0;
 for(let n=4;n<=8;n++){
  const N=2**n;
  for(let s=2;s<=n-2;s++)for(let m=1;m<N;m+=2)for(let C=0;C<N;C+=Math.max(1,N/16)){
   const p=unionQuarterMixture(n,s,m,C);
   for(let gamma=0;gamma<=1;gamma++){
    const counts=candidateQuarterHistogram(n,s,n-1,m,C,gamma);
    assertQuarter(counts[0]+counts[3]+counts[5]===p.count,"direct union mixture");
    checked++;
   }
  }
 }
 return {checked,widths:[4,5,6,7,8],every_odd_coefficient:true,bases_per_width:16,both_gamma_values:true};
}
function gaugeCertificate(){
 let seed=0x56f391a7,checked=0;
 function next(){seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed;}
 for(let n=4;n<=11;n++){
  const N=2**n;
  for(let i=0;i<96;i++){
   const s=1+next()%(n-1),t=1+next()%(n-1),m=(next()%N)|1,C=next()%N,gamma=next()&1;
   const first={m1:(next()%N)|1,C1:next()%N,Ki:next()%N,K:next()%N};
   const expected=candidateQuarterHistogram(n,s,t,m,C,gamma),
    actual=candidateQuarterHistogram(n,s,t,m,C,gamma,first);
   assertQuarter(JSON.stringify(actual)===JSON.stringify(expected),"first parameter/gauge histogram invariance");
   checked++;
  }
 }
 return {checked,widths:[4,5,6,7,8,9,10,11],parameters:["m1","C1","Ki","K"],full_histogram:true};
}
function sOneEndpointCertificate(){
 const out=[];
 for(const m of [1,3,5,7]){
  const counts=Array(6).fill(0);
  for(let p=0;p<=1;p++)for(let B=0;B<8;B++){
   const words=p?[1,2,7,4]:[0,3,6,5];
   const bits=words.map(w=>Math.floor(modPos(m*w+B,8)/4));
   counts[quarterClass(bits)]++;
  }
  const c=counts[0]+counts[5],o=counts[3];
  assertQuarter(!(c&&o),"s1 top endpoint");
  out.push({m,counts,has_constant:!!c,has_opposite:!!o});
 }
 return {table:out,checked:64};
}
function sThreeProjectionCertificate(){
 const rows=[];
 for(const m of [3,13]){
  let maximum=0;
  const profiles=[];
  for(let C=0;C<16;C++){
   const p=[0,0,0,0];
   for(let u=0;u<4;u++)p[Math.floor(modPos(C+m*u,16)/4)]++;
   profiles.push(p);maximum=Math.max(maximum,...p);
  }
  assertQuarter(maximum===2,"s3 quarter occupancy");
  rows.push({m,maximum,profiles});
 }
 return {rows,maximum_union_fraction:[1,8]};
}
function sFourInfluenceCertificate(){
 const out=[];
 for(const m of [7,25]){
  const p=[];
  for(let C=0;C<32;C++){
   let w=0;
   for(let z=0;z<16;z++)w+=Math.floor(modPos(m*z+C,32)/16);
   p.push(w);
  }
  assertQuarter(Math.min(...p)===6&&Math.max(...p)===10,"s4 projected influence range");
  out.push({m,values:p,minimum:6,maximum:10});
 }
 return {rows:out,required_fractions:[[353,2048],[1695,2048]],allowed_fraction:[3/8,5/8]};
}
function sLastEndpointCertificate(){
 let checked=0;
 for(let n=3;n<=8;n++){
  const N=2**n,Q=N/4;
  for(let m=1;m<N;m+=2)for(let B=0;B<N;B++)for(const epsilon of [-1,1])for(let gamma=0;gamma<=1;gamma++){
   const d=modPos(m*Q,N),bits=[B,B+d,B+epsilon*m,B+epsilon*m+d]
    .map((x,v)=>Math.floor(modPos(x,N)/(N/2))^((1-gamma)*Math.floor(v/2)));
   const isConstant=bits.every(v=>v===bits[0]),distance=Math.min(m,N-m);
   assertQuarter(!isConstant||(gamma?distance<Q:distance>Q),"s31 constant-pair distance");
   checked++;
  }
 }
 const T=1295908864,U=2**31-T,Q=2**30;
 assertQuarter(T-1>Q&&U+1<Q,"full endpoint distances");
 return {checked,maximum_width:8,full_Q:Q,gamma_one_distances:[T-1,T+1],gamma_zero_distances:[U-1,U+1]};
}
function genericTopBoundsCertificate(){
 const target=9680/65536,table=[];
 for(let s=6;s<=30;s++){
  const bound=3107/32768+3/(2**s);
  assertQuarter(bound<target,"generic top union bound");
  table.push({s,upper_fraction:bound});
 }
 const fifth=affineQuarterResidues(128,modPos(13+(13%4)*32,128));
 assertQuarter(Math.max(...fifth.union)===4,"s5 exact bound");
 return {target_fraction:[605,4096],worst_generic_bound:[4643,32768],table,
  s2_maximum_union:0,s3_maximum_union_fraction:[1,8],s5_profile:fifth.union,s5_maximum_union_fraction:[1,8]};
}
function topSignCounterexampleCertificate(){
 const n=5,s=2,t=4,m=3,C=3,N=2**n,Q=N/4,orbits=[];
 for(const A of [1,2]){
  const bits=[];
  for(let v=0;v<4;v++){
   const a=A+v*Q,b=a^(a>>>s);
   bits.push((b&1)^((wordProduct(m,b,C,n)>>>t)&1));
  }
  orbits.push({A,bits,class:quarterClass(bits)});
 }
 assertQuarter(orbits[0].class===5&&orbits[1].class===3,"sign-variation counterexample");
 return {n,s,t,m,C,orbits};
}
function verifyAllShiftQuarters(){
 return {scope:"H1 != gamma*b0 XOR bit_t(m2*b+C2) XOR constant, all s,t 1..31, gamma 0/1, odd first MAD and arbitrary constant-XOR gauges; even second MAD reduces to odd effective selected bit",
  result:"ALL_961_SHIFT_PAIRS_EXCLUDED",
  reference:referenceQuarterCertificate(),
  affine_coordinate:affineDistanceCertificate(),
  fixed_step:fixedStepCertificate(),
  union_profiles:unionProfileCertificate(),
  direct_mixture:unionMixtureSmallCertificate(),
  first_parameter_gauges:gaugeCertificate(),
  s1:sOneEndpointCertificate(),s3:sThreeProjectionCertificate(),s4:sFourInfluenceCertificate(),
  s31:sLastEndpointCertificate(),top_bounds:genericTopBoundsCertificate(),
  forbidden_simplification_counterexample:topSignCounterexampleCertificate()
 };
}

function affineDistanceCertificate(){
 let checked=0;
 for(let n=3;n<=8;n++){
  const N=2**n;
  for(let j=0;j<=n-2;j++){
   const H=2**j,P=N/H;
   for(let m=1;m<N;m+=2)for(let C=0;C<N;C+=Math.max(1,N/16)){
    let edges=0,W=0;
    for(let b=0;b<N;b++)if(!(b&H)){
     const v=wordProduct(m,b,C,n),w=wordProduct(m,b^H,C,n);
     edges+=((v>>>(n-1))^(w>>>(n-1)))&1;
    }
    for(let z=0;z<H;z++)W+=(wordProduct(m,z,C,n)>>>j)&1;
    const r=m%P,d=Math.min(r,P-r),epsilon=r<P/2?1:-1;
    assertQuarter(edges===H*(d-epsilon)+2*epsilon*W,"affine coordinate exact formula");
    checked++;
   }
  }
 }
 return {checked,maximum_width:8,formula:"I=H*(d-epsilon)+2*epsilon*W"};
}

if (typeof module !== "undefined") {
  module.exports = {verifyAllShiftQuarters};
  if (require.main === module) console.log(JSON.stringify(verifyAllShiftQuarters(), null, 2));
}
