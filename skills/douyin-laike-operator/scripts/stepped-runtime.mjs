/* Cooperative executor for slow host calls. Each step() issues at most ONE UI
 * request inside an active cua_repl invocation. Uses ONLY documented public APIs.
 * Does not inspect host internals or execute browser calls in a background job.
 */
import role from './acquire.mjs';
const METHODS=['context','account','openSwitch','searchCompany','chooseCompany','confirmSwitch','verifySwitch','openReviews','openPageCalendar','calendarDate','verifyFilter','openExportMenu','openExportDialog','exportRange','openExportCalendar','prepareSubmit','submit','recordTabs','openRecordMenu','useRecordTab','listRecords','verifyRecord','prepareDownload','armDownload','clickDownload','downloadResult'];
function classify(error){
  if(!error)return null;
  if(/Debugger unattached|could not read requirements|browser is not available|disconnected/i.test(error))return 'connection-unavailable';
  for(const code of ['risk-prompt','captcha','login-required','account-changed','identity-unverified','source-company-mismatch','company-not-found','company-ambiguous','export-outcome-unknown','download-outcome-unknown'])if(error.includes(code))return code;
  return /timed? ?out|timeout/i.test(error)?'ui-outcome-unknown':'operator-step-failed';
}

export async function createSteppedOperator(browser,tab,job) {
  const queue=[];
  let running=false,result=null,error=null,method=null,executing=false;
  const locatorFactories=new WeakMap();
  function enqueue(label,run,registerOnly=false) {
    return new Promise((resolve,reject)=>queue.push({label,run,resolve,reject,registerOnly}));
  }
  function realOptions(options) {
    if(!options)return options;
    const out={...options};
    for(const key of ['has','hasNot'])if(out[key]&&locatorFactories.has(out[key]))out[key]=locatorFactories.get(out[key])();
    return out;
  }
  function locator(factory) {
    const obj={};locatorFactories.set(obj,factory);
    for(const name of ['count','isVisible','isEnabled','innerText','getAttribute','evaluate','evaluateAll','click','fill','waitFor'])
      obj[name]=(...args)=>enqueue('locator.'+name,()=>factory()[name](...args));
    for(const name of ['getByText','getByRole','getByPlaceholder','getByLabel','getByTestId'])
      obj[name]=(...args)=>locator(()=>factory()[name](...args));
    obj.locator=(...args)=>locator(()=>factory().locator(...args));
    obj.filter=options=>locator(()=>factory().filter(realOptions(options)));
    return obj;
  }
  function wrapTab(realTab) {
    const playwright={};
    for(const name of ['getByText','getByRole','getByPlaceholder','getByLabel','getByTestId','locator'])
      playwright[name]=(...args)=>locator(()=>realTab.playwright[name](...args));
    for(const name of ['domSnapshot','evaluate'])playwright[name]=(...args)=>enqueue('tab.'+name,()=>realTab.playwright[name](...args));
    playwright.waitForEvent=(event,options)=>{
      if(event!=='download')throw Error('only-download-events-supported');
      // This queue item REGISTERS the documented event waiter, without blocking
      // the next UI command (the click). The eventual result never calls a UI API.
      return enqueue('register.download',()=>realTab.playwright.waitForEvent(event,options),true)
        .then(download=>({path:opts=>enqueue('download.path',()=>download.path(opts))}));
    };
    return {id:realTab.id,url:()=>enqueue('tab.url',()=>realTab.url()),playwright};
  }
  const wrappedBrowser={tabs:{
    list:()=>enqueue('tabs.list',()=>browser.tabs.list()),
    get:id=>enqueue('tabs.get',()=>browser.tabs.get(id)).then(wrapTab)
  }};
  const op=await role.create(wrappedBrowser,wrapTab(tab),job);
  async function flush(){for(let i=0;i<16;i++)await Promise.resolve();}
  const controller={
    async start(name,...args){
      if(running || queue.length)throw Error('operator-step-still-running');
      if(error)throw Error('previous-step-failed: record failure and reconstruct from durable work order before continuing');
      if(!METHODS.includes(name))throw Error('operator-method-not-allowed');
      running=true;result=null;error=null;method=name;
      // The role is now pure cooperative logic: it only enqueues UI work. Real
      // host API requests are made exclusively by awaited step(), never here.
      Promise.resolve().then(()=>op[name](...args)).then(value=>{result=value;running=false;},reason=>{error=String(reason);running=false;});
      await flush();return this.status();
    },
    status(){return {method,state:error?'failed':running?'running':'complete',next:queue[0]?.label||null,pending:queue.length,result,error,error_code:classify(error)};},
    async step(){
      if(executing)throw Error('operator-ui-step-busy');
      executing=true;
      try {
      await flush();const item=queue.shift();
      if(!item)return this.status();
      try {
        if(item.registerOnly){
          // Calling the API here synchronously attaches the active invocation's
          // host requirements. Only promise settlement occurs after this returns.
          Promise.resolve(item.run()).then(item.resolve,item.reject);
        }else item.resolve(await item.run());
      }catch(e){item.reject(e);}
      await flush();return this.status();
      }finally{executing=false;}
    }
  };
  for(const name of METHODS)controller[name]=(...args)=>controller.start(name,...args);
  return controller;
}
export default createSteppedOperator;
