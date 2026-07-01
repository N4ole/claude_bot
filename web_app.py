"""Panel web du bot : connexion Discord OAuth2, réservé aux administrateurs.

Affiche des graphiques (évolution du nombre de serveurs, membres par serveur,
utilisation par serveur). L'accès est réservé :
  - aux owners du bot (voient toutes les données) ;
  - aux administrateurs d'un serveur où le bot est présent (voient les données
    des serveurs qu'ils administrent).
"""
import secrets
from urllib.parse import urlencode

import aiohttp
from aiohttp import web

import checks
import config
import stats

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
        return web.json_response(payload)

    app.router.add_get("/", index)
    app.router.add_get("/login", login)
    app.router.add_get("/logout", logout)
    app.router.add_get("/callback", callback)
    app.router.add_get("/api/stats", api_stats)
    return app


# --------------------------------------------------------------------------- #
# Pages HTML
# --------------------------------------------------------------------------- #
_LOGIN_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>ClaudeBot — Panel</title>
<style>
 body{font-family:system-ui,sans-serif;background:#1e1f22;color:#eee;
   display:flex;height:100vh;align-items:center;justify-content:center;margin:0}
 .card{background:#2b2d31;padding:40px;border-radius:12px;text-align:center}
 a.btn{display:inline-block;margin-top:20px;background:#5865F2;color:#fff;
   padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600}
</style></head>
<body><div class="card">
 <h1>📊 ClaudeBot — Panel admin</h1>
 <p>Connecte-toi avec Discord pour accéder aux statistiques.</p>
 <a class="btn" href="/login">Se connecter avec Discord</a>
</div></body></html>"""

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>ClaudeBot — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
 body{font-family:system-ui,sans-serif;background:#1e1f22;color:#eee;margin:0;
   padding:24px}
 header{display:flex;justify-content:space-between;align-items:center}
 a{color:#8ea1ff}
 .card{background:#2b2d31;border-radius:12px;padding:20px;margin:16px 0}
 h2{margin-top:0}
 canvas{max-height:320px}
</style></head>
<body>
 <header><h1>📊 ClaudeBot</h1><a href="/logout">Se déconnecter</a></header>
 <div id="content"></div>
<script>
function tsLabels(points){return points.map(p=>new Date(p.ts*1000)
  .toLocaleString());}
async function load(){
 const r = await fetch('/api/stats');
 if(!r.ok){document.getElementById('content').innerHTML=
   '<p>Session expirée. <a href="/login">Se reconnecter</a></p>';return;}
 const d = await r.json();
 const content = document.getElementById('content');
 if(d.servers_history){
   const c=document.createElement('div');c.className='card';
   c.innerHTML='<h2>Évolution du nombre de serveurs</h2>'+
     '<canvas id="servers"></canvas>';
   content.appendChild(c);
   new Chart(document.getElementById('servers'),{type:'line',data:{
     labels:tsLabels(d.servers_history),
     datasets:[
      {label:'Serveurs',data:d.servers_history.map(p=>p.guilds),
       borderColor:'#5865F2',tension:.2},
      {label:'Membres (total)',data:d.servers_history.map(p=>p.members),
       borderColor:'#57F287',tension:.2,yAxisID:'y1'}]},
     options:{scales:{y1:{position:'right'}}}});
 }
 d.guilds.forEach((g,i)=>{
   const c=document.createElement('div');c.className='card';
   c.innerHTML='<h2>'+g.name+'</h2>'+
     '<canvas id="m'+i+'"></canvas><canvas id="u'+i+'"></canvas>';
   content.appendChild(c);
   new Chart(document.getElementById('m'+i),{type:'line',data:{
     labels:tsLabels(g.members),
     datasets:[{label:'Membres',data:g.members.map(p=>p.count),
       borderColor:'#57F287',tension:.2}]}});
   new Chart(document.getElementById('u'+i),{type:'bar',data:{
     labels:g.usage.map(p=>p.date),
     datasets:[{label:'Commandes utilisées',data:g.usage.map(p=>p.count),
       backgroundColor:'#FEE75C'}]}});
 });
 if(!d.servers_history && d.guilds.length===0){
   content.innerHTML='<p>Aucune donnée disponible pour le moment.</p>';}
}
load();
</script>
</body></html>"""
