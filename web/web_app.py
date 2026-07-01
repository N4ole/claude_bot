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


def _set_session(response: web.Response, data: dict) -> None:
    token = secrets.token_urlsafe(32)
    _sessions[token] = data
    response.set_cookie(
        "session", token, httponly=True, samesite="Lax", max_age=86400
    )


# --------------------------------------------------------------------------- #
# OAuth
# --------------------------------------------------------------------------- #
def _authorize_url() -> str:
    params = {
        "client_id": config.OAUTH_CLIENT_ID,
        "redirect_uri": config.OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
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

    async def login(_request: web.Request) -> web.Response:
        raise web.HTTPFound(_authorize_url())

    async def logout(request: web.Request) -> web.Response:
        token = request.cookies.get("session")
        _sessions.pop(token, None)
        response = web.HTTPFound("/")
        response.del_cookie("session")
        return response

    async def callback(request: web.Request) -> web.Response:
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
             "guild_ids": guild_ids},
        )
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

    app.router.add_get("/", index)
    app.router.add_get("/login", login)
    app.router.add_get("/logout", logout)
    app.router.add_get("/callback", callback)
    app.router.add_get("/api/stats", api_stats)
    app.router.add_post("/api/control/presence", control_presence)
    app.router.add_post("/api/control/reload", control_reload)
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
"""

_LOGIN_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>ClaudeBot — Panel</title>
<style>""" + _NEON_CSS + """
 body{display:flex;height:100vh;align-items:center;justify-content:center}
 .card{padding:44px;text-align:center;max-width:420px}
</style></head>
<body><div class="card">
 <h1>▚ ClaudeBot ▞</h1>
 <p>Panneau d'administration. Connecte-toi avec Discord pour accéder aux
 statistiques et au contrôle du bot.</p>
 <a class="btn" href="/login">Se connecter avec Discord</a>
</div></body></html>"""

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>ClaudeBot — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>""" + _NEON_CSS + """
 body{padding:24px;max-width:1100px;margin:auto}
 header{display:flex;justify-content:space-between;align-items:center;
   border-bottom:1px solid rgba(157,75,255,.3);padding-bottom:12px}
 canvas{max-height:320px}
 .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
</style></head>
<body>
 <header><h1>▚ ClaudeBot ▞</h1>
   <span class="row"><span id="who"></span>
   <a class="btn" href="/logout">Déconnexion</a></span></header>
 <div id="content"></div>
<script>
function fmtUptime(s){const d=Math.floor(s/86400),h=Math.floor(s%86400/3600),
 m=Math.floor(s%3600/60);return (d?d+'j ':'')+(h?h+'h ':'')+m+'m';}
function tsLabels(p){return p.map(x=>new Date(x.ts*1000).toLocaleString());}
const NEON={cyan:'#00eaff',magenta:'#ff2bd6',purple:'#9d4bff',
 green:'#39ff14',yellow:'#f5ff3d'};
Chart.defaults.color='#c8c8e6';Chart.defaults.borderColor='rgba(157,75,255,.15)';
function card(html){const c=document.createElement('div');c.className='card';
 c.innerHTML=html;document.getElementById('content').appendChild(c);return c;}
async function post(url,body){const r=await fetch(url,{method:'POST',
 headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
 return r.json();}
async function load(){
 const r=await fetch('/api/stats');
 if(!r.ok){document.getElementById('content').innerHTML=
   '<p>Session expirée. <a href="/login">Se reconnecter</a></p>';return;}
 const d=await r.json();
 document.getElementById('who').textContent='@'+(d.user.username||'');
 // Analytics (owners).
 if(d.analytics){const a=d.analytics;
   card('<h2>Analytics</h2><div class="grid">'+
    '<div class="stat"><div class="n">'+a.guilds+'</div><div class="l">Serveurs</div></div>'+
    '<div class="stat"><div class="n">'+a.members+'</div><div class="l">Membres</div></div>'+
    '<div class="stat"><div class="n">'+a.commands_total+'</div><div class="l">Commandes</div></div>'+
    '<div class="stat"><div class="n">'+a.latency_ms+'<span style="font-size:.5em">ms</span></div><div class="l">Ping</div></div>'+
    '<div class="stat"><div class="n">'+fmtUptime(a.uptime_seconds)+'</div><div class="l">Uptime</div></div>'+
    '</div>');
   // Contrôle du bot (owners).
   const cc=card('<h2>Contrôle du bot</h2>'+
    '<div class="row"><input id="pres" placeholder="Statut (ex: §help)" value="'+
      (a.presence||'')+'"><button class="btn" id="setpres">Définir le statut</button>'+
    '<button class="btn" id="reload">Recharger les cogs</button>'+
    '<span id="ctlmsg"></span></div>');
   cc.querySelector('#setpres').onclick=async()=>{
     const t=cc.querySelector('#pres').value;const j=await post('/api/control/presence',{text:t});
     cc.querySelector('#ctlmsg').textContent=j.ok?'✅ Statut mis à jour':'❌ Erreur';};
   cc.querySelector('#reload').onclick=async()=>{
     const j=await post('/api/control/reload');
     cc.querySelector('#ctlmsg').textContent=j.ok?('✅ '+j.reloaded+' cogs rechargés'):'❌ Erreur';};
 }
 // Évolution serveurs (owners).
 if(d.servers_history){
   card('<h2>Évolution du nombre de serveurs</h2><canvas id="servers"></canvas>');
   new Chart(document.getElementById('servers'),{type:'line',data:{
     labels:tsLabels(d.servers_history),datasets:[
      {label:'Serveurs',data:d.servers_history.map(p=>p.guilds),
       borderColor:NEON.cyan,backgroundColor:'rgba(0,234,255,.1)',fill:true,tension:.25},
      {label:'Membres (total)',data:d.servers_history.map(p=>p.members),
       borderColor:NEON.magenta,tension:.25,yAxisID:'y1'}]},
     options:{scales:{y1:{position:'right'}}}});
 }
 // Par serveur.
 d.guilds.forEach((g,i)=>{
   card('<h2>'+g.name+'</h2><canvas id="m'+i+'"></canvas><canvas id="u'+i+'"></canvas>');
   new Chart(document.getElementById('m'+i),{type:'line',data:{
     labels:tsLabels(g.members),datasets:[{label:'Membres',
       data:g.members.map(p=>p.count),borderColor:NEON.green,
       backgroundColor:'rgba(57,255,20,.1)',fill:true,tension:.25}]}});
   new Chart(document.getElementById('u'+i),{type:'bar',data:{
     labels:g.usage.map(p=>p.date),datasets:[{label:'Commandes utilisées',
       data:g.usage.map(p=>p.count),backgroundColor:NEON.purple}]}});
 });
 if(!d.analytics && d.guilds.length===0){
   card('<p>Aucune donnée disponible pour le moment.</p>');}
}
load();
</script>
</body></html>"""
