#!/usr/bin/env node
// Analytical adapter checks; requires the explicitly supplied pinned checkout.
import assert from 'node:assert/strict';
import {loadSauce,calculate} from './run_sauce_research.mjs';
const {sauce,sha256}=loadSauce(process.argv[2]);
const time=Array.from({length:3600},(_,i)=>i);
const input={ftp:200,streams:{time,watts:time.map(()=>200),moving:time.map(()=>true)},trace:true};
const full=calculate(sauce,input);
assert.equal(full.np,200);
assert.ok(Math.abs(full.stress-3599/36)<1e-10); // Upstream interval duration is N-1.
assert.equal(full.active_seconds,3599);
assert.equal(full.counts.valuePad,0);
let checks=4;
for (const gap of [1,5,15,30,60,73,74,75,300,600,4000]) {
    const after=input.streams.time.map(t=>t>=1800?t+gap:t);
    const row={...input,streams:{...input.streams,time:after},pauseSpans:[[1800,1800+gap]]};
    const raw=calculate(sauce,row);
    const informed=calculate(sauce,row,{timerAware:true});
    if (gap<74) {assert.equal(raw.counts.valuePad,gap);assert.equal(raw.counts.zeroPad,0);}
    else {assert.equal(raw.counts.valuePad,0);assert.ok(raw.counts.zeroPad>0);}
    assert.equal(informed.counts.valuePad,0);
    assert.ok(informed.counts.zeroPad>0);checks+=4;
}
// Synthetic unknown power is explicitly rejected, never JS-null-coerced to zero.
assert.throws(()=>calculate(sauce,{...input,streams:{...input.streams,watts:time.map((_,i)=>i===500?null:200)}}));checks++;
const zero=calculate(sauce,{...input,streams:{...input.streams,watts:time.map(()=>0)}});
assert.equal(zero.stress,0);assert.equal(zero.counts.observed,3600);checks+=2;
// Exact pin fills from the arriving value, not the last pre-gap value.
const edge=calculate(sauce,{...input,streams:{time:[0,1,5,6],watts:[100,100,300,300],moving:[true,true,true,true]}});
assert.deepEqual(Array.from(edge.trace.values),[100,100,300,300,300,300,300]);checks++;
console.log(JSON.stringify({checks,sha256,pinned_code:'unmodified data/power namespaces',result:'pass'}));
