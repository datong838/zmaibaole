import assert from 'node:assert/strict';
import {recoverConnection} from '../scripts/workflow-runtime.mjs';
const job={recovery_request:{kind:'connection-recovery',id:'attempt-1'}};
const base={state:'failed',phase:'submit',error_code:'connection-unavailable',error:'Debugger unattached',exportPending:true,attempts:1};
let s=structuredClone(base);
assert.equal(recoverConnection(s,job),true);assert.equal(s.phase,'account');assert.equal(s.recoverPhase,'recordTabs');assert.equal(s.exportPending,true);assert.equal(s.attempts,1);
s.state='failed';s.error_code='connection-unavailable';assert.equal(recoverConnection(s,job),false);
s=structuredClone(base);s.downloadPending=true;assert.throws(()=>recoverConnection(s,job),/download-outcome-unknown/);
for(const error_code of ['risk-prompt','account-changed','captcha']){s={...structuredClone(base),error_code};assert.equal(recoverConnection(s,job),false);assert.equal(s.state,'failed');}
s=structuredClone(base);s.exportPending=false;assert.equal(recoverConnection(s,job),true);assert.equal(s.recoverPhase,null);
console.log('Explicit connection recovery preserves intents, refreshes identity, refuses risk/download replay.');
