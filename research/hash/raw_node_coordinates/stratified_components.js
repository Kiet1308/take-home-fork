"use strict";

function classifyStratifiedMoments(rawRows) {
  const U32 = 0xffffffff;
  const LOW30 = 0x3fffffff;
  function parity(x) {
    x ^= x >>> 16; x ^= x >>> 8; x ^= x >>> 4;
    return (0x6996 >>> (x & 15)) & 1;
  }
  function hash(x) {
    x >>>= 0;
    x = (x + 0x7ed55d16 + (x << 12)) >>> 0;
    x = (x ^ 0xc761c23c ^ (x >>> 19)) >>> 0;
    x = (x + 0x165667b1 + (x << 5)) >>> 0;
    x = ((x + 0xd3a2646c) ^ (x << 9)) >>> 0;
    x = (x + 0xfd7046c5 + (x << 3)) >>> 0;
    return (x ^ 0xb55a4f09 ^ (x >>> 16)) >>> 0;
  }
  function fusedHash(x) {
    let a = (Math.imul(4097, x) + 0x7ed55d16) >>> 0;
    let b = (a ^ (a >>> 19) ^ 0xc761c23c) >>> 0;
    let f = (Math.imul(9, ((Math.imul(33, b) + 0xe9f8cc1d) ^ (Math.imul(16896, b) + 0xaccf6200))) + 0xfd7046c5) >>> 0;
    return (f ^ (f >>> 16) ^ 0xb55a4f09) >>> 0;
  }
  function value(spec, x) {
    const h = hash(x);
    return parity(h & spec.hMask) ^ (spec.quadratic & (h >>> 30) & (h >>> 31));
  }
  const rows = rawRows.map((row, index) => {
    if (row.tag !== index || row.missing.length !== 30) throw Error("Unexpected row schema");
    return {tag: index, total: row.total >>> 0, missing: row.missing.map(x => x >>> 0)};
  });
  if (rows.length !== 4) throw Error("Four tag rows required");
  let sample = 0;
  for (let i = 0; i < 4096; i++) {
    sample = (Math.imul(sample, 1664525) + 1013904223) >>> 0;
    if (hash(sample) !== fusedHash(sample)) throw Error("Reference hash mismatch");
  }
  const witnesses = [3, 5, 6, 7, 9, 10, 12, 15, 31, 63, 127, 255,
                     0x3fffffff, 0x40000001, 0x7fffffff, 0x80000001, 0xbfffffff, U32];
  sample = 0;
  for (let i = 0; i < 256; i++) {
    sample = (Math.imul(sample, 1664525) + 1013904223) >>> 0;
    witnesses.push(sample);
  }
  const specs = [];
  function add(hMask, quadratic, label) {
    hMask >>>= 0;
    const momentMask = ((hMask & 0xfffffffe) ^ ((hMask & 1) ? (1 << 16) : 0) ^ quadratic) >>> 0;
    specs.push({id: label, hMask, quadratic, momentMask});
  }
  for (let k = 0; k < 30; k++) {
    for (let alpha = 0; alpha < 2; alpha++) for (let beta = 0; beta < 2; beta++) for (let eta = 0; eta < 2; eta++) {
      add(((1 << k) ^ (alpha << 30) ^ (beta << 31)) >>> 0, eta,
          `H${k}+${alpha}H30+${beta}H31+${eta}Q`);
    }
  }
  add(1 << 30, 0, "H30");
  add(1 << 31, 0, "H31");
  add((1 << 30) ^ (1 << 31), 0, "H30+H31");
  for (let alpha = 0; alpha < 2; alpha++) for (let beta = 0; beta < 2; beta++) for (let eta = 0; eta < 2; eta++) {
    add((3 ^ (alpha << 30) ^ (beta << 31)) >>> 0, eta,
        `H0+H1+${alpha}H30+${beta}H31+${eta}Q`);
  }
  function lowCertificate(spec, leading) {
    if (leading === 0) return {closed: false, reason: "zero-degree31-vector"};
    if ((leading >>> 30) !== 0) return {closed: true, reason: "unique-direction-is-not-low30", direction: leading};
    const delta = leading >>> 0;
    function difference(x) { return value(spec, x) ^ value(spec, (x ^ delta) >>> 0); }
    const constant = difference(0);
    let linear = 0;
    for (let j = 0; j < 32; j++) if (difference((1 << j) >>> 0) ^ constant) linear = (linear ^ (1 << j)) >>> 0;
    const pair = 0xc0000000;
    const quadratic = difference(pair) ^ constant ^ parity(pair & linear);
    for (const x of witnesses) {
      const actual = difference(x);
      const predicted = constant ^ parity(x & linear) ^ (quadratic & (x >>> 30) & (x >>> 31));
      if (actual !== predicted) return {
        closed: true, reason: "affine-plus-top-product-contradiction",
        direction: delta, constant, linear, quadratic,
        witness: {x, actual, predicted}
      };
    }
    return {closed: false, reason: "finite-witnesses-did-not-reject",
            direction: delta, constant, linear, quadratic};
  }
  function pairCertificate(spec, first, second, delta) {
    function difference(u) {
      return value(spec, (((first << 30) >>> 0) | u) >>> 0)
           ^ value(spec, (((second << 30) >>> 0) | ((u ^ delta) & LOW30)) >>> 0);
    }
    const constant = difference(0);
    let linear = 0;
    for (let j = 0; j < 30; j++) if (difference(1 << j) ^ constant) linear ^= 1 << j;
    linear >>>= 0;
    for (const word of witnesses) {
      const u = word & LOW30;
      const actual = difference(u);
      const predicted = constant ^ parity(u & linear);
      if (actual !== predicted) return {
        rejected: true, pair: [first, second], direction: delta,
        constant, linear, witness: {u, actual, predicted}
      };
    }
    return {rejected: false, pair: [first, second], direction: delta, constant, linear};
  }
  const matchings = [[[0,1],[2,3]], [[0,2],[1,3]], [[0,3],[1,2]]];
  const cases = [];
  for (const spec of specs) {
    const c = rows.map(row => parity(row.total & spec.momentMask));
    const v = rows.map(row => {
      let bits = 0;
      for (let i = 0; i < 30; i++) if (parity(row.missing[i] & spec.momentMask)) bits |= 1 << i;
      return bits >>> 0;
    });
    if ((c[0] ^ c[1] ^ c[2] ^ c[3]) !== 0) throw Error("Balanced component has nonzero full ANF coefficient");
    const leading = (v[0] ^ v[1] ^ v[2] ^ v[3]
                    ^ ((c[0] ^ c[2]) << 30)
                    ^ ((c[0] ^ c[1]) << 31)) >>> 0;
    const low = lowCertificate(spec, leading);
    const pairCache = new Map();
    const high = [];
    for (const matching of matchings) {
      const pairs = [];
      let rejected = false;
      for (const [first, second] of matching) {
        if (c[first] !== c[second]) {
          pairs.push({pair: [first,second], rejected: true, reason: "degree30-mismatch"});
          rejected = true;
        } else if (c[first] === 0) {
          const mismatch = v[first] !== v[second];
          pairs.push({pair: [first,second], rejected: mismatch,
                      reason: mismatch ? "degree29-mismatch" : "translation-not-fixed"});
          rejected ||= mismatch;
        } else {
          const key = `${first},${second}`;
          if (!pairCache.has(key)) pairCache.set(key, pairCertificate(spec, first, second, (v[first] ^ v[second]) >>> 0));
          const certificate = pairCache.get(key);
          pairs.push(certificate);
          rejected ||= certificate.rejected;
        }
      }
      if (!rejected && pairs.every(pair => pair.linear !== undefined) && pairs[0].linear !== pairs[1].linear) {
        high.push({matching, rejected: true, reason: "incompatible-low-linear-parts", pairs});
      } else {
        high.push({matching, rejected, pairs});
      }
    }
    cases.push({...spec, c, v, leading, low, high,
                closed: low.closed && high.every(matching => matching.rejected)});
  }
  const unclosed = cases.filter(row => !row.closed).map(row => ({
    id: row.id, lowClosed: row.low.closed,
    highUnclosed: row.high.filter(matching => !matching.rejected).map(matching => matching.matching)
  }));
  return {
    scope: "Affine derivatives of 251 balanced full32 hash components under independent invertible raw-node-commuting input/output encodings; complements omitted.",
    referenceHashSelfChecks: 4096,
    rows, targetCount: cases.length,
    lowClosed: cases.filter(row => row.low.closed).length,
    highClosed: cases.filter(row => row.high.every(matching => matching.rejected)).length,
    allClosed: unclosed.length === 0,
    unclosed, cases
  };
}

