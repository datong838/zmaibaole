const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const path=require('node:path');
const file=path.join(__dirname,'../extension/download-reconcile.js');
async function test(){
 let searches=0,items=[],tab={id:9,windowId:3,url:'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123'};
 const sandbox={URL,Date,Number,Error,P:{origin:'https://life.douyin.com'},target:async()=>({...tab}),chrome:{downloads:{search:async()=>{searches++;return items},download:()=>{throw Error('mutation-forbidden')}}}};
 vm.createContext(sandbox);vm.runInContext(fs.readFileSync(file,'utf8'),sandbox);
 const cmd={op:'download-reconcile',tabId:9,groupid:'123',ticket:'2243af46-9390-47c2-a0ba-4f11dffc5f83',since:new Date(Date.now()-15*60000).toISOString(),filename:'门店评价_全部门店_2026_10_16-2026_10_19.xlsx'};
 assert.equal((await sandbox.reconcileDownload(cmd)).state,'pending');
 items=[{id:1,filename:'/Downloads/'+cmd.filename,url:'https://download.douyinstatic.com/a.xlsx?signature=private',state:'complete',exists:true,bytesReceived:42,totalBytes:42}];
 const result=await sandbox.reconcileDownload(cmd);assert.equal(result.state,'complete');assert.equal(result.readonly,true);assert.equal(result.ticket,cmd.ticket);assert(!JSON.stringify(result).includes('private'));assert(!('url' in result));
 items.push({...items[0],id:2});await assert.rejects(()=>sandbox.reconcileDownload(cmd),/ambiguous/);
 items=[{...items[0],url:'https://douyinstatic.com.evil.invalid/a.xlsx'}];assert.equal((await sandbox.reconcileDownload(cmd)).state,'pending');
 for(const bad of [{...cmd,filename:'secrets.xlsx'},{...cmd,since:new Date(Date.now()+60000).toISOString()},{...cmd,extra:'download'},{...cmd,groupid:'456'}])await assert.rejects(()=>sandbox.reconcileDownload(bad));
 tab.url='https://life.douyin.com/p/life_comment/management?groupid=123';await assert.rejects(()=>sandbox.reconcileDownload(cmd),/context/);
 assert.equal(searches,4);console.log('read-only download reconciliation scope/expiry/CDN/ambiguity tests passed');
}
test().catch(error=>{console.error(error);process.exitCode=1});
