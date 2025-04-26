import pytz

# bot.py
import discord
from discord.ext import commands
from discord import Object
from collections import defaultdict
from datetime import datetime, timedelta
import json
import os
import shutil
import logging
import re
from dotenv import load_dotenv


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")],
)
logger = logging.getLogger("wec-bot")


class Config:
    COMMAND_PREFIX = "!"

    # robins server
    GUILD_ID = 417833754325811200
    GUILD2_ID = 1005949928297734284

    # scrim channel aus robins server
    SCRIM_CHANNEL_ID = 1363843518455484599

    SCRIM2_CHANNEL_ID = 1364722193963159653
    TEAMS = [
        t.lower()
        for t in ["Gold", "Crystal", "Ruby", "Silver", "Mixed", "Unite", "Splatoon"]
    ]
    TEAM_COLORS = {
        "gold": "🟡",
        "crystal": "🔷",
        "ruby": "🔴",
        "silver": "⚪",
        "mixed": "🟠",
        "unite": "⚡",
        "splatoon": "🦑",
    }
    HOURS = list(range(24))
    BACKUP_RETENTION_DAYS = 7
    MAX_PLAYERS_DEFAULT = 6
    MAX_PLAYERS_PER_TEAM = {"unite": 5, "splatoon": 4}
    # channel "scrim" aus dem WEC-Server
    VOLL_CHANNEL_ID = 853950976385613844


def get_max_players(team):
    return Config.MAX_PLAYERS_PER_TEAM.get(team, Config.MAX_PLAYERS_DEFAULT)


DATA_FILE = "scrims.json"
BACKUP_FOLDER = "backups"
FULL_LIST_FILE = "voll_scrims.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(
    command_prefix=Config.COMMAND_PREFIX, intents=intents, help_command=None
)

events = defaultdict(
    lambda: defaultdict(lambda: defaultdict(lambda: {"main": [], "subs": []}))
)
scrim_ids = defaultdict(lambda: defaultdict(int))


# Message_ID für die Scrim-Liste wird gespeichert, damit man später diese Nachricht editieren,
# anstatt jedes mal eine neue Nachricht für die Liste abzusenden.
# Am Besten seperat parallel zum Main_Bot als WebHook laufen lassen (alle 5 min updaten)
#
def save_message_id(message_id):
    print(message_id)


# überarbeitung dieser 2 Funktion, um übersichtlichkeit zu haben
# checkt vorher, ob eintrag vorher schon vorhanden ist, da wahrscheinlichkeit morgens
# nicht da ist, dass ein scrim stattfindet
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                team: {
                    str(hour): {
                        str(scrim_num): {
                            "main": [u.id for u in data["main"]],
                            "subs": [u.id for u in data["subs"]],
                        }
                        for scrim_num, data in hours.items()
                    }
                    for hour, hours in team_data.items()
                }
                for team, team_data in events.items()
            },
            f,
        )
    create_backup()
    save_full_list()


