#!/usr/bin/env node
// Research adapter: execute unmodified pinned Sauce data/power namespaces only.
// No browser, storage, network, FTP lookup, HR fallback, or daily aggregation.
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import readline from 'node:readline';
import {execFileSync} from 'node:child_process';

export const PIN = '4b6d4f42bf56d064507d694abd56e5f989530e03';
export function loadSauce(directory) {
    const revision = execFileSync('git', ['-C', directory, 'rev-parse', 'HEAD'], {encoding: 'utf8'}).trim();
    if (revision !== PIN) throw new Error('Wrong Sauce revision');
    const source = fs.readFileSync(`${directory}/src/common/lib.js`);
    const committed = execFileSync('git', ['-C', directory, 'show', `${PIN}:src/common/lib.js`], {maxBuffer: 2**22});
    if (!source.equals(committed)) throw new Error('Modified Sauce calculation source');
    const sauce = {ns(name, factory) {
        if (['data', 'power'].includes(name)) this[name] = factory();
    }};
    vm.runInNewContext(source.toString(), {sauce}, {filename: 'pinned-sauce-lib.js', timeout: 10000});
    return {sauce, sha256: crypto.createHash('sha256').update(source).digest('hex')};
}

export function calculate(sauce, row, options={}) {
    const streams = row.streams;
    if (streams.time.length !== streams.watts.length || streams.time.length < 2) return null;
    for (let i=0; i<streams.time.length; i++) {
        if (!Number.isFinite(streams.watts[i]) || streams.watts[i] < 0 || !Number.isFinite(streams.time[i]) ||
            (i && streams.time[i] <= streams.time[i-1])) throw new Error('Adapter requires valid unique ordered power; never coerce null to zero');
    }
    const active = sauce.data.createActiveStream(streams, {isTrainer: true, ...options});
    if (options.timerAware && row.pauseSpans) {
        for (let i=1; i<active.length; i++) {
            if (row.pauseSpans.some(([a,b]) => streams.time[i-1] < b && streams.time[i] >= a)) active[i]=false;
        }
    }
    const corrected = sauce.power.correctedPower(streams.time, streams.watts, {activeStream: active});
    const np = corrected.np();
    const average = corrected.avg({active: true});
    const seconds = sauce.data.activeTime(streams.time, active);
    const power = np || average; // Match the pinned processor's explicit fallback.
    const stress = sauce.power.calcTSS(power, seconds, row.ftp);
    const counts = {observed: 0, valuePad: 0, zeroPad: 0, breakPad: 0};
    for (const value of corrected.values()) {
        const key = value instanceof sauce.data.Break ? 'breakPad' : value instanceof sauce.data.Zero ? 'zeroPad' :
            value instanceof sauce.data.Pad ? 'valuePad' : 'observed';
        counts[key]++;
    }
    return {stress: Number.isFinite(stress) ? stress : null, np: np ?? null, average,
        active_seconds: seconds, corrected_active_seconds: corrected.active(), work_kj: corrected.joules()/1000,
        counts, idealGap: corrected.idealGap, maxGap: corrected.maxGap,
        active, trace: row.trace ? {times: corrected.times(), values: corrected.values().map(Number),
            kinds: corrected.values().map(v => v instanceof sauce.data.Break ? 'break' : v instanceof sauce.data.Zero ? 'zero' : v instanceof sauce.data.Pad ? 'pad' : 'observed')} : undefined};
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
    const [directory,input,output] = process.argv.slice(2);
    const {sauce,sha256} = loadSauce(directory);
    const handle=fs.openSync(output,'w');
    for await (const line of readline.createInterface({input:fs.createReadStream(input),crlfDelay:Infinity})) {
        if (!line.trim()) continue;
        const row=JSON.parse(line);
        const result={key:row.key,sha256};
        for (const [name,options] of Object.entries(row.variants || {sauce:{}})) {
            const value=calculate(sauce,row,options);
            if (value && !row.trace) delete value.active;
            result[name]=value;
        }
        fs.writeSync(handle,JSON.stringify(result)+'\n');
    }
    fs.closeSync(handle);
}
