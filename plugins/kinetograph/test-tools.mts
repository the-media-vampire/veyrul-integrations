import assert from 'node:assert/strict';
import { tools } from './tools.ts';
const compare=tools[0]!.run, font=tools[1]!.run;
const results:Record<string,unknown>={};let checks=0;
function test(name:string,run:()=>unknown){results[name]=run()??true;checks++;}
test('alpha_zero_tolerance_detects_one_level',()=>{const r:any=compare({channel:'alpha8',reference:[0,64,192,255],decoded:[0,64,193,255],tolerance:0});assert.equal(r.status,'outside_supplied_tolerance');assert.equal(r.max_error,1);return r;});
test('alpha_caller_accepts_one_level',()=>{const r:any=compare({channel:'alpha8',reference:[0,64,192,255],decoded:[0,64,193,255],tolerance:1});assert.equal(r.status,'within_supplied_tolerance');});
test('issue111_reported_pixel_detects_error16',()=>{const r:any=compare({channel:'rgb8',reference:[145,95,243],decoded:[141,79,237],tolerance:2});assert.equal(r.max_error,16);assert.equal(r.status,'outside_supplied_tolerance');return r;});
test('issue111_reported_control_error1',()=>{const r:any=compare({channel:'rgb8',reference:[145,95,243],decoded:[145,94,243],tolerance:2});assert.equal(r.max_error,1);assert.equal(r.status,'within_supplied_tolerance');});
test('channel_max_bound',()=>{assert.equal((compare({channel:'alpha8',reference:[0],decoded:[255],tolerance:255}) as any).max_error,255);});
for(const [name,input] of Object.entries({empty:{reference:[],decoded:[]},mismatch:{reference:[1],decoded:[1,2]},negative:{reference:[-1],decoded:[0]},too_large:{reference:[256],decoded:[0]},float:{reference:[1.1],decoded:[0]},nonfinite:{reference:[Infinity],decoded:[0]},oversize:{reference:Array(257).fill(1),decoded:Array(257).fill(1)},bad_tolerance:{tolerance:-1},extra:{private_file:'/not-read'},rgb_truncated:{channel:'rgb8',reference:[1],decoded:[1]}})){
 test('reject_'+name,()=>assert.throws(()=>compare({channel:'alpha8',reference:[1],decoded:[1],tolerance:0,...input})));
}
test('font_missing_deduplicated_sorted',()=>{const r:any=font({required:[0x2691,0x2399,0x2691,65],covered:[65]});assert.deepEqual(r.missing,['U+2399','U+2691']);return r;});
test('font_covered_is_not_render_proof',()=>{const r:any=font({required:[65],covered:[65]});assert.equal(r.status,'covered_by_supplied_set');assert.ok(r.limitation.includes('shaping'));});
test('font_supplementary_scalar',()=>{assert.deepEqual((font({required:[0x1f600],covered:[]}) as any).missing,['U+1F600']);});
for(const value of [-1,0x110000,0xd800,1.2])test('font_reject_'+value,()=>assert.throws(()=>font({required:[value],covered:[]})));
test('input_unchanged',()=>{const x=Object.freeze({channel:'alpha8',reference:Object.freeze([1]),decoded:Object.freeze([1]),tolerance:0});compare(x);assert.deepEqual(x.reference,[1]);});
console.log(JSON.stringify({status:'passed',checks}));
