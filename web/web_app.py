"""Panel web du bot : connexion Discord OAuth2, réservé aux administrateurs.

Affiche des graphiques (évolution du nombre de serveurs, membres par serveur,
utilisation par serveur). L'accès est réservé :
  - aux owners du bot (voient toutes les données) ;
  - aux administrateurs d'un serveur où le bot est présent (voient les données
    des serveurs qu'ils administrent).
"""
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import aiohttp
import discord
from aiohttp import web

from utils import checks
import config
from web import logbuffer
from web import prefs
from web import stats

DISCORD_API = "https://discord.com/api"
ADMINISTRATOR = 0x8

# Sessions en mémoire : token -> {"user": {...}, "guild_ids": set|"all"}.
_sessions: dict[str, dict] = {}


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
def _get_session(request: web.Request) -> dict | None:
    token = request.cookies.get("session")
    return _sessions.get(token) if token else None


def _is_secure(request: web.Request) -> bool:
    """True si la requête est servie en HTTPS (directement ou via un proxy)."""
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    return proto == "https"


def _set_session(response: web.Response, data: dict, *, secure: bool) -> None:
    token = secrets.token_urlsafe(32)
    _sessions[token] = data
    response.set_cookie(
        "session", token, httponly=True, samesite="Lax", max_age=86400,
        secure=secure,
    )


# --------------------------------------------------------------------------- #
# OAuth
# --------------------------------------------------------------------------- #
def _authorize_url(state: str) -> str:
    params = {
        "client_id": config.OAUTH_CLIENT_ID,
        "redirect_uri": config.OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
    }
    return f"{DISCORD_API}/oauth2/authorize?{urlencode(params)}"