function verifyStratifiedClassification(certificate) {
  function insist(test, message) { if (!test) throw Error(message); }
  function parity(word) {
    let bit = 0;
    for (let i = 0; i < 32; i++) bit ^= (word >>> i) & 1;
    return bit;
  }
  function hash(x) {
    const a = (Math.imul(x, 4097) + 0x7ed55d16) >>> 0;
    const b = (a ^ (a >>> 19) ^ 0xc761c23c) >>> 0;
    const u = (Math.imul(b, 33) + 0xe9f8cc1d) >>> 0;
    const v = (Math.imul(b, 16896) + 0xaccf6200) >>> 0;
    const f = (Math.imul(u ^ v, 9) + 0xfd7046c5) >>> 0;
    return (f ^ (f >>> 16) ^ 0xb55a4f09) >>> 0;
  }
  function target(spec, x) {
    const h = hash(x);
    return parity(h & spec.hMask) ^ (spec.quadratic && (((h >>> 30) & 1) * (h >>> 31)));
  }
  function moment(spec, packed) {
    let value = spec.quadratic * (packed & 1);
    for (let bit = 0; bit < 32; bit++) if ((spec.hMask >>> bit) & 1) value ^= (packed >>> (bit === 0 ? 16 : bit)) & 1;
    return value;
  }
  const keys = new Set();
  function key(mask, q) { return (mask >>> 0) + ":" + q; }
  for (let base = 0; base < 30; base++) for (let tagMask = 0; tagMask < 4; tagMask++) for (let q = 0; q < 2; q++) {
    keys.add(key((1 << base) ^ (tagMask << 30), q));
  }
  for (let tagMask = 1; tagMask < 4; tagMask++) keys.add(key(tagMask << 30, 0));
  for (let tagMask = 0; tagMask < 4; tagMask++) for (let q = 0; q < 2; q++) keys.add(key(3 ^ (tagMask << 30), q));
  insist(certificate.cases.length === keys.size && keys.size === 251, "Wrong target count");
  const rows = certificate.rows;
  insist(rows.length === 4 && rows.every((row, tag) => row.tag === tag && row.missing.length === 30), "Wrong moment schema");
  const expectedMatchings = [[[0,1],[2,3]],[[0,2],[1,3]],[[0,3],[1,2]]];
  const counts = {casesChecked: 0, lowImmediate: 0, lowWitness: 0, highMomentRejections: 0,
                  highWitnessRejections: 0, highLinearMismatch: 0, basisValuesChecked: 0,
                  unresolvedCases: []};
  const seen = new Set();
  for (const spec of certificate.cases) {
    const id = key(spec.hMask, spec.quadratic);
    insist(keys.has(id) && !seen.has(id), "Missing or duplicate component");
    seen.add(id);
    const c = rows.map(row => moment(spec, row.total));
    const vectors = rows.map(row => {
      let answer = 0;
      for (let bit = 0; bit < 30; bit++) answer += moment(spec, row.missing[bit]) * 2**bit;
      return answer >>> 0;
    });
    insist(JSON.stringify(c) === JSON.stringify(spec.c) && JSON.stringify(vectors) === JSON.stringify(spec.v), "Moment component mismatch");
    insist(c.reduce((a,b) => a ^ b, 0) === 0, "Nonzero full degree32 coefficient");
    let direction = 0;
    for (let bit = 0; bit < 30; bit++) {
      const coefficient = rows.reduce((sum, row) => sum ^ moment(spec, row.missing[bit]), 0);
      if (coefficient) direction = (direction + 2**bit) >>> 0;
    }
    if (c[0] ^ c[2]) direction = (direction + 2**30) >>> 0;
    if (c[0] ^ c[1]) direction = (direction + 2**31) >>> 0;
    insist(direction === spec.leading, "Global leading vector mismatch");
    let lowConfirmed = false;
    const low = spec.low;
    if (low.reason === "unique-direction-is-not-low30") {
      insist(direction !== 0 && direction >= 2**30 && low.direction === direction, "Invalid immediate low rejection");
      lowConfirmed = true; counts.lowImmediate++;
    } else if (low.reason === "affine-plus-top-product-contradiction") {
      insist(direction !== 0 && direction < 2**30 && low.direction === direction, "Invalid low witness direction");
      function actual(x) { return target(spec,x) ^ target(spec,(x ^ direction) >>> 0); }
      function fitted(x) {
        return low.constant ^ parity(x & low.linear) ^ (low.quadratic * (((x >>> 30) & 1) * (x >>> 31)));
      }
      const basis = [0, 0xc0000000];
      for (let bit = 0; bit < 32; bit++) basis.push((2**bit) >>> 0);
      for (const x of basis) { insist(actual(x) === fitted(x), "Invalid low affine fit"); counts.basisValuesChecked++; }
      const witness = low.witness;
      insist(actual(witness.x) === witness.actual && fitted(witness.x) === witness.predicted && witness.actual !== witness.predicted, "Invalid low contradiction");
      lowConfirmed = true; counts.lowWitness++;
    }
    insist(lowConfirmed === low.closed, "Incorrect low classification");
    insist(spec.high.length === 3, "Wrong matching count");
    const highConfirmed = [];
    for (let index = 0; index < 3; index++) {
      const entry = spec.high[index];
      const matching = expectedMatchings[index];
      insist(JSON.stringify(entry.matching) === JSON.stringify(matching) && entry.pairs.length === 2, "Wrong tag matching");
      const rejectedPairs = [];
      for (let pairIndex = 0; pairIndex < 2; pairIndex++) {
        const pair = entry.pairs[pairIndex];
        const [left,right] = matching[pairIndex];
        insist(JSON.stringify(pair.pair) === JSON.stringify([left,right]), "Wrong pair");
        let rejected = false;
        if (c[left] !== c[right]) {
          insist(pair.reason === "degree30-mismatch", "Wrong degree30 claim");
          rejected = true; counts.highMomentRejections++;
        } else if (c[left] === 0) {
          rejected = vectors[left] !== vectors[right];
          insist(pair.reason === (rejected ? "degree29-mismatch" : "translation-not-fixed"), "Wrong degree29 claim");
          if (rejected) counts.highMomentRejections++;
        } else {
          const delta = (vectors[left] ^ vectors[right]) >>> 0;
          insist(pair.direction === delta, "Wrong forced translation");
          function actual(u) {
            return target(spec, (left * 2**30 + u) >>> 0)
                 ^ target(spec, (right * 2**30 + (u ^ delta)) >>> 0);
          }
          function fitted(u) { return pair.constant ^ parity(u & pair.linear); }
          insist(pair.linear >= 0 && pair.linear < 2**30, "Invalid low linear mask");
          const basis = [0];
          for (let bit = 0; bit < 30; bit++) basis.push(2**bit);
          for (const u of basis) { insist(actual(u) === fitted(u), "Invalid high-pair affine fit"); counts.basisValuesChecked++; }
          if (pair.witness) {
            const witness = pair.witness;
            insist(witness.u >= 0 && witness.u < 2**30, "Witness out of coset");
            insist(actual(witness.u) === witness.actual && fitted(witness.u) === witness.predicted && witness.actual !== witness.predicted, "Invalid high-pair contradiction");
            rejected = true; counts.highWitnessRejections++;
          }
        }
        insist(rejected === pair.rejected, "Wrong pair rejection flag");
        rejectedPairs.push(rejected);
      }
      let rejected = rejectedPairs.some(Boolean);
      if (!rejected && entry.reason === "incompatible-low-linear-parts") {
        insist(entry.pairs.every(pair => pair.linear !== undefined)
               && entry.pairs[0].linear !== entry.pairs[1].linear, "Invalid coefficient mismatch");
        rejected = true; counts.highLinearMismatch++;
      }
      insist(rejected === entry.rejected, "Wrong matching rejection flag");
      highConfirmed.push(rejected);
    }
    const closed = lowConfirmed && highConfirmed.every(Boolean);
    insist(closed === spec.closed, "Wrong component classification");
    if (!closed) counts.unresolvedCases.push(spec.id);
    counts.casesChecked++;
  }
  insist(seen.size === keys.size, "Incomplete target coverage");
  const allConfirmed = counts.unresolvedCases.length === 0;
  insist(allConfirmed === certificate.allClosed, "Incorrect final closure flag");
  return {...counts, allConfirmed};
}

