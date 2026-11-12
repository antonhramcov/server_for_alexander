// Small inline loader for T123. All application files live at data-assets-base.
(()=>{
  const root=document.currentScript.closest('#aa-iso-readiness');
  if(!root||root.dataset.loaderBound==='true'||root.dataset.initialized==='true')return;
  root.dataset.loaderBound='true';
  const status=root.querySelector('#aa-load-status'),retry=root.querySelector('[data-action="retry-program"]');
  let timer,loadedScript;
  const clear=()=>{clearTimeout(timer);root.dataset.bootLoading='false';};
  const failure=()=>{clear();status.textContent=root.dataset.loadError;retry.hidden=false;};
  root.addEventListener('aa:ready',()=>{clear();status.textContent='';retry.hidden=true;});
  root.addEventListener('aa:load-error',failure);
  function load(){
    if(root.dataset.bootLoading==='true'||root.dataset.initialized==='true')return;
    const address=root.dataset.assetsBase;
    let base;
    try{base=new URL(address);if(base.protocol!=='https:'&&!(base.protocol==='http:'&&['127.0.0.1','localhost'].includes(base.hostname)))throw new Error('invalid address');}
    catch{status.textContent=root.dataset.setupMessage;retry.hidden=true;return;}
    root.dataset.loadAttempt=String(Number(root.dataset.loadAttempt||0)+1);
    root.dataset.bootLoading='true';status.textContent=root.dataset.loadMessage;retry.hidden=true;
    if(loadedScript)loadedScript.remove();
    loadedScript=document.createElement('script');
    loadedScript.src=new URL('audit-advisor.js',base.href.replace(/\/?$/,'/')).href;
    loadedScript.dataset.rootId=root.id;loadedScript.dataset.attempt=root.dataset.loadAttempt;
    loadedScript.async=true;loadedScript.crossOrigin='anonymous';loadedScript.referrerPolicy='no-referrer';
    loadedScript.onerror=failure;
    timer=setTimeout(()=>{root.dataset.loadAttempt=String(Number(root.dataset.loadAttempt)+1);failure();},30000);
    root.appendChild(loadedScript);
  }
  retry.addEventListener('click',load);load();
})();
