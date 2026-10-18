"use strict";
// Exact gamma=1 input31 classification; these passing witnesses are not full hash solutions.
function floorSumBI(n, mod, a, b) {
  let answer=0n;
  for (;;) {
    if (a>=mod) {answer+=n*(n-1n)*(a/mod)/2n;a%=mod;}
    if (b>=mod) {answer+=n*(b/mod);b%=mod;}
    const ymax=a*n+b;
    if (ymax<mod) return answer;
    n=ymax/mod;b=ymax%mod;[a,mod]=[mod,a];
  }
}

function onesHalfBI(m,c,j) {
  const H=1n<<BigInt(j),M=BigInt(m),C=BigInt(c);
  return floorSumBI(H,H,M,C)-2n*floorSumBI(H,2n*H,M,C);
}

function affineEdgesBI(m,c,j,t) {
  const P=1n<<BigInt(t+1-j),H=1n<<BigInt(j);
  const r=BigInt(m)%P,d=r<P-r?r:P-r,sgn=r<P/2n?1n:-1n;
  return H*(d-sgn)+2n*sgn*onesHalfBI(m,c,j);
}

function inverseSmall(m,n) {
  let a=m,b=n,u=1,v=0;
  while(b){const q=Math.floor(a/b);[a,b]=[b,a-q*b];[u,v]=[v,u-q*v];}
  if(a!==1)throw new Error("not invertible");
  return (u%n+n)%n;
}

function circularProfile(n,m) {
  m%=n;const H=n/2,S=new Int8Array(n),p=new Int32Array(2*n+1);
  for(let z=0;z<H;z++)S[(m*z)%n]=1;
  for(let z=0;z<2*n;z++)p[z+1]=p[z]+S[z%n];
  const values=new Int32Array(n),inv=inverseSmall(m,n);
  let minimum=H+1,maximum=-1,rolling=0;
  for(let z=0;z<H;z++)rolling+=Math.floor((m*z)/H)%2;
  const initial=rolling;
  for(let c=0;c<n;c++){
    const start=(H-c+n)%n,count=p[start+H]-p[start];
    if(count!==rolling)throw new Error("window recurrence mismatch");
    values[c]=count;minimum=Math.min(minimum,count);maximum=Math.max(maximum,count);
    const incoming=(((inv*(H-1-c))%n+n)%n)<H;
    const outgoing=(((inv*(n-1-c))%n+n)%n)<H;
    rolling+=Number(incoming)-Number(outgoing);
  }
  if(rolling!==initial)throw new Error("window cycle mismatch");
  return {n,m,minimum,maximum,values};
}

function bracketConstant(m,j,target) {
  const H=2**j;
  let lo=0,hi=H,wlo=Number(onesHalfBI(m,lo,j)),whi=Number(onesHalfBI(m,hi,j));
  if(target<Math.min(wlo,whi)||target>Math.max(wlo,whi))return null;
  while(hi-lo>1) {
    const mid=Math.floor((lo+hi)/2),w=Number(onesHalfBI(m,mid,j));
    if(w===target)return mid;
    if((wlo-target)*(w-target)<=0){hi=mid;whi=w;}else{lo=mid;wlo=w;}
  }
  if(wlo===target)return lo;
  if(whi===target)return hi;
  throw new Error("integer intermediate value violation");
}