function stratifiedGeometrySelfCheck() {
  let random = 0x6d2b79f5;
  function next() { random = (Math.imul(random,1664525)+1013904223)>>>0; return random; }
  function parity(x) { let p=0; while(x){p^=x&1;x>>>=1;} return p; }
  function moments(values, width) {
    let total=0;const missing=Array(width).fill(0);
    for(let x=0;x<values.length;x++){
      total^=values[x];
      for(let j=0;j<width;j++)if(!(x&(1<<j)))missing[j]^=values[x];
    }
    return {total,missing};
  }
  function mobius(values,width) {
    const a=values.slice();
    for(let j=0;j<width;j++)for(let x=0;x<a.length;x++)if(x&(1<<j))a[x]^=a[x^(1<<j)];
    return a;
  }
  let globalChecks=0,translatedPairs=0;
  for(let lowWidth=3;lowWidth<=8;lowWidth++){
    const lowSize=1<<lowWidth, size=lowSize*4, width=lowWidth+2;
    for(let repeat=0;repeat<24;repeat++){
      const values=Array.from({length:size},()=>next()>>>31);
      const rows=Array.from({length:4},(_,tag)=>moments(values.slice(tag*lowSize,(tag+1)*lowSize),lowWidth));
      const direct=mobius(values,width);
      for(let bit=0;bit<width;bit++){
        const recovered=bit<lowWidth ? rows.reduce((v,row)=>v^row.missing[bit],0)
          : bit===lowWidth ? rows[0].total^rows[2].total : rows[0].total^rows[1].total;
        if(recovered!==direct[(size-1)^(1<<bit)])throw Error("Global coefficient recovery failed");
      }
      globalChecks++;
      const first=values.slice(0,lowSize);
      let top=first.reduce((a,b)=>a^b,0);
      first[0]^=top^1;
      const delta=next()&(lowSize-1), linear=next()&(lowSize-1), constant=next()&1;
      const second=Array.from({length:lowSize},(_,u)=>first[u^delta]^parity(u&linear)^constant);
      const a=moments(first,lowWidth),b=moments(second,lowWidth);
      if(a.total!==1||b.total!==1)throw Error("Translation changed full coefficient");
      let recovered=0;
      for(let bit=0;bit<lowWidth;bit++)if(a.missing[bit]^b.missing[bit])recovered|=1<<bit;
      if(recovered!==delta)throw Error("Unique translation formula failed");
      translatedPairs++;
    }
  }
  return {globalMomentComparisons:globalChecks, forcedTranslationComparisons:translatedPairs,
          lowWidths:[3,4,5,6,7,8], allPassed:true};
}

