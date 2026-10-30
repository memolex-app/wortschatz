const V="memolex-1.1.1",SHELL=["./","index.html","manifest.webmanifest","icon-192.png","icon-512.png","lists-de-fr.json","examples-de-fr.json","chunks-de-fr.json","lists-it-fr.json","examples-it-fr.json","chunks-it-fr.json"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL.map(u=>new Request(u,{cache:"reload"})))));self.skipWaiting();});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))));self.clients.claim();});
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(e.request.method!=="GET"||u.hostname.endsWith(".supabase.co"))return;
  if(u.origin===location.origin&&!u.pathname.endsWith(".json")){ // l'appli : réseau d'abord, copie hors ligne sinon
    const key=e.request.mode==="navigate"?"index.html":e.request;
    e.respondWith(fetch(e.request,{cache:"no-cache"}).then(r=>{const cp=r.clone();if(r.ok)caches.open(V).then(c=>c.put(key,cp));return r;}).catch(()=>caches.match(key).then(r=>r||caches.match("index.html"))));return;}
  // listes, dictionnaire, polices : copie locale d'abord (renouvelée à chaque nouvelle version)
  e.respondWith(caches.open(V).then(c=>c.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r.ok)c.put(e.request,r.clone());return r;}))));});
