#!/usr/bin/env node
// Exact original-hash full32 ANF collector. Default invocation runs a small
// independent check; --full32 runs all 4,294,967,296 inputs.
import {writeFileSync} from "node:fs";

async function packedStratifiedMoments(lowWidth=30, chunkBits=16, state=null, onProgress=null) {
  if (!(lowWidth>=1 && lowWidth<=30 && chunkBits>=1 && chunkBits<=lowWidth)) throw Error("invalid widths");
  const size=2**chunkBits, chunksPerTag=2**(lowWidth-chunkBits), totalChunks=4*chunksPerTag;
  const words=new Uint32Array(size);
  if (!state) state={lowWidth,chunkBits,cursor:0,rows:Array.from({length:4},(_,tag)=>({tag,total:0,upper:Array(lowWidth).fill(0)}))};
  if (state.lowWidth!==lowWidth || state.chunkBits!==chunkBits) throw Error("resume width mismatch");
  const started=Date.now(), initialCursor=state.cursor;
  for (;state.cursor<totalChunks;) {
    const tag=Math.floor(state.cursor/chunksPerTag), local=state.cursor%chunksPerTag, base=local*size;
    const row=state.rows[tag];
    for(let i=0;i<size;i++){
      let h=(tag*2**30+base+i)>>>0;
      h=(h+0x7ed55d16+(h<<12))>>>0;
      h=(h^0xc761c23c^(h>>>19))>>>0;
      h=(h+0x165667b1+(h<<5))>>>0;
      h=((h+0xd3a2646c)^(h<<9))>>>0;
      h=(h+0xfd7046c5+(h<<3))>>>0;
      h=(h^0xb55a4f09^(h>>>16))>>>0;
      words[i]=((h&0xfffffffe)|((h>>>30)&(h>>>31)&1))>>>0;
    }
    let len=size;
    for(let bit=0;bit<chunkBits;bit++){
      let rightXor=0;
      for(let i=0;i<len/2;i++){
        const right=words[2*i+1];
        rightXor^=right;
        words[i]=words[2*i]^right;
      }
      row.upper[bit]=(row.upper[bit]^rightXor)>>>0;
      len/=2;
    }
    const total=words[0];
    row.total=(row.total^total)>>>0;
    for(let bit=chunkBits;bit<lowWidth;bit++) if ((base>>>bit)&1) row.upper[bit]=(row.upper[bit]^total)>>>0;
    state.cursor++;
    if(onProgress && (state.cursor%512===0 || state.cursor===totalChunks)) await onProgress(state);
  }
  return {state,elapsedMs:Date.now()-started,inputsProcessed:(state.cursor-initialCursor)*size,
    rows:state.rows.map(row=>({tag:row.tag,total:row.total,missing:row.upper.map(v=>(v^row.total)>>>0)}))};
}

function fusedHash(x) {
  const a=(Math.imul(4097,x)+0x7ed55d16)>>>0;
  const b=(a^(a>>>19)^0xc761c23c)>>>0;
  const u=(Math.imul(33,b)+0xe9f8cc1d)>>>0;
  const v=(Math.imul(16896,b)+0xaccf6200)>>>0;
  const f=(Math.imul(9,u^v)+0xfd7046c5)>>>0;
  return (f^(f>>>16)^0xb55a4f09)>>>0;
}
async function verifyCollector() {
  const result=await packedStratifiedMoments(8,5);
  for(let tag=0;tag<4;tag++){
    let total=0;const missing=Array(8).fill(0);
    for(let x=0;x<256;x++){
      const h=fusedHash((tag*2**30+x)>>>0);
      const p=((h&0xfffffffe)|((h>>>30)&(h>>>31)&1))>>>0;
      total^=p;
      for(let bit=0;bit<8;bit++) if(!((x>>>bit)&1)) missing[bit]^=p;
    }
    if(result.rows[tag].total!==(total>>>0) || missing.some((v,j)=>(v>>>0)!==result.rows[tag].missing[j])) throw Error("independent reduced-domain moment check failed");
  }
  return {width:8,independent_inputs:1024,all_passed:true};
}

const precheck=await verifyCollector();
if(!process.argv.includes("--full32")){
  process.stdout.write(JSON.stringify(precheck,null,2)+"\n");
}else{
  const result=await packedStratifiedMoments(30,16,null,state=>{
    if(state.cursor%2048===0) process.stderr.write(state.cursor+"/65536 chunks\n");
  });
  const report={
    description:"Exact top-two-input-bit-stratified ANF moments for all 2^32 original six-stage hash inputs. Packed bit0 is H30*H31; bits1..31 are H1..31.",
    inputs:4294967296,
    elapsed_ms:result.elapsedMs,
    precheck,
    rows:result.rows
  };
  const output=process.argv.find(a=>a.startsWith("--output="))?.slice(9)||"raw_tag_all_coordinate_moments.json";
  writeFileSync(output,JSON.stringify(report,null,2)+"\n");
  process.stdout.write(JSON.stringify({output,inputs:report.inputs,elapsed_ms:report.elapsed_ms})+"\n");
}
