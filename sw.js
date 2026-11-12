const V="memolex-1.9.3",SHELL=["./","index.html","manifest.webmanifest","icon-192.png","icon-512.png","lists-de-fr.json","examples-de-fr.json","chunks-de-fr.json","lists-it-fr.json","examples-it-fr.json","chunks-it-fr.json"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL.map(u=>new Request(u,{cache:"reload"})))));self.skipWaiting();});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))));self.clients.claim();});
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(e.request.method!=="GET"||u.hostname.endsWith(".supabase.co"))return;
  if(u.origin===location.origin&&!u.pathname.endsWith(".json")){ // l'appli : réseau d'abord, copie hors ligne sinon
    const key=e.request.mode==="navigate"?"index.html":e.request;
    e.respondWith(fetch(e.request,{cache:"no-cache"}).then(r=>{const cp=r.clone();if(r.ok)caches.open(V).then(c=>c.put(key,cp));return r;}).catch(()=>caches.match(key).then(r=>r||caches.match("index.html"))));return;}
  // listes, dictionnaire, polices : copie locale d'abord (renouvelée à chaque nouvelle version)
  e.respondWith(caches.open(V).then(c=>c.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r.ok)c.put(e.request,r.clone());return r;}))));});

// ---------- notifications (envoyées par la fonction Supabase memolex-push) ----------
// Le bouton « Ajouter » range le mot dans IndexedDB (mx / inbox) : l'appli l'ajoute à son prochain lancement, sans avoir à l'ouvrir.
function inboxAdd(item){return new Promise(res=>{const r=indexedDB.open("mx",1);r.onupgradeneeded=()=>r.result.createObjectStore("inbox",{autoIncrement:true});
  r.onerror=()=>res(false);r.onsuccess=()=>{const db=r.result,tx=db.transaction("inbox","readwrite");tx.objectStore("inbox").add(item);tx.oncomplete=()=>{db.close();res(true);};tx.onerror=()=>{db.close();res(false);};};});}
self.addEventListener("push",e=>{let d={};try{d=e.data?e.data.json():{};}catch(_){d={title:"Memolex",body:e.data?e.data.text():""};}
  const o={body:d.body||"",icon:"icon-192.png",badge:"icon-192.png",tag:d.kind||"memolex",renotify:true,data:d};
  if(d.kind==="wotd"&&d.word)o.actions=[{action:"add",title:"Ajouter à l’apprentissage"}];
  e.waitUntil(self.registration.showNotification(d.title||"Memolex",o));});
self.addEventListener("notificationclick",e=>{const n=e.notification,d=n.data||{};n.close();
  if(e.action==="add"&&d.word){const w=d.word,label=(w.f.art?w.f.art+(/'$/.test(w.f.art)?"":" "):"")+w.f.de;
    e.waitUntil(inboxAdd(w).then(()=>self.clients.matchAll({type:"window",includeUncontrolled:true})).then(cs=>{cs.forEach(c=>c.postMessage({type:"inbox"}));
      return self.registration.showNotification("Ajouté à tes mots",{body:"« "+label+" » arrive dans ta prochaine session.",icon:"icon-192.png",badge:"icon-192.png",tag:"wotd"});}));return;}
  e.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(cs=>{for(const c of cs){if("focus" in c)return c.focus();}return self.clients.openWindow("./");}));});