def save_full_list():
    voll = []
    for team in Config.TEAMS:
        for hour in Config.HOURS:
            for scrim_num, data in events[team][hour].items():
                if len(data["main"]) >= get_max_players(team):
                    voll.append(
                        {
                            "team": team,
                            "hour": hour,
                            "scrim_num": scrim_num,
                            "main": [u.id for u in data["main"]],
                            "subs": [u.id for u in data["subs"]],
                        }
                    )
    with open(FULL_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(voll, f, indent=2)


def load_data():
    if not os.path.isfile(DATA_FILE):
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    for team, hours in raw.items():
        for hour, scrims in hours.items():
            for scrim_num, data in scrims.items():
                for role in ["main", "subs"]:
                    events[team][int(hour)][int(scrim_num)][role] = [
                        bot.get_user(uid) or Object(id=uid) for uid in data[role]
                    ]


def create_backup():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    shutil.copy2(
        DATA_FILE, os.path.join(BACKUP_FOLDER, f"scrims_backup_{timestamp}.json")
    )


def clean_display_name(name):
    return re.sub(r"[^A-Za-z\s]", "", name)


@bot.command(name="hilfe")
async def hilfe(ctx):
    msg = (
        "**WEC-Bot Hilfe**\n"
        "`!c TEAM STUNDE` – Zusagen\n"
        "`!d TEAM STUNDE` – Absagen\n"
        "`!sub TEAM STUNDE` – Als Sub eintragen\n"
        "`!l [TEAM]` – Liste aller oder einzelner Scrims\n"
        "`!reset` – (Admin) Reset aller Daten\n"
        "`!ac @User TEAM STUNDE` – (Admin) User eintragen\n"
        "`!asub @User TEAM STUNDE` – (Admin) User als Sub eintragen\n"
        "`!ad @User TEAM STUNDE` – (Admin) User austragen\n"
        "`!replace @Alt @Neu TEAM STUNDE` – (Admin) User ersetzen\n"
    )
    await ctx.send(msg)


@bot.command(name="c")
async def zusagen(ctx, *args):
    user = ctx.author
    await handle_signup(ctx, user, args, as_sub=False)
    print(dir(ctx))


@bot.command(name="sub")
async def sub(ctx, *args):
    user = ctx.author
    await handle_signup(ctx, user, args, as_sub=True)


@bot.command(name="asub")
@commands.has_permissions(administrator=True)
async def admin_sub(ctx, user: discord.Member, team: str, hour: int):
    await handle_signup(ctx, user, [team, str(hour)], as_sub=True)


@bot.command(name="ad")
@commands.has_permissions(administrator=True)
async def admin_remove(ctx, user: discord.Member, team: str, hour: int):
    team = team.lower()
    if team not in Config.TEAMS or hour not in Config.HOURS:
        await ctx.send("❌ Ungültiges Team oder Uhrzeit.")
        return
    for scrim_num in events[team][hour]:
        events[team][hour][scrim_num]["main"] = [
            u for u in events[team][hour][scrim_num]["main"] if u.id != user.id
        ]
        events[team][hour][scrim_num]["subs"] = [
            u for u in events[team][hour][scrim_num]["subs"] if u.id != user.id
        ]
    save_data()
    await ctx.send(
        f"🗑️ {user.display_name} wurde entfernt aus {team.capitalize()} {hour} Uhr."
    )


# Behandelt die Scrimliste, um Person hinzuzufügen/entfernen mit ggf. admin_checkin
#
# bessere struktur für die scrimliste muss noch erstellt werden.
async def handle_signup(ctx, user, args, as_sub):
    voll_channel = bot.get_channel(Config.SCRIM2_CHANNEL_ID)
    for team, hour in parse_pairs(args):
        ensure_scrim_slot(team, hour)
        scrim_id = scrim_ids[team][hour]

        for sid in events[team][hour]:
            events[team][hour][sid]["main"] = [
                u for u in events[team][hour][sid]["main"] if u.id != user.id
            ]
            events[team][hour][sid]["subs"] = [
                u for u in events[team][hour][sid]["subs"] if u.id != user.id
            ]

        role = "subs" if as_sub else "main"
        if user not in events[team][hour][scrim_id][role]:
            events[team][hour][scrim_id][role].append(user)

        if not as_sub and len(events[team][hour][scrim_id]["main"]) == get_max_players(
            team
        ):
            mentions = " ".join(
                u.mention
                for u in sorted(
                    events[team][hour][scrim_id]["main"],
                    key=lambda x: x.display_name.lower()
                    if hasattr(x, "display_name")
                    else "",
                )
            )
            await voll_channel.send(
                f"✅ {Config.TEAM_COLORS[team]} {team.capitalize()} {hour} Uhr ist voll!\n"
                f"{mentions}\n"
                f"Bitte 6v6 suchen."
            )
            for sid, scrim in list(events[team][hour].items()):
                if sid != scrim_id:
                    scrim["main"] = [u for u in scrim["main"] if u.id != user.id]
                    scrim["subs"] = [u for u in scrim["subs"] if u.id != user.id]

    save_data()
    await ctx.send(f"{'🏦' if as_sub else '✅'} {user.mention} wurde eingetragen.")
    await list_scrims(ctx)


@bot.command(name="d")
async def absagen(ctx, *args):
    user = ctx.author
    for team, hour in parse_pairs(args):
        for scrim_num in events[team][hour]:
            events[team][hour][scrim_num]["main"] = [
                u for u in events[team][hour][scrim_num]["main"] if u.id != user.id
            ]
            events[team][hour][scrim_num]["subs"] = [
                u for u in events[team][hour][scrim_num]["subs"] if u.id != user.id
            ]
    save_data()
    await ctx.send(f"❌ {user.mention} wurde entfernt.")


@bot.command(name="ac")
@commands.has_permissions(administrator=True)
async def admin_checkin(ctx, user: discord.Member, team: str, hour: int):
    await handle_signup(ctx, user, [team, str(hour)], as_sub=False)


@bot.command(name="replace")
@commands.has_permissions(administrator=True)
async def replace_user(
    ctx, alt_user: discord.Member, new_user: discord.Member, team: str, hour: int
):
    team = team.lower()
    if team not in Config.TEAMS or hour not in Config.HOURS:
        await ctx.send("❌ Ungültiges Team oder Uhrzeit.")
        return
    voll_channel = bot.get_channel(Config.SCRIM2_CHANNEL_ID)
    ensure_scrim_slot(team, hour)
    scrim_id = scrim_ids[team][hour]

    for sid in events[team][hour]:
        events[team][hour][sid]["main"] = [
            u
            for u in events[team][hour][sid]["main"]
            if u.id != alt_user.id and u.id != new_user.id
        ]
        events[team][hour][sid]["subs"] = [
            u
            for u in events[team][hour][sid]["subs"]
            if u.id != alt_user.id and u.id != new_user.id
        ]

    events[team][hour][scrim_id]["main"].append(new_user)

    if len(events[team][hour][scrim_id]["main"]) == get_max_players(team):
        mentions = " ".join(
            u.mention
            for u in sorted(
                events[team][hour][scrim_id]["main"],
                key=lambda x: x.display_name.lower()
                if hasattr(x, "display_name")
                else "",
            )
        )
        await voll_channel.send(
            f"✅ {Config.TEAM_COLORS[team]} {team.capitalize()} {hour} Uhr ist voll!\n"
            f"{mentions}\n"
            f"Bitte 6v6 suchen."
        )

    save_data()
    await ctx.send(
        f"🔁 {alt_user.display_name} wurde durch {new_user.display_name} ersetzt für {team.capitalize()} {hour} Uhr."
    )


@bot.command(name="l")
async def list_scrims(ctx, *args):
    teams_filter = [arg.lower() for arg in args if arg.lower() in Config.TEAMS]
    msg = ""
    for team in Config.TEAMS:
        if teams_filter and team not in teams_filter:
            continue
        for hour in sorted(events[team].keys()):
            for scrim_num, data in events[team][hour].items():
                if data["main"] or data["subs"]:
                    line = f"{Config.TEAM_COLORS.get(team, '')} {team.capitalize()} {hour} Uhr ({len(data['main'])}/{get_max_players(team)})"
                    if data["main"]:
                        mains = ", ".join(
                            clean_display_name(u.display_name)
                            if hasattr(u, "display_name")
                            else str(u.id)
                            for u in data["main"]
                        )
                        line += f" LU: {mains}"
                    if data["subs"]:
                        subs = ", ".join(
                            clean_display_name(u.display_name)
                            if hasattr(u, "display_name")
                            else str(u.id)
                            for u in data["subs"]
                        )
                        line += f" 🏦 {subs}"
                    msg += line + "\n"
    message = await ctx.send(msg or "Keine Scrims vorhanden.")
    save_message_id(message.id)


@bot.command(name="reset")
@commands.has_permissions(administrator=True)
async def admin_reset(ctx):
    events.clear()
    scrim_ids.clear()
    save_data()
    await ctx.send("♻️ Scrim-Daten wurden zurückgesetzt.")


def ensure_scrim_slot(team, hour):
    scrim_id = scrim_ids[team][hour]
    if len(events[team][hour][scrim_id]["main"]) >= get_max_players(team):
        scrim_ids[team][hour] += 1


def parse_pairs(args):
    pairs, hours = [], []
    for arg in args:
        if arg.lower() in Config.TEAMS:
            if hours:
                for hour in hours:
                    pairs.append((arg.lower(), hour))
                hours = []
            else:
                pairs.append((arg.lower(), None))
        else:
            try:
                h = int(arg)
                if h in Config.HOURS:
                    hours.append(h)
            except:
                continue
    if hours and pairs:
        last_team = pairs[-1][0]
        pairs = [p for p in pairs if p[1] is not None]
        for h in hours:
            pairs.append((last_team, h))
    return pairs


@bot.event
async def on_ready():
    logger.info(f"{bot.user} ist online!")
    load_data()
    # Alte, nicht volle Scrims löschen (basierend auf CEST)
    cest = pytz.timezone("Europe/Berlin")
    now_hour = datetime.now(cest).hour

    for team in list(events.keys()):
        for hour in list(events[team].keys()):
            if hour < now_hour:
                for scrim_num in list(events[team][hour].keys()):
                    data = events[team][hour][scrim_num]
                    if len(data["main"]) < get_max_players(team):
                        del events[team][hour][scrim_num]
                if not events[team][hour]:  # Stunde leer?
                    del events[team][hour]

    save_data()
    logger.info("Vergangene, unvollständige Scrims wurden entfernt (CEST).")


@bot.command(name="full")
async def list_full_scrims(ctx):
    save_full_list()  # Exportiere in voll_scrims.json
    from datetime import datetime
    import pytz

    cest = pytz.timezone("Europe/Berlin")
    timestamp = datetime.now(cest).strftime("%Y-%m-%d %H:%M")

    voll = []
    for team in Config.TEAMS:
        for hour in Config.HOURS:
            for scrim_num, data in events[team][hour].items():
                if len(data["main"]) >= get_max_players(team):
                    mains = ", ".join(
                        clean_display_name(u.display_name)
                        if hasattr(u, "display_name")
                        else str(u.id)
                        for u in data["main"]
                    )
                    voll.append(
                        f"{Config.TEAM_COLORS[team]} {team.capitalize()} {hour} Uhr • LU: {mains}"
                    )
    header = f"**Volle Scrims – Stand: {timestamp}**\n"
    await ctx.send(header + ("\n".join(voll) if voll else "Keine vollen Scrims."))


load_dotenv()
client_id = os.getenv("KJ_ID")
bot.run(client_id)