function compactStratifiedCertificate(result) {
  return {
    schema: "[H mask, quadratic tag coefficient, low-direction witness or null, six high-pair witnesses or null]; null means a degree-coefficient exclusion",
    highPairOrder: [[0,1],[2,3],[0,2],[1,3],[0,3],[1,2]],
    rows: result.cases.map(row => [row.hMask, row.quadratic, row.low.witness ? row.low.witness.x : null,
      ...row.high.flatMap(matching => matching.pairs.map(pair => pair.witness ? pair.witness.u : null))])
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {classifyStratifiedMoments, verifyStratifiedClassification, stratifiedGeometrySelfCheck, compactStratifiedCertificate};
  if (require.main === module) {
    const fs = require("node:fs");
    const path = require("node:path");
    const directory = path.dirname(__filename);
    const input = JSON.parse(fs.readFileSync(path.join(directory, "stratified_component_moments.json"), "utf8"));
    const expected = JSON.parse(fs.readFileSync(path.join(directory, "stratified_component_certificate.json"), "utf8"));
    const classification = classifyStratifiedMoments(input.rows);
    const verification = verifyStratifiedClassification(classification);
    const geometry = stratifiedGeometrySelfCheck();
    if (!verification.allConfirmed || !geometry.allPassed) throw Error("Certificate verification failed");
    if (JSON.stringify(compactStratifiedCertificate(classification)) !== JSON.stringify(expected)) throw Error("Stored witness certificate differs");
    if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify({classification, verification, geometry}, null, 2) + "\n");
    console.log(JSON.stringify({verification, geometry}, null, 2));
  }
}
