import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time, timedelta
import pytz

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1379477200298053784

intents = discord.Intents.default()
intents.message_content = True

allowed_mentions = discord.AllowedMentions(everyone=True)

bot = commands.Bot(command_prefix='!', intents=intents, allowed_mentions=allowed_mentions)
scheduler = AsyncIOScheduler()

current_event = None
last_reminder_message_id = None
last_event_date = None

tz_mx = pytz.timezone("America/Mexico_City")
tz_peru = pytz.timezone("America/Lima")
tz_col = pytz.timezone("America/Bogota")
tz_ven = pytz.timezone("America/Caracas")
tz_chile = pytz.timezone("America/Santiago")
tz_argentina = pytz.timezone("America/Argentina/Buenos_Aires")
tz_brasil = pytz.timezone("America/Sao_Paulo")

def format_time(dt):
    return dt.strftime("%H:%M")

def get_event_message(event):
    if event == "guerra":
        return ("Guerreros, mañana es la 💥GUERRA TERRITORIAL💥 Demuestren su fuerza, estrategia y honor en el campo de batalla. "
                "NO OLVIDEN MARCAR EL BOT. 🔥⚔️La victoria será nuestra🔥⚔️.")
    elif event == "entrenamiento":
        return ("Guerreros, es nuestro deber seguir mejorando nuestra forma de jugar, así que los invitamos cordialmente a un 💥ENTRENAMIENTO💥 "
                "La excelencia no es un acto, sino un hábito. NO OLVIDEN MARCAR EL BOT.")
    else:
        return None

def get_event_datetime(event_date):
    # Hora del evento: 20:30 Argentina
    return tz_argentina.localize(datetime.combine(event_date, time(20, 30)))

def get_all_times(event_date):
    dt_arg = get_event_datetime(event_date)
    times = {
        "México": format_time(dt_arg.astimezone(tz_mx)) + " (UTC-5/-6 dependiendo horario)",
        "Perú": format_time(dt_arg.astimezone(tz_peru)) + " (UTC-5)",
        "Colombia": format_time(dt_arg.astimezone(tz_col)) + " (UTC-5)",
        "Venezuela": format_time(dt_arg.astimezone(tz_ven)) + " (UTC-4)",
        "Chile": format_time(dt_arg.astimezone(tz_chile)) + " (UTC-3/-4 dependiendo horario)",
        "Argentina": format_time(dt_arg.astimezone(tz_argentina)) + " (UTC-3)",
        "Brasil": format_time(dt_arg.astimezone(tz_brasil)) + " (UTC-3)",
    }
    return times

async def send_reminder():
    global last_reminder_message_id, last_event_date

    if current_event is None:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("No se encontró el canal")
        return

    ahora_arg = datetime.now(tz_argentina)

    event_date = None
    if current_event == "guerra":
        manana = ahora_arg + timedelta(days=1)
        if manana.weekday() in [1, 5]:  # martes=1, sábado=5
            event_date = manana.date()
        else:
            return
    elif current_event == "entrenamiento":
        manana = ahora_arg + timedelta(days=1)
        event_date = manana.date()

    if event_date is None:
        return

    # Borrar mensaje anterior si existe
    if last_reminder_message_id:
        try:
            msg = await channel.fetch_message(last_reminder_message_id)
            await msg.delete()
        except Exception as e:
            print(f"No se pudo borrar el mensaje anterior: {e}")

    mensaje = "@everyone " + get_event_message(current_event)
    horarios = get_all_times(event_date)
    horarios_str = "\n".join([f"**{pais}:** {hora}" for pais, hora in horarios.items()])
    texto_final = f"{mensaje}\n\n🕒 Horarios de inicio según países:\n{horarios_str}"

    msg = await channel.send(texto_final)
    last_reminder_message_id = msg.id
    last_event_date = event_date

    # Programar borrado para las 20:30 (hora del evento)
    event_dt = get_event_datetime(event_date)
    print(f"Mensaje programado para borrarse a las {event_dt} (ARG) / {event_dt.astimezone(pytz.utc)} (UTC)")
    scheduler.add_job(delete_reminder, 'date', run_date=event_dt.astimezone(pytz.utc), args=[CHANNEL_ID, msg.id])

async def delete_reminder(channel_id, message_id):
    channel = bot.get_channel(channel_id)
    if channel is None:
        print("No se encontró el canal para borrar mensaje")
        return

    try:
        msg = await channel.fetch_message(message_id)
        await msg.delete()
        print(f"Mensaje {message_id} borrado a la hora del evento.")
    except Exception as e:
        print(f"No se pudo borrar el mensaje {message_id}: {e}")

@bot.command()
async def guerra(ctx):
    global current_event
    current_event = "guerra"
    await ctx.send("Evento configurado para 💥GUERRA TERRITORIAL💥. Recordatorios activados.")

@bot.command()
async def entrenamiento(ctx):
    global current_event
    current_event = "entrenamiento"
    await ctx.send("Evento configurado para 💥ENTRENAMIENTO💥. Recordatorios activados.")

@bot.command()
async def prueba(ctx):
    if current_event is None:
        await ctx.send("No hay evento configurado. Usa !guerra o !entrenamiento primero.")
        return

    event_date = datetime.now(tz_argentina).date() + timedelta(days=1)
    mensaje = "@everyone " + get_event_message(current_event)
    horarios = get_all_times(event_date)
    horarios_str = "\n".join([f"**{pais}:** {hora}" for pais, hora in horarios.items()])
    texto_final = f"{mensaje}\n\n🕒 Horarios de inicio según países:\n{horarios_str}"
    await ctx.send(texto_final)

@bot.event
async def on_ready():
    print(f'Bot listo! Conectado como {bot.user}')
    scheduler.remove_all_jobs()
    # Enviar recordatorio lunes y sábado a las 20:20 ARG
    scheduler.add_job(send_reminder, 'cron', day_of_week='mon,sat', hour=20, minute=20, timezone=tz_argentina)
    scheduler.start()

bot.run(TOKEN)
