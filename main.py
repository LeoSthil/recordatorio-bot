import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime, timedelta
import json

# Configuración
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1379477200298053784
TIMEZONE = "America/Argentina/Buenos_Aires"
EVENT_HOUR_ARG = 22
REMINDER_HOUR_ARG = 17

# Cargar tipo de evento
def load_event_type():
    with open("config.json", "r") as f:
        return json.load(f)["current_event"]

def save_event_type(event_type):
    with open("config.json", "w") as f:
        json.dump({"current_event": event_type}, f)

# Generar mensaje
def generate_message(event_type):
    if event_type == "guerra":
        intro = "Guerreros, mañana es la 💥GUERRA TERRITORIAL💥 Demuestren su fuerza, estrategia y honor en el campo de batalla. NO OLVIDEN MARCAR EL BOT. 🔥⚔️La victoria será nuestra🔥⚔️."
    else:
        intro = "Guerreros, es nuestro deber seguir mejorando, así que los invitamos cordialmente a un 💥ENTRENAMIENTO💥 La excelencia no es un acto, sino un hábito. NO OLVIDEN MARCAR EL BOT."

    tz = pytz.timezone(TIMEZONE)
    event_time = tz.localize(datetime.now().replace(hour=EVENT_HOUR_ARG, minute=0, second=0, microsecond=0) + timedelta(days=1))

    zones = {
        "🇲🇽 México": "America/Mexico_City",
        "🇵🇪 Perú": "America/Lima",
        "🇨🇴 Colombia": "America/Bogota",
        "🇻🇪 Venezuela": "America/Caracas",
        "🇨🇱 Chile": "America/Santiago",
        "🇦🇷 Argentina": "America/Argentina/Buenos_Aires",
        "🇧🇷 Brasil": "America/Sao_Paulo",
        "🇪🇸 España": "Europe/Madrid"
    }

    times = "\n".join([f"{flag}: {event_time.astimezone(pytz.timezone(tz)).strftime('%H:%M')} UTC{event_time.astimezone(pytz.timezone(tz)).strftime('%z')[:-2]}" for flag, tz in zones.items()])
    return f"{intro}\n\n🕒 Horarios del evento:\n{times}"

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    scheduler.add_job(send_reminder, CronTrigger(day_of_week='mon,fri', hour=REMINDER_HOUR_ARG, timezone=TIMEZONE))
    scheduler.start()

@bot.command()
async def guerra(ctx):
    save_event_type("guerra")
    await ctx.send("Evento configurado: 💥GUERRA TERRITORIAL💥")

@bot.command()
async def entrenamiento(ctx):
    save_event_type("entrenamiento")
    await ctx.send("Evento configurado: 💥ENTRENAMIENTO💥")

@bot.command()
async def prueba(ctx):
    event_type = load_event_type()
    message = generate_message(event_type)
    await ctx.send(message)

async def send_reminder():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        event_type = load_event_type()
        message = generate_message(event_type)
        await channel.send(message)

bot.run(TOKEN)