async def _exchange_code(code: str) -> str | None:
    data = {
        "client_id": config.OAUTH_CLIENT_ID,
        "client_secret": config.OAUTH_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.OAUTH_REDIRECT_URI,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{DISCORD_API}/oauth2/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if resp.status != 200:
                return None
            return (await resp.json()).get("access_token")


async def _fetch(access_token: str, path: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DISCORD_API}{path}", headers=headers) as resp:
            if resp.status != 200:
                return None
            return await resp.json()


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
def build_app(bot) -> web.Application:
    app = web.Application()

    async def login(request: web.Request) -> web.Response:
        # Paramètre `state` anti-CSRF : posé en cookie, revérifié au callback.
        state = secrets.token_urlsafe(24)
        response = web.HTTPFound(_authorize_url(state))
        response.set_cookie(
            "oauth_state", state, httponly=True, samesite="Lax",
            max_age=600, secure=_is_secure(request),
        )
        return response

    async def logout(request: web.Request) -> web.Response:
        token = request.cookies.get("session")
        _sessions.pop(token, None)
        response = web.HTTPFound("/")
        response.del_cookie("session")
        return response

    async def callback(request: web.Request) -> web.Response:
        # Vérifie le `state` OAuth (protection contre le login CSRF).
        state = request.query.get("state")
        expected = request.cookies.get("oauth_state")
        if not state or not expected or not secrets.compare_digest(
            state, expected
        ):
            return web.Response(text="État OAuth invalide.", status=400)

        code = request.query.get("code")
        if not code:
            raise web.HTTPFound("/")
        access_token = await _exchange_code(code)
        if access_token is None:
            return web.Response(text="Échec de l'authentification.", status=401)

        user = await _fetch(access_token, "/users/@me")
        user_guilds = await _fetch(access_token, "/users/@me/guilds") or []
        if user is None:
            return web.Response(text="Échec de l'authentification.", status=401)

        # Owner du bot -> accès total.
        if checks.is_owner_id(int(user["id"])):
            return _redirect_home(request, user, "all")

        # Sinon : serveurs où l'utilisateur est admin ET où le bot est présent.
        bot_guild_ids = {g.id for g in bot.guilds}
        admin_guild_ids = {
            int(g["id"])
            for g in user_guilds
            if (int(g.get("permissions", 0)) & ADMINISTRATOR) == ADMINISTRATOR
            and int(g["id"]) in bot_guild_ids
        }
        if not admin_guild_ids:
            return web.Response(
                text="Accès refusé : vous devez être administrateur d'un "
                "serveur où le bot est présent.",
                status=403,
            )
        return _redirect_home(request, user, admin_guild_ids)

    def _redirect_home(request, user, guild_ids) -> web.Response:
        response = web.HTTPFound("/")
        _set_session(
            response,
            {"user": {"id": user["id"], "username": user.get("username")},
             "guild_ids": guild_ids,
             # Langue mémorisée pour ce compte (persistée côté serveur).
             "lang": prefs.get_lang(user["id"])},
            secure=_is_secure(request),
        )
        # Le `state` a servi : on retire son cookie.
        response.del_cookie("oauth_state")
        return response

    async def index(request: web.Request) -> web.Response:
        session = _get_session(request)
        if session is None:
            return web.Response(text=_LOGIN_HTML, content_type="text/html")
        return web.Response(text=_DASHBOARD_HTML, content_type="text/html")

    async def api_stats(request: web.Request) -> web.Response:
        session = _get_session(request)
        if session is None:
            return web.json_response({"error": "unauthorized"}, status=401)

        guild_ids = session["guild_ids"]
        is_owner = guild_ids == "all"

        if is_owner:
            allowed = [g.id for g in bot.guilds]
        else:
            allowed = list(guild_ids)

        guilds_data = []
        for gid in allowed:
            gs = stats.get_guild_stats(gid)
            if gs is not None:
                guilds_data.append({"id": str(gid), **gs})

        payload = {
            "is_owner": is_owner,
            "user": session["user"],
            "guilds": guilds_data,
            "lang": session.get("lang", "fr"),
        }
        if is_owner:
            payload["servers_history"] = stats.get_snapshots()
            total_members = sum((g.member_count or 0) for g in bot.guilds)
            total_usage = sum(
                sum(g["usage"][i]["count"] for i in range(len(g["usage"])))
                for g in guilds_data
            )
            uptime = (
                datetime.now(timezone.utc) - bot.start_time
            ).total_seconds()
            payload["analytics"] = {
                "guilds": len(bot.guilds),
                "members": total_members,
                "commands_total": total_usage,
                "latency_ms": round(bot.latency * 1000),
                "uptime_seconds": int(uptime),
                "presence": str(
                    bot.activity.name if bot.activity else ""
                ),
            }
        return web.json_response(payload)

    def _require_owner(request: web.Request) -> dict | None:
        session = _get_session(request)
        if session is None or session.get("guild_ids") != "all":
            return None
        return session

    async def control_presence(request: web.Request) -> web.Response:
        if _require_owner(request) is None:
            return web.json_response({"error": "forbidden"}, status=403)
        body = await request.json()
        text = (body.get("text") or "").strip()
        activity = discord.Game(name=text) if text else None
        await bot.change_presence(activity=activity)
        return web.json_response({"ok": True, "presence": text})

    async def control_reload(request: web.Request) -> web.Response:
        if _require_owner(request) is None:
            return web.json_response({"error": "forbidden"}, status=403)
        reloaded, failed = 0, 0
        for ext in list(bot.extensions):
            try:
                await bot.reload_extension(ext)
                reloaded += 1
            except Exception:  # noqa: BLE001
                failed += 1
        return web.json_response({"ok": True, "reloaded": reloaded, "failed": failed})

    async def api_logs(request: web.Request) -> web.Response:
        # Console en direct : réservée aux owners.
        if _require_owner(request) is None:
            return web.json_response({"error": "forbidden"}, status=403)
        after = request.query.get("after", "0")
        after = int(after) if after.isdigit() else 0
        lines = logbuffer.get_since(after)
        last = lines[-1]["id"] if lines else after
        return web.json_response({"lines": lines, "last": last})

    async def set_lang(request: web.Request) -> web.Response:
        # Enregistre la langue pour le compte connecté (persistée côté serveur).
        session = _get_session(request)
        if session is None:
            return web.json_response({"error": "unauthorized"}, status=401)
        body = await request.json()
        lang = (body.get("lang") or "").lower()
        if lang not in prefs.LANGS:
            return web.json_response({"error": "invalid"}, status=400)
        prefs.set_lang(session["user"]["id"], lang)
        session["lang"] = lang
        return web.json_response({"ok": True, "lang": lang})

    async def privacy(_request: web.Request) -> web.Response:
        return web.Response(text=_PRIVACY_HTML, content_type="text/html")

    async def terms(_request: web.Request) -> web.Response:
        return web.Response(text=_TERMS_HTML, content_type="text/html")

    app.router.add_get("/", index)
    app.router.add_get("/login", login)
    app.router.add_get("/logout", logout)
    app.router.add_get("/callback", callback)
    app.router.add_get("/api/stats", api_stats)
    app.router.add_post("/api/control/presence", control_presence)
    app.router.add_post("/api/control/reload", control_reload)
    app.router.add_post("/api/lang", set_lang)
    app.router.add_get("/api/logs", api_logs)
    # Pages publiques (accessibles sans connexion).
    app.router.add_get("/privacy", privacy)
    app.router.add_get("/confidentialite", privacy)
    app.router.add_get("/terms", terms)
    app.router.add_get("/conditions", terms)
    return app


# --------------------------------------------------------------------------- #
# Pages HTML
# --------------------------------------------------------------------------- #
_NEON_CSS = """
 :root{--bg:#0a0a12;--card:#12121f;--cyan:#00eaff;--magenta:#ff2bd6;
   --purple:#9d4bff;--text:#e6e6ff}
 *{box-sizing:border-box}
 body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);
   margin:0;padding:0}
 h1,h2{font-weight:700}
 h1{color:var(--cyan);text-shadow:0 0 8px var(--cyan),0 0 20px rgba(0,234,255,.5)}
 h2{color:var(--magenta);text-shadow:0 0 6px rgba(255,43,214,.6)}
 a{color:var(--cyan)}
 .card{background:var(--card);border:1px solid rgba(157,75,255,.35);
   border-radius:14px;padding:20px;margin:16px 0;
   box-shadow:0 0 18px rgba(157,75,255,.25)}
 .btn{display:inline-block;background:transparent;color:var(--cyan);
   border:1px solid var(--cyan);padding:10px 20px;border-radius:8px;
   text-decoration:none;font-weight:600;cursor:pointer;
   box-shadow:0 0 12px rgba(0,234,255,.4);transition:.2s}
 .btn:hover{background:var(--cyan);color:#0a0a12;box-shadow:0 0 22px var(--cyan)}
 input{background:#0a0a12;border:1px solid var(--purple);color:var(--text);
   padding:9px 12px;border-radius:8px;outline:none}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
   gap:14px}
 .stat{background:linear-gradient(145deg,#12121f,#181830);border-radius:12px;
   padding:16px;border:1px solid rgba(0,234,255,.3);
   box-shadow:0 0 14px rgba(0,234,255,.15)}
 .stat .n{font-size:1.8em;font-weight:800;color:var(--cyan);
   text-shadow:0 0 10px rgba(0,234,255,.6)}
 .stat .l{opacity:.7;font-size:.85em}
 #cookie-banner{position:fixed;inset:0;display:none;z-index:999;
   align-items:center;justify-content:center;
   background:rgba(5,5,12,.82);backdrop-filter:blur(4px)}
 #cookie-banner.show{display:flex}
 #cookie-card{background:linear-gradient(160deg,#15152a,#0d0d1a);
   border:2px solid var(--magenta);border-radius:18px;padding:34px;
   max-width:460px;margin:20px;text-align:center;
   box-shadow:0 0 40px rgba(255,43,214,.55),0 0 90px rgba(157,75,255,.4);
   animation:cookiepop .3s ease}
 @keyframes cookiepop{from{transform:scale(.9);opacity:0}
   to{transform:scale(1);opacity:1}}
 #cookie-card .ico{font-size:2.6em;line-height:1}
 #cookie-card h2{margin:.4em 0 .3em}
 #cookie-card p{opacity:.85;font-size:.95em;margin:0 0 22px}
 #cookie-card .row{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
 .btn.decline{color:var(--magenta);border-color:var(--magenta);
   box-shadow:0 0 12px rgba(255,43,214,.4)}
 .btn.decline:hover{background:var(--magenta);color:#0a0a12;
   box-shadow:0 0 22px var(--magenta)}
 .gated{opacity:.35;pointer-events:none;filter:grayscale(.6)}
"""

# Consentement cookies + gestion de la langue sur les pages publiques.
# La persistance de la langue (localStorage) n'a lieu qu'avec le consentement.
_CONSENT_JS = """
function getConsent(){return localStorage.getItem('cookieConsent');}
function persistLang(l){if(getConsent()==='yes')localStorage.setItem('lang',l);}
function startLang(){return getConsent()==='yes'?
 (localStorage.getItem('lang')||'fr'):'fr';}
var _lang=startLang();
function getLang(){return _lang;}
function toggleLang(){applyLang(getLang()==='fr'?'en':'fr');}
function setGate(on){document.querySelectorAll('.gate-consent').forEach(
 function(e){if(on){e.classList.add('gated');e.setAttribute('aria-disabled','true');}
 else{e.classList.remove('gated');e.removeAttribute('aria-disabled');}});}
function cookieChoice(v){localStorage.setItem('cookieConsent',v);
 if(v==='no'){localStorage.removeItem('lang');}else{persistLang(_lang);}
 var bn=document.getElementById('cookie-banner');if(bn)bn.classList.remove('show');
 setGate(false);}
function initConsent(){if(getConsent()===null){
 var bn=document.getElementById('cookie-banner');if(bn)bn.classList.add('show');
 setGate(true);}else{setGate(false);}}
// Bloque toute action verrouillée tant que le choix n'est pas fait.
document.addEventListener('click',function(ev){
 var el=ev.target.closest?ev.target.closest('.gate-consent'):null;
 if(el&&el.classList.contains('gated')){ev.preventDefault();ev.stopPropagation();}
},true);
"""

# Modale de consentement (bilingue, bloquante), masquée par défaut.
_COOKIE_BANNER = """
 <div id="cookie-banner">
  <div id="cookie-card">
   <div class="ico">🍪</div>
   <h2 data-fr="Cookies & confidentialité" data-en="Cookies & privacy"></h2>
   <p data-fr="Ce site peut mémoriser votre langue dans votre navigateur. Choisissez avant de continuer : votre choix est nécessaire pour vous connecter."
      data-en="This site can store your language in your browser. Please choose before continuing: your choice is required to log in."></p>
   <div class="row">
    <button class="btn" onclick="cookieChoice('yes')"
     data-fr="Accepter" data-en="Accept"></button>
    <button class="btn decline" onclick="cookieChoice('no')"
     data-fr="Refuser" data-en="Decline"></button>
   </div>
  </div>
 </div>"""

_LOGIN_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>Watcher — Panel</title>
<style>""" + _NEON_CSS + """
 body{display:flex;height:100vh;align-items:center;justify-content:center}
 .card{padding:44px;text-align:center;max-width:420px;position:relative}
 #lang{position:absolute;top:16px;right:16px}
</style></head>
<body><div class="card">
 <button class="btn" id="lang" onclick="toggleLang()">English</button>
 <h1>▚ Watcher ▞</h1>
 <p data-fr="Panneau d'administration. Connecte-toi avec Discord pour accéder aux statistiques et au contrôle du bot."
    data-en="Admin panel. Log in with Discord to access the bot's statistics and controls."></p>
 <a class="btn gate-consent" href="/login" data-fr="Se connecter avec Discord"
    data-en="Log in with Discord"></a>
 <p style="margin-top:26px;font-size:.85em;opacity:.75">
   <a href="/privacy" data-fr="Politique de confidentialité"
      data-en="Privacy Policy"></a> ·
   <a href="/terms" data-fr="Conditions d'utilisation"
      data-en="Terms of Service"></a></p>
</div>""" + _COOKIE_BANNER + """
<script>""" + _CONSENT_JS + """
function applyLang(l){_lang=l;document.documentElement.lang=l;persistLang(l);
 document.querySelectorAll('[data-fr]').forEach(function(e){
   e.textContent=e.getAttribute('data-'+l);});
 var b=document.getElementById('lang');if(b)b.textContent=(l==='fr'?'English':'Français');}
applyLang(_lang);initConsent();
</script>
</body></html>"""

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>Watcher — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>""" + _NEON_CSS + """
 body{padding:24px;max-width:1100px;margin:auto}
 header{display:flex;justify-content:space-between;align-items:center;
   border-bottom:1px solid rgba(157,75,255,.3);padding-bottom:12px}
 canvas{max-height:320px}
 .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
 nav.tabs{display:flex;gap:8px;margin:16px 0;flex-wrap:wrap}
 nav.tabs .btn.active{background:var(--cyan);color:#0a0a12;
   box-shadow:0 0 18px var(--cyan)}
 select{background:#0a0a12;border:1px solid var(--purple);color:var(--text);
   padding:8px 10px;border-radius:8px}
 #console{background:#07070d;border:1px solid rgba(0,234,255,.25);
   border-radius:10px;padding:12px;height:62vh;overflow:auto;
   font-family:ui-monospace,Menlo,monospace;font-size:.82em;
   white-space:pre-wrap;line-height:1.45}
 .lg-INFO{color:#c8c8e6}.lg-WARNING{color:#f5ff3d}
 .lg-ERROR,.lg-CRITICAL{color:#ff6b6b}.lg-DEBUG{color:#7fb0b0}
 .lg-t{color:#66d9ff}.lg-lvl{opacity:.7}
</style></head>
<body>
 <header><h1>▚ Watcher ▞</h1>
   <span class="row"><span id="who"></span>
   <button class="btn" id="lang" onclick="toggleLang()">English</button>
   <a class="btn" href="/logout" id="logout"></a></span></header>
 <nav class="tabs" id="tabs" style="display:none"></nav>
 <div id="content"></div>
<script>
const T={fr:{lang:'English',logout:'Déconnexion',analytics:'Analytics',
 servers:'Serveurs',members:'Membres',commands:'Commandes',ping:'Ping',
 uptime:'Uptime',control:'Contrôle du bot',statusPh:'Statut (ex: §help)',
 setStatus:'Définir le statut',reloadCogs:'Recharger les cogs',
 statusOk:'✅ Statut mis à jour',cogsOk:'cogs rechargés',err:'❌ Erreur',
 serversEvo:'Évolution du nombre de serveurs',serversLbl:'Serveurs',
 membersTotal:'Membres (total)',membersLbl:'Membres',membersEvo:'Évolution des membres',
 cmdUsed:'Commandes utilisées',cmdPerDay:'Commandes par jour',
 noData:'Aucune donnée disponible pour le moment.',
 expired:'Session expirée.',reconnect:'Se reconnecter',
 tGeneral:'Général',tAnalytics:'Analytics',tLive:'Live',
 selServer:'Serveur :',selAll:'Général (tous les serveurs)',
 liveTitle:'Console en direct',liveClear:'Effacer',liveAuto:'Défilement auto'},
 en:{lang:'Français',logout:'Log out',analytics:'Analytics',servers:'Servers',
 members:'Members',commands:'Commands',ping:'Ping',uptime:'Uptime',
 control:'Bot control',statusPh:'Status (e.g. §help)',setStatus:'Set status',
 reloadCogs:'Reload cogs',statusOk:'✅ Status updated',cogsOk:'cogs reloaded',
 err:'❌ Error',serversEvo:'Server count over time',serversLbl:'Servers',
 membersTotal:'Members (total)',membersLbl:'Members',membersEvo:'Members over time',
 cmdUsed:'Commands used',cmdPerDay:'Commands per day',
 noData:'No data available yet.',expired:'Session expired.',
 reconnect:'Log in again',tGeneral:'General',tAnalytics:'Analytics',tLive:'Live',
 selServer:'Server:',selAll:'General (all servers)',
 liveTitle:'Live console',liveClear:'Clear',liveAuto:'Auto-scroll'}};
let CUR='fr';let L=T[CUR];let DATA=null;let charts=[];let liveTimer=null;let liveLast=0;
function applyHeader(){document.documentElement.lang=CUR;L=T[CUR];
 document.getElementById('lang').textContent=L.lang;
 document.getElementById('logout').textContent=L.logout;}
applyHeader();
function toggleLang(){const nl=CUR==='fr'?'en':'fr';
 post('/api/lang',{lang:nl}).then(function(){location.reload();});}
function fmtUptime(s){const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),
 m=Math.floor(s%3600/60);const u=CUR==='fr'?'j':'d';
 return (d?d+u+' ':'')+(h?h+'h ':'')+m+'m';}
function tsLabels(p){return p.map(x=>new Date(x.ts*1000).toLocaleString());}
const NEON={cyan:'#00eaff',magenta:'#ff2bd6',purple:'#9d4bff',
 green:'#39ff14',yellow:'#f5ff3d'};
Chart.defaults.color='#c8c8e6';Chart.defaults.borderColor='rgba(157,75,255,.15)';
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function card(html){const c=document.createElement('div');c.className='card';
 c.innerHTML=html;document.getElementById('content').appendChild(c);return c;}
function chart(el,cfg){const c=new Chart(el,cfg);charts.push(c);return c;}
async function post(url,body){const r=await fetch(url,{method:'POST',
 headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
 return r.json();}
function clearPage(){
 if(liveTimer){clearInterval(liveTimer);liveTimer=null;}
 charts.forEach(function(c){c.destroy();});charts=[];
 document.getElementById('content').innerHTML='';}

// ---- Page Général ----
function renderGeneral(){const a=DATA.analytics;
 if(a){card('<h2>'+L.analytics+'</h2><div class="grid">'+
   '<div class="stat"><div class="n">'+a.guilds+'</div><div class="l">'+L.servers+'</div></div>'+
   '<div class="stat"><div class="n">'+a.members+'</div><div class="l">'+L.members+'</div></div>'+
   '<div class="stat"><div class="n">'+a.commands_total+'</div><div class="l">'+L.commands+'</div></div>'+
   '<div class="stat"><div class="n">'+a.latency_ms+'<span style="font-size:.5em">ms</span></div><div class="l">'+L.ping+'</div></div>'+
   '<div class="stat"><div class="n">'+fmtUptime(a.uptime_seconds)+'</div><div class="l">'+L.uptime+'</div></div>'+
   '</div>');
  const cc=card('<h2>'+L.control+'</h2><div class="row">'+
   '<input id="pres" placeholder="'+L.statusPh+'" value="'+(a.presence||'')+'">'+
   '<button class="btn" id="setpres">'+L.setStatus+'</button>'+
   '<button class="btn" id="reload">'+L.reloadCogs+'</button>'+
   '<span id="ctlmsg"></span></div>');
  cc.querySelector('#setpres').onclick=async()=>{
    const j=await post('/api/control/presence',{text:cc.querySelector('#pres').value});
    cc.querySelector('#ctlmsg').textContent=j.ok?L.statusOk:L.err;};
  cc.querySelector('#reload').onclick=async()=>{
    const j=await post('/api/control/reload');
    cc.querySelector('#ctlmsg').textContent=j.ok?('✅ '+j.reloaded+' '+L.cogsOk):L.err;};
 }
 if(DATA.servers_history){
   card('<h2>'+L.serversEvo+'</h2><canvas id="sv"></canvas>');
   chart(document.getElementById('sv'),{type:'line',data:{
     labels:tsLabels(DATA.servers_history),datasets:[
      {label:L.serversLbl,data:DATA.servers_history.map(p=>p.guilds),
       borderColor:NEON.cyan,backgroundColor:'rgba(0,234,255,.1)',fill:true,tension:.25},
      {label:L.membersTotal,data:DATA.servers_history.map(p=>p.members),
       borderColor:NEON.magenta,tension:.25,yAxisID:'y1'}]},
     options:{scales:{y1:{position:'right'}}}});
 }}

// ---- Page Analytics (sélecteur de serveur) ----
function aggregateUsage(){const m={};DATA.guilds.forEach(function(g){
  g.usage.forEach(function(p){m[p.date]=(m[p.date]||0)+p.count;});});
 return Object.keys(m).sort().map(function(k){return {date:k,count:m[k]};});}
function renderAnalytics(sel){
 let opts='<option value="all">'+L.selAll+'</option>';
 DATA.guilds.forEach(function(g){opts+='<option value="'+g.id+'"'+
   (sel===g.id?' selected':'')+'>'+esc(g.name)+'</option>';});
 const head=card('<h2>'+L.analytics+'</h2><div class="row">'+
   '<label>'+L.selServer+'</label><select id="srv">'+opts+'</select></div>');
 head.querySelector('#srv').onchange=function(e){
   // On ne recrée que la partie graphiques.
   clearPage();renderTabs();renderAnalytics(e.target.value);};
 if(sel==='all'){
   if(DATA.servers_history){
     card('<h2>'+L.membersEvo+' — '+L.selAll+'</h2><canvas id="am"></canvas>');
     chart(document.getElementById('am'),{type:'line',data:{
       labels:tsLabels(DATA.servers_history),datasets:[{label:L.membersTotal,
         data:DATA.servers_history.map(p=>p.members),borderColor:NEON.magenta,
         backgroundColor:'rgba(255,43,214,.1)',fill:true,tension:.25}]}});
   }
   const agg=aggregateUsage();
   card('<h2>'+L.cmdPerDay+' — '+L.selAll+'</h2><canvas id="au"></canvas>');
   chart(document.getElementById('au'),{type:'bar',data:{labels:agg.map(p=>p.date),
     datasets:[{label:L.cmdUsed,data:agg.map(p=>p.count),backgroundColor:NEON.purple}]}});
 }else{
   const g=DATA.guilds.find(function(x){return x.id===sel;});
   if(!g){card('<p>'+L.noData+'</p>');return;}
   card('<h2>'+L.membersEvo+' — '+esc(g.name)+'</h2><canvas id="gm"></canvas>');
   chart(document.getElementById('gm'),{type:'line',data:{labels:tsLabels(g.members),
     datasets:[{label:L.membersLbl,data:g.members.map(p=>p.count),borderColor:NEON.green,
       backgroundColor:'rgba(57,255,20,.1)',fill:true,tension:.25}]}});
   card('<h2>'+L.cmdPerDay+' — '+esc(g.name)+'</h2><canvas id="gu"></canvas>');
   chart(document.getElementById('gu'),{type:'bar',data:{labels:g.usage.map(p=>p.date),
     datasets:[{label:L.cmdUsed,data:g.usage.map(p=>p.count),backgroundColor:NEON.purple}]}});
 }}

// ---- Page Live (console) ----
function pad(n){return (n<10?'0':'')+n;}
function renderLive(){
 const c=card('<h2>'+L.liveTitle+'</h2><div class="row" style="margin-bottom:8px">'+
   '<button class="btn" id="clr">'+L.liveClear+'</button>'+
   '<label><input type="checkbox" id="auto" checked> '+L.liveAuto+'</label></div>'+
   '<div id="console"></div>');
 const box=c.querySelector('#console');
 c.querySelector('#clr').onclick=function(){box.innerHTML='';};
 liveLast=0;
 async function poll(){
   const r=await fetch('/api/logs?after='+liveLast);
   if(!r.ok)return;const j=await r.json();liveLast=j.last;
   j.lines.forEach(function(ln){const dt=new Date(ln.ts*1000);
     const ts=pad(dt.getHours())+':'+pad(dt.getMinutes())+':'+pad(dt.getSeconds());
     const div=document.createElement('div');div.className='lg-'+ln.level;
     div.innerHTML='<span class="lg-t">'+ts+'</span> <span class="lg-lvl">['+
       ln.level+']</span> '+ln.msg.replace(/</g,'&lt;');
     box.appendChild(div);});
   if(j.lines.length && c.querySelector('#auto').checked){box.scrollTop=box.scrollHeight;}}
 poll();liveTimer=setInterval(poll,2000);}

const PAGES={general:renderGeneral,analytics:function(){renderAnalytics('all');},
 live:renderLive};
let ACTIVE='general';
function renderTabs(){const tabs=document.getElementById('tabs');tabs.style.display='flex';
 const defs=[['general',L.tGeneral],['analytics',L.tAnalytics],['live',L.tLive]];
 tabs.innerHTML='';defs.forEach(function(d){const b=document.createElement('button');
   b.className='btn'+(ACTIVE===d[0]?' active':'');b.textContent=d[1];
   b.onclick=function(){show(d[0]);};tabs.appendChild(b);});}
function show(page){ACTIVE=page;clearPage();renderTabs();PAGES[page]();}

async function load(){
 const r=await fetch('/api/stats');
 if(!r.ok){document.getElementById('content').innerHTML=
   '<p>'+L.expired+' <a href="/login">'+L.reconnect+'</a></p>';return;}
 DATA=await r.json();CUR=DATA.lang||'fr';applyHeader();
 document.getElementById('who').textContent='@'+(DATA.user.username||'');
 if(DATA.is_owner){show('general');}
 else{
   // Vue administrateur : cartes par serveur qu'il administre.
   if(DATA.guilds.length===0){card('<p>'+L.noData+'</p>');return;}
   DATA.guilds.forEach(function(g,i){
     card('<h2>'+esc(g.name)+'</h2><canvas id="m'+i+'"></canvas><canvas id="u'+i+'"></canvas>');
     chart(document.getElementById('m'+i),{type:'line',data:{labels:tsLabels(g.members),
       datasets:[{label:L.membersLbl,data:g.members.map(p=>p.count),borderColor:NEON.green,
         backgroundColor:'rgba(57,255,20,.1)',fill:true,tension:.25}]}});
     chart(document.getElementById('u'+i),{type:'bar',data:{labels:g.usage.map(p=>p.date),
       datasets:[{label:L.cmdUsed,data:g.usage.map(p=>p.count),backgroundColor:NEON.purple}]}});
   });
 }}
load();
</script>
</body></html>"""


# --------------------------------------------------------------------------- #
# Pages légales publiques
# --------------------------------------------------------------------------- #
def _legal_page(title: str, fr_body: str, en_body: str) -> str:
    return (
        "<!DOCTYPE html><html lang=\"fr\"><head><meta charset=\"utf-8\">"
        f"<title>Watcher — {title}</title><style>" + _NEON_CSS + """
 body{max-width:820px;margin:auto;padding:32px 24px;line-height:1.6}
 h1{margin-bottom:4px}
 h2{margin-top:28px}
 .card{padding:28px;position:relative}
 #lang{position:absolute;top:20px;right:20px}
 footer{margin-top:30px;font-size:.85em;opacity:.7;text-align:center}
</style></head><body><div class="card">
 <button class="btn" id="lang" onclick="toggleLang()">English</button>
 <div id="fr">""" + fr_body + """</div>
 <div id="en" style="display:none">""" + en_body + """</div>
 <footer><a href="/">Accueil / Home</a> ·
 <a href="/privacy">Confidentialité / Privacy</a> ·
 <a href="/terms">Conditions / Terms</a></footer>
</div>""" + _COOKIE_BANNER + """
<script>""" + _CONSENT_JS + """
function applyLang(l){_lang=l;document.documentElement.lang=l;persistLang(l);
 document.getElementById('fr').style.display=(l==='fr'?'':'none');
 document.getElementById('en').style.display=(l==='en'?'':'none');
 document.getElementById('lang').textContent=(l==='fr'?'English':'Français');}
applyLang(_lang);initConsent();
</script>
</body></html>"""
    )


_PRIVACY_BODY = """
 <h1>Politique de confidentialité</h1>
 <p><em>Dernière mise à jour : 2026.</em></p>
 <p>Cette politique décrit les données traitées par le bot Discord
 « Watcher » (« le Bot ») et la façon dont elles sont utilisées.</p>

 <h2>1. Données collectées</h2>
 <p>Le Bot peut enregistrer, selon les fonctionnalités activées par les
 administrateurs d'un serveur :</p>
 <ul>
   <li><strong>Identifiants Discord</strong> (utilisateurs, serveurs, salons,
   rôles) nécessaires au fonctionnement des commandes ;</li>
   <li><strong>Données de modération</strong> : avertissements, mutes,
   confinements et historique des sanctions ;</li>
   <li><strong>Statistiques agrégées</strong> : nombre de messages, arrivées
   et départs, nombre de membres (pour les graphiques d'activité) ;</li>
   <li><strong>Réglages de serveur</strong> (protections activées) ;</li>
   <li><strong>Rappels</strong> que vous programmez ;</li>
   <li>Lorsqu'un administrateur active la <strong>surveillance</strong> d'un
   utilisateur, le contenu de ses messages, réactions, changements de pseudo
   et statut, et son activité vocale sont recopiés dans un salon privé du
   serveur concerné.</li>
 </ul>
 <p>Le Bot n'accède au contenu des messages que dans le cadre des
 fonctionnalités d'automodération et de surveillance décrites ci-dessus.</p>

 <h2>2. Connexion au panel web</h2>
 <p>Le panel d'administration utilise l'authentification Discord (OAuth2). Le
 Bot lit alors votre identifiant, votre nom d'utilisateur et la liste de vos
 serveurs afin de vérifier vos droits d'accès. Aucune de ces informations
 n'est revendue ni transmise à des tiers.</p>
 <p>Un cookie de session strictement nécessaire est utilisé pour vous garder
 connecté. Une fois connecté, votre <strong>choix de langue est mémorisé côté
 serveur, rattaché à votre compte</strong>. Sur les pages publiques, la
 mémorisation de la langue dans votre navigateur (stockage local) n'a lieu
 qu'avec votre <strong>consentement</strong>.</p>

 <h2>3. Finalités</h2>
 <p>Les données servent uniquement au fonctionnement du Bot (modération,
 statistiques, rappels) et ne sont pas utilisées à des fins publicitaires.</p>

 <h2>4. Conservation</h2>
 <p>Les données sont conservées tant qu'elles sont nécessaires au service. Les
 statistiques d'activité sont automatiquement purgées au-delà de 60 jours. Un
 administrateur peut supprimer les données liées à une fonctionnalité en la
 désactivant (par exemple <code>unwatch</code>, <code>unwarn</code>).</p>

 <h2>5. Partage</h2>
 <p>Les données ne sont pas partagées avec des tiers. Elles restent stockées
 par l'hébergeur du Bot et, pour la surveillance, dans le serveur Discord
 concerné.</p>

 <h2>6. Vos droits</h2>
 <p>Vous pouvez demander la suppression des données vous concernant en
 contactant un administrateur du serveur ou l'exploitant du Bot. Retirer le
 Bot d'un serveur cesse toute nouvelle collecte pour ce serveur.</p>

 <h2>7. Contact</h2>
 <p>Pour toute question relative à ces données, contactez l'exploitant du Bot
 via le serveur de support ou la commande <code>contactowner</code>.</p>
"""

_TERMS_BODY = """
 <h1>Conditions d'utilisation</h1>
 <p><em>Dernière mise à jour : 2026.</em></p>
 <p>En ajoutant ou en utilisant le bot « Watcher » (« le Bot »), vous
 acceptez les présentes conditions.</p>

 <h2>1. Service</h2>
 <p>Le Bot fournit des fonctionnalités de modération, d'utilitaires et de
 statistiques pour les serveurs Discord. Il est fourni « tel quel », sans
 garantie de disponibilité ni d'absence d'erreurs.</p>

 <h2>2. Utilisation acceptable</h2>
 <ul>
   <li>Respectez les <a href="https://discord.com/terms">Conditions de
   Discord</a> et les <a href="https://discord.com/guidelines">Règles de la
   communauté</a> ;</li>
   <li>N'utilisez pas le Bot pour harceler, espionner à des fins abusives, ou
   enfreindre la loi ;</li>
   <li>Les fonctionnalités de surveillance et de modération doivent être
   utilisées de manière responsable et conforme au droit applicable et à la
   transparence envers vos membres.</li>
 </ul>

 <h2>3. Responsabilité</h2>
 <p>L'exploitant du Bot ne saurait être tenu responsable des dommages
 résultant de l'utilisation ou de l'indisponibilité du Bot, ni de l'usage
 qu'en font les administrateurs de serveur.</p>

 <h2>4. Disponibilité</h2>
 <p>Le service peut être modifié, suspendu ou interrompu à tout moment, sans
 préavis.</p>

 <h2>5. Données</h2>
 <p>Le traitement des données est décrit dans la
 <a href="/privacy">Politique de confidentialité</a>.</p>

 <h2>6. Modifications</h2>
 <p>Ces conditions peuvent évoluer. L'utilisation continue du Bot vaut
 acceptation de la version en vigueur.</p>
"""

_PRIVACY_BODY_EN = """
 <h1>Privacy Policy</h1>
 <p><em>Last updated: 2026.</em></p>
 <p>This policy describes the data processed by the Discord bot “Watcher”
 (“the Bot”) and how it is used.</p>

 <h2>1. Data collected</h2>
 <p>Depending on the features enabled by a server's administrators, the Bot may
 store:</p>
 <ul>
   <li><strong>Discord identifiers</strong> (users, servers, channels, roles)
   required to run commands;</li>
   <li><strong>Moderation data</strong>: warnings, mutes, confinements and the
   history of sanctions;</li>
   <li><strong>Aggregated statistics</strong>: message counts, joins and
   leaves, member counts (for activity charts);</li>
   <li><strong>Server settings</strong> (enabled protections);</li>
   <li><strong>Reminders</strong> you schedule;</li>
   <li>When an administrator enables <strong>watching</strong> of a user, the
   content of their messages, reactions, nickname and status changes, and voice
   activity are copied into a private channel of the relevant server.</li>
 </ul>
 <p>The Bot only accesses message content for the automoderation and watching
 features described above.</p>

 <h2>2. Web panel login</h2>
 <p>The admin panel uses Discord authentication (OAuth2). The Bot then reads
 your identifier, username and the list of your servers to verify your access
 rights. None of this information is sold or shared with third parties.</p>
 <p>A strictly necessary session cookie keeps you logged in. Once logged in,
 your <strong>language choice is stored server-side, tied to your account</strong>.
 On public pages, storing the language in your browser (local storage) only
 happens with your <strong>consent</strong>.</p>

 <h2>3. Purposes</h2>
 <p>Data is used solely to operate the Bot (moderation, statistics, reminders)
 and is not used for advertising.</p>

 <h2>4. Retention</h2>
 <p>Data is kept as long as necessary for the service. Activity statistics are
 automatically purged after 60 days. An administrator can delete data related
 to a feature by disabling it (e.g. <code>unwatch</code>, <code>unwarn</code>).</p>

 <h2>5. Sharing</h2>
 <p>Data is not shared with third parties. It remains stored by the Bot's host
 and, for watching, within the relevant Discord server.</p>

 <h2>6. Your rights</h2>
 <p>You may request deletion of your data by contacting a server administrator
 or the Bot operator. Removing the Bot from a server stops any further
 collection for that server.</p>

 <h2>7. Contact</h2>
 <p>For any question about this data, contact the Bot operator through the
 support server or the <code>contactowner</code> command.</p>
"""

_TERMS_BODY_EN = """
 <h1>Terms of Service</h1>
 <p><em>Last updated: 2026.</em></p>
 <p>By adding or using the “Watcher” bot (“the Bot”), you accept these terms.</p>

 <h2>1. Service</h2>
 <p>The Bot provides moderation, utility and statistics features for Discord
 servers. It is provided “as is”, without warranty of availability or absence
 of errors.</p>

 <h2>2. Acceptable use</h2>
 <ul>
   <li>Comply with the <a href="https://discord.com/terms">Discord Terms</a> and
   <a href="https://discord.com/guidelines">Community Guidelines</a>;</li>
   <li>Do not use the Bot to harass, spy abusively, or break the law;</li>
   <li>Watching and moderation features must be used responsibly and in
   compliance with applicable law and transparency towards your members.</li>
 </ul>

 <h2>3. Liability</h2>
 <p>The Bot operator cannot be held liable for damages resulting from the use
 or unavailability of the Bot, nor for how server administrators use it.</p>

 <h2>4. Availability</h2>
 <p>The service may be modified, suspended or discontinued at any time without
 notice.</p>

 <h2>5. Data</h2>
 <p>Data processing is described in the
 <a href="/privacy">Privacy Policy</a>.</p>

 <h2>6. Changes</h2>
 <p>These terms may change. Continued use of the Bot constitutes acceptance of
 the version in force.</p>
"""

_PRIVACY_HTML = _legal_page("Confidentialité / Privacy", _PRIVACY_BODY, _PRIVACY_BODY_EN)
_TERMS_HTML = _legal_page("Conditions / Terms", _TERMS_BODY, _TERMS_BODY_EN)
