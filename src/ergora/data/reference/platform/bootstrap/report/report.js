
'use strict';
const data=JSON.parse(document.getElementById('artifact-data').textContent);
const toast=document.getElementById('toast'); let timer;
function tell(msg){toast.textContent=msg;toast.classList.add('show');clearTimeout(timer);timer=setTimeout(()=>toast.classList.remove('show'),3300)}
function saveBase64(b64,name,mime){const binary=atob(b64),bytes=new Uint8Array(binary.length);for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);const blob=new Blob([bytes],{type:mime||'application/octet-stream'}),u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);tell('已准备下载：'+name)}
function downloadKit(){saveBase64(data.zip,'training-efficiency-kit.zip','application/zip')}
document.getElementById('download-kit').addEventListener('click',downloadKit);document.querySelectorAll('[data-kit]').forEach(b=>b.addEventListener('click',downloadKit));
document.querySelectorAll('[data-download]').forEach(b=>b.addEventListener('click',()=>{const key=b.dataset.download;if(!data.files[key]){tell('文件未包含在部署包中');return}saveBase64(data.files[key],key.split('/').pop())}));
async function copyText(text){
  let copied=false;
  if(navigator.clipboard&&window.isSecureContext){try{await navigator.clipboard.writeText(text);copied=true}catch(e){}}
  if(!copied){const el=document.createElement('textarea');el.value=text;el.style.position='fixed';el.style.opacity='0';document.body.appendChild(el);try{el.select();copied=document.execCommand('copy')}catch(e){}finally{el.remove()}}
  tell(copied?'已复制':'浏览器阻止了复制，请下载对应任务文件');
}
document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',()=>copyText(b.parentElement.querySelector('code').textContent)));
document.getElementById('copy-setup').addEventListener('click',()=>copyText(data.setup));document.querySelectorAll('[data-setup]').forEach(b=>b.addEventListener('click',()=>copyText(data.setup)));
const storageKey='training-efficiency-v1-checks';let saved={};try{saved=JSON.parse(localStorage.getItem(storageKey)||'{}')}catch(e){}
const checks=[...document.querySelectorAll('[data-check]')];
function progress(){let n=0;checks.forEach(c=>{c.parentElement.classList.toggle('done',c.checked);if(c.checked)n++});document.getElementById('progress').max=checks.length;document.getElementById('progress').value=n;document.getElementById('progress-text').textContent=n+' / '+checks.length}
checks.forEach(c=>{c.checked=!!saved[c.dataset.check];c.addEventListener('change',()=>{saved[c.dataset.check]=c.checked;try{localStorage.setItem(storageKey,JSON.stringify(saved))}catch(e){tell('浏览器无法保存清单，本次页面内仍可使用')}progress()})});progress();
document.getElementById('reset').addEventListener('click',()=>{checks.forEach(c=>c.checked=false);saved={};try{localStorage.removeItem(storageKey)}catch(e){}progress();tell('清单已重置')});
let filter='全部';const cards=[...document.querySelectorAll('.direction')],search=document.getElementById('search');
function applyFilter(){const q=search.value.trim().toLowerCase();let n=0;cards.forEach(c=>{const show=(filter==='全部'||c.dataset.tag===filter)&&(!q||c.dataset.search.includes(q));c.hidden=!show;if(show)n++});document.getElementById('match-count').textContent='显示 '+n+' / '+cards.length+' 个方向';document.getElementById('no-results').hidden=n!==0}
search.addEventListener('input',applyFilter);document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>{const selected=x===b;x.classList.toggle('selected',selected);x.setAttribute('aria-pressed',String(selected))});applyFilter()}));
let printState=[];function beforePrint(){printState=[...document.querySelectorAll('details')].map(d=>[d,d.open,d.hidden]);printState.forEach(([d])=>{d.hidden=false;d.open=true})}function afterPrint(){printState.forEach(([d,o,h])=>{d.open=o;d.hidden=h});printState=[]}
window.addEventListener('beforeprint',beforePrint);window.addEventListener('afterprint',afterPrint);document.getElementById('print').addEventListener('click',()=>window.print());
document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{const target=document.getElementById(a.getAttribute('href').slice(1));if(!target)return;for(let p=target.parentElement;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}if(target.tagName==='DETAILS')target.open=true;}));
if('IntersectionObserver'in window){const ob=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){document.querySelectorAll('.rail nav a').forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id))}})},{rootMargin:'-15% 0px -65% 0px'});document.querySelectorAll('main section').forEach(s=>ob.observe(s))}