function classifyAllShiftInfluences() {
  const targetFull=1295908864,total=2**31,rows=[],cache=new Map(),profileCertificates=[];
  const profile=(n,m)=>{
    const key=`${n}:${m%n}`;
    if(!cache.has(key)){
      const p=circularProfile(n,m);cache.set(key,p);
      profileCertificates.push({n:p.n,m:p.m,minimum:p.minimum,maximum:p.maximum});
    }
    return cache.get(key);
  };
  const record=(row,status,reason,extra={})=>rows.push({...row,status,reason,...extra});
  const pass=(row,m,c,reason,extra={})=>{
    const count=affineEdgesBI(m,c,row.j,row.t);
    if(count!==BigInt(row.required_affine_edges))throw new Error(`bad witness ${row.s},${row.t}`);
    record(row,"PASSES_INFLUENCE",reason,{witness:{m2:m,C2:c,affine_edges:Number(count)},...extra});
  };
  for(let s=1;s<=31;s++)for(let t=1;t<=31;t++){
    const j=31-s,row={s,t,j};
    if(j>=t){record(row,"EXCLUDED","constant input31 derivative");continue;}
    if(t<14){record(row,"EXCLUDED","nonintegral edge replication");continue;}
    if(t===14){record(row,"EXCLUDED","affine coordinate edges must be even");continue;}
    const complement=Number((j===0)!==(t===31));
    const requiredFull=complement?total-targetFull:targetFull;
    const I=requiredFull/2**(31-t),L=I/2**(t-14),H=2**j,N=2*H,P=2**(t+1-j),E=t-14-j;
    Object.assign(row,{complement,required_affine_edges:I,L,H,P,E});
    if(E>0){
      const R=I/H,distances=[R-1,R+1].filter(d=>d>0&&d<P/2);
      let answer=null;
      for(const d of distances){
        const W=(I-H*(d-1))/2;
        if(W!==0&&W!==H)throw new Error("nonendpoint");
        for(const mlo of new Set([1,N-1])){
          let m;
          if(P>=N){m=d;if(m%N!==mlo)continue;}
          else {m=mlo;if(m%P!==d)continue;}
          const c=(mlo===1)?(W===0?0:H):(W===0?H-1:N-1);
          answer={m,c,d,W};break;
        }
        if(answer)break;
      }
      if(answer)pass(row,answer.m,answer.c,"endpoint congruences",answer);
      else record(row,"EXCLUDED","endpoint congruences incompatible",{distances});
      continue;
    }
    if(E===0){
      const m=L,c=(((m-1-H)/2)%H+H)%H;
      pass(row,m,c,"balanced half profile");continue;
    }
    const k=-E,d=2*Math.floor(L/2**(k+1))+1,W=(I-H*(d-1))/2;
    Object.assign(row,{k,d,required_half_ones:W});
    if(N<P){
      const p=profile(N,d);
      const c=p.values.findIndex(value=>value===W);
      if(c>=0)pass(row,d,c,"complete smaller profile",{profile_modulus:N});
      else record(row,"EXCLUDED","complete smaller profile",{profile_modulus:N,minimum:p.minimum,maximum:p.maximum});
      continue;
    }
    const p=profile(P,d),delta=N/P,min=delta*p.minimum,max=delta*p.maximum;
    if(W<min||W>max){
      record(row,"EXCLUDED","small-residue projection",{profile_modulus:P,minimum:min,maximum:max});continue;
    }
    if(delta>=2 && (W===min||W===max)){
      const extrema=W===min?p.minimum:p.maximum,S=[];
      p.values.forEach((v,c)=>{if(v===extrema)S.push(c)});
      const set=new Set(S),steps=[(d-1)/2,(d+1)/2,(d+P-1)/2,(d+P+1)/2];
      const pair=steps.some(step=>S.some(c=>set.has((c+step)%P)));
      if(!pair){
        record(row,"EXCLUDED","projection endpoint incompatible pair",{profile_modulus:P,extremal_bases:S,required_steps:steps});continue;
      }
    }
    const c=bracketConstant(d,j,W);
    if(c!==null)pass(row,d,c,"constructive floor-sum bracket");
    else record(row,"UNRESOLVED","projection bound inconclusive",{profile_modulus:P,minimum:min,maximum:max});
  }
  const counts={},reasons={};
  for(const row of rows){counts[row.status]=(counts[row.status]||0)+1;reasons[row.reason]=(reasons[row.reason]||0)+1;}
  return {target_full_input31_edges:targetFull,rows,counts,reasons,
    profile_certificates:profileCertificates,
    largest_profile_modulus:Math.max(...profileCertificates.map(p=>p.n)),
    total_profile_windows:profileCertificates.reduce((sum,p)=>sum+p.n,0)};
}
if (typeof module !== "undefined") {
  module.exports = {classifyAllShiftInfluences};
  if (require.main === module) console.log(JSON.stringify(classifyAllShiftInfluences(), null, 2));
}
