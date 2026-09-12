import os, io, json, time, urllib.parse, requests
from flask import Flask, request, jsonify, render_template_string, Response
from PIL import Image, ImageDraw
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
db = None
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    if not firebase_admin._apps:
        cred_json = os.environ.get('FIREBASE_CREDENTIALS')
        if cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        elif os.path.exists('serviceAccountKey.json'):
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            db = firestore.client()
except Exception as e:
    print("Firebase skip:", e)

cache_search = {}
cache_stream = {}
PIPED = ["https://pipedapi.kavin.rocks","https://api.piped.privacydev.net","https://pipedapi.moomoo.me"]

HTML = """<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>YODHA MUSIC</title><link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1DB954">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore-compat.js"></script>
</head><body class="bg-black text-white min-h-screen flex flex-col">
<div id="loginScreen" class="fixed inset-0 bg-black z-[9999] flex items-center justify-center p-4">
<div class="bg-[#181818] p-8 rounded-[24px] w-full max-w-[380px] text-center border border-[#333]">
<h1 class="text-[46px] tracking-[8px] text-[#1DB954]">YODHA</h1>
<input id="email" placeholder="EMAIL" class="w-full bg-[#222] border border-[#333] rounded-full px-5 py-3 mb-2 text-sm outline-none">
<input id="password" type="password" placeholder="PASSWORD" class="w-full bg-[#222] border border-[#333] rounded-full px-5 py-3 mb-4 text-sm outline-none">
<button onclick="loginEmail()" class="w-full bg-[#1DB954] text-black py-3 rounded-full font-black mb-2">LOGIN WITH EMAIL</button>
<button onclick="signupEmail()" class="w-full bg-[#2a2a2a] text-white py-3 rounded-full font-bold mb-2">CREATE ACCOUNT</button>
<button onclick="loginGoogle()" class="w-full bg-white text-black py-3 rounded-full font-bold">GOOGLE</button>
<p id="msg" class="text-red-500 text-[11px] mt-2"></p></div></div>
<header class="p-4 flex justify-between sticky top-0 bg-black border-b border-zinc-900"><h2 class="text-2xl font-black tracking-[6px] text-[#1DB954]">YODHA</h2><button onclick="logout()" class="bg-zinc-800 px-4 py-1.5 rounded-full text-xs">LOGOUT</button></header>
<div class="p-4 flex gap-2"><input id="q" placeholder="Search any song..." class="flex-1 bg-zinc-800 rounded-full px-5 py-3 text-sm outline-none" onkeypress="if(event.key=='Enter')doSearch()"><button onclick="doSearch()" class="bg-[#1DB954] text-black px-7 py-3 rounded-full font-black">GO</button></div>
<main class="flex-1 p-4 pb-[300px]"><div id="searchGrid" class="grid grid-cols-2 md:grid-cols-4 gap-3"></div><div id="homeGrid" class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6"></div><div id="lyricsBox" class="bg-zinc-900 p-4 rounded-xl text-sm mt-6 whitespace-pre-line max-h-[200px] overflow-auto">Lyrics will show here</div></main>
<footer class="fixed bottom-0 left-0 right-0 bg-[#181818] border-t border-zinc-800 p-4 rounded-t-[24px]"><div class="flex items-center gap-3"><img id="pImg" src="https://via.placeholder.com/60" class="w-14 h-14 rounded-lg"><div class="flex-1 truncate"><b id="pTitle" class="text-sm truncate block">No song</b><small id="pStatus" class="text-[10px] text-[#1DB954]"></small><div class="w-full h-1 bg-zinc-700 rounded-full mt-1"><div id="bar" class="h-full bg-[#1DB954] w-0"></div></div></div><button onclick="togglePlay()" id="playBtn" class="w-12 h-12 bg-white text-black rounded-full font-black">PLAY</button></div><audio id="audio"></audio></footer>
<script>
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js');}
const firebaseConfig = {apiKey:"AIzaSyArZJxJ6N4YHh8-0fbyH8c-MQ1V3jzbP9k",authDomain:"python-music-app-67.firebaseapp.com",projectId:"python-music-app-67",storageBucket:"python-music-app-67.firebasestorage.app",messagingSenderId:"868162538798",appId:"1:868162538798:web:a83ad67487d493d44cbebf",measurementId:"G-9EZFG6NZ3D"};
firebase.initializeApp(firebaseConfig); const auth=firebase.auth(); const fdb=firebase.firestore();
let list=[], idx=0; const audio=document.getElementById('audio');
const TRENDING=[{url:"https://www.youtube.com/watch?v=TO-_3tck2tg",title:"BONES",thumb:"https://i.ytimg.com/vi/TO-_3tck2tg/hqdefault.jpg",channel:"Imagine Dragons"},{url:"https://www.youtube.com/watch?v=7wtfhZwyrcc",title:"BELIEVER",thumb:"https://i.ytimg.com/vi/7wtfhZwyrcc/hqdefault.jpg",channel:"Imagine Dragons"},{url:"https://www.youtube.com/watch?v=60ItHLz5WEA",title:"FADED",thumb:"https://i.ytimg.com/vi/60ItHLz5WEA/hqdefault.jpg",channel:"Alan Walker"}];
auth.onAuthStateChanged(u=>{if(u){loginScreen.style.display='none'; showHome();}else{loginScreen.style.display='flex';}});
function showHome(){homeGrid.innerHTML=TRENDING.map((s,i)=>`<div onclick="playTrending(${i})" class="bg-zinc-900 p-3 rounded-xl cursor-pointer"><img src="${s.thumb}" class="w-full aspect-square rounded-lg"><b class="text-xs mt-2 block truncate">${s.title}</b></div>`).join('');}
async function loginEmail(){try{await auth.signInWithEmailAndPassword(email.value,password.value);}catch(e){msg.innerText=e.message;}}
async function signupEmail(){try{await auth.createUserWithEmailAndPassword(email.value,password.value);}catch(e){msg.innerText=e.message;}}
async function loginGoogle(){try{await auth.signInWithPopup(new firebase.auth.GoogleAuthProvider());}catch(e){msg.innerText=e.message;}}
function logout(){auth.signOut();}
async function doSearch(){let v=q.value.trim(); if(!v) return; searchGrid.innerHTML='Searching...'; let r=await fetch('/search?q='+encodeURIComponent(v)); let songs=await r.json(); list=songs; searchGrid.innerHTML=songs.map((s,i)=>`<div onclick="playAt(${i})" class="bg-zinc-900 p-3 rounded-xl cursor-pointer"><img src="${s.thumbnail}" class="w-full aspect-square rounded-lg"><b class="text-xs mt-2 block truncate">${s.title}</b></div>`).join('');}
function playTrending(i){list=TRENDING.map(x=>({url:x.url,title:x.title,thumbnail:x.thumb,channel:x.channel})); idx=i; play(list[i]);}
function playAt(i){idx=i; play(list[i]);}
async function play(song){pImg.src=song.thumbnail; pTitle.innerText=song.title; pStatus.innerText='LOADING...'; playBtn.innerText='...'; try{let r=await fetch('/stream?url='+encodeURIComponent(song.url)); let d=await r.json(); audio.src=d.url; await audio.play(); pStatus.innerText='PLAYING YODHA'; playBtn.innerText='PAUSE'; loadLyrics(song.title);}catch(e){pStatus.innerText='FAILED'; playBtn.innerText='PLAY';}}
async function loadLyrics(t){lyricsBox.innerText='Loading lyrics...'; try{let r=await fetch('/lyrics?title='+encodeURIComponent(t)); let d=await r.json(); lyricsBox.innerText=d.lyrics;}catch(e){lyricsBox.innerText='Not found';}}
function togglePlay(){if(audio.paused){audio.play(); playBtn.innerText='PAUSE';}else{audio.pause(); playBtn.innerText='PLAY';}}
audio.ontimeupdate=()=>{if(audio.duration) bar.style.width=(audio.currentTime/audio.duration*100)+'%';}
</script></body></html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/manifest.json")
def manifest():
    return jsonify({"name":"YODHA","short_name":"YODHA","start_url":"/","display":"standalone","background_color":"#000000","theme_color":"#1DB954","icons":[{"src":"/icon-192","sizes":"192x192","type":"image/png"},{"src":"/icon-512","sizes":"512x512","type":"image/png"}]})

@app.route("/sw.js")
def sw():
    return Response("const C='YODHA-V7';self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(['/'])))});self.addEventListener('fetch',e=>{if(e.request.url.includes('/search')||e.request.url.includes('/stream'))return fetch(e.request); e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));});", mimetype="application/javascript")

@app.route("/icon-<int:size>")
def icon(size):
    if size not in [192,512]: size=192
    img = Image.new("RGB", (size,size), "#000000")
    draw = ImageDraw.Draw(img)
    draw.ellipse([size*0.08,size*0.08,size*0.92,size*0.92], fill="#1DB954")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")

@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    if not q: return jsonify([])
    ql = q.lower()
    if ql in cache_search: return jsonify(cache_search[ql])
    for server in PIPED:
        try:
            r = requests.get(server+"/search?q="+urllib.parse.quote(q)+"&filter=music_songs", timeout=4, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code==200:
                out=[]
                for it in r.json().get("items",[])[:12]:
                    u=it.get("url","")
                    vid=u.split("v=")[-1].split("&")[0] if "v=" in u else u.split("/")[-1].split("?")[0]
                    if len(vid)<6: continue
                    thumb=it.get("thumbnail") or "https://i.ytimg.com/vi/"+vid+"/hqdefault.jpg"
                    out.append({"url":"https://www.youtube.com/watch?v="+vid,"title":it.get("title","Unknown"),"thumbnail":thumb,"channel":it.get("uploaderName","YouTube")})
                if out:
                    cache_search[ql]=out
                    return jsonify(out)
        except Exception:
            continue
    return jsonify([])

@app.route("/stream")
def stream():
    url=request.args.get("url","")
    vid=url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1].split("?")[0]
    if not vid: return jsonify({"error":"no vid"}),400
    if vid in cache_stream and time.time()-cache_stream[vid]["t"]<1800:
        return jsonify({"url":cache_stream[vid]["url"]})
    for server in PIPED:
        try:
            r=requests.get(server+"/streams/"+vid, timeout=4, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code==200:
                j=r.json()
                aud=j.get("audioStreams",[])
                if aud:
                    best=sorted(aud, key=lambda x:x.get("bitrate",0), reverse=True)[0]
                    if best.get("url"):
                        cache_stream[vid]={"url":best["url"],"t":time.time()}
                        return jsonify({"url":best["url"]})
                if j.get("hls"):
                    cache_stream[vid]={"url":j["hls"],"t":time.time()}
                    return jsonify({"url":j["hls"]})
        except Exception:
            continue
    return jsonify({"error":"busy"}),500

@app.route("/lyrics")
def lyrics():
    title=request.args.get("title","")
    try:
        r=requests.get("https://lrclib.net/api/search?track_name="+urllib.parse.quote(title), timeout=5)
        d=r.json()
        if d and len(d)>0 and d[0].get("plainLyrics"):
            return jsonify({"lyrics":d[0]["plainLyrics"][:8000]})
    except Exception:
        pass
    return jsonify({"lyrics":"Lyrics not found for "+title})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
