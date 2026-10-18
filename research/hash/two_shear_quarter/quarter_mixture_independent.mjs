#!/usr/bin/env node
function quarterMixtureCheck(){
  let checked=0, gaugeChecked=0; const byWidth=[];
  let rng=0x13789abd; function next(){rng=(Math.imul(rng,1664525)+1013904223)>>>0;return rng;}
  function unionPattern(p){return p===0||p===15||p===5||p===10}
  function actual(n,s,m,C,first=1,firstC=0,ki=0,K=0){
    const N=2**n,Q=N/4,mask=N-1;let count=0;
    for(let x=0;x<Q;x++){let p=0;for(let v=0;v<4;v++){
      const raw=(x+Q*v)^ki, a=(first*raw+firstC)&mask,b=(a^(a>>>s)^K)&mask;
      p|=((b&1)^(((m*b+C)&mask)>>>(n-1)))<<v;
    } if(unionPattern(p))count++;}
    return count;
  }
  function profile(s,m){
    const M=2**(s+2),mask=M-1,step=(m*(1+2**s))&mask,counts=[0,0,0,0];
    for(let q=0;q<M;q++){let p=0;for(let v=0;v<4;v++)p|=(((q+v*step)&mask)>>>(s+1))<<v;
      if(unionPattern(p))counts[q&3]++;
    }
    const R=2**(s+1),r=m&(R-1),dm=Math.min(r,R-r),length=Math.max(3*dm-2**s,0);
    if(counts.reduce((a,b)=>a+b,0)!==2*length)throw Error("length sum");
    if(counts.some(x=>x>2*Math.ceil(length/4)))throw Error("length bound");
    return counts;
  }
  for(let n=4;n<=12;n++){
    const N=2**n,mask=N-1;let current=0;
    for(let s=2;s<=n-2;s++){
      const ell=2**(n-2-s);
      const cases=[];
      if(n<=7){for(let m=1;m<N;m+=2)for(let C=0;C<N;C++)cases.push([m,C]);}
      else for(let j=0;j<32;j++)cases.push([(next()&mask)|1,next()&mask]);
      const cache=new Map();
      for(const [m,C]of cases){
        if(!cache.has(m))cache.set(m,profile(s,m));
        const counts=cache.get(m);let predicted=0;
        for(let z=0;z<ell;z++)predicted+=counts[Math.floor((m*z+C)/ell)&3];
        const got=actual(n,s,m,C);
        if(got!==predicted)throw Error(JSON.stringify({n,s,m,C,got,predicted,counts}));
        checked++;current++;
        if(n>=8){
          const gotGauge=actual(n,s,m,C,(next()&mask)|1,next()&mask,next()&mask,next()&mask);
          if(gotGauge!==predicted)throw Error("gauge mismatch");
          gaugeChecked++;
        }
      }
    }
    byWidth.push({width:n,cases:current});
  }
  return{all_passed:true,checked,gaugeChecked,byWidth};
}
console.log(JSON.stringify(quarterMixtureCheck(), null, 2));
