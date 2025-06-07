import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
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

# Evento actual a recordar ('guerra' o 'entrenamiento')
current_event = None

# Horarios y zonas horarias
tz_argentina = pytz.timezone("America/Argentina/Buenos_Aires")
tz_mx = pytz.timezone("America/Mexico_City")
tz_peru = pytz.timezone("America/Lima")
tz_col = pytz.timezone("America/Bogota")
tz_ven = pytz.timezone("America/Caracas")
tz_chile = pytz.timezone("America/Santiago")
tz_brasil = pytz.timezone("America/Sao_Paulo")
tz_esp = pytz.timezone("Europe/Madrid")

def format_time(dt):
    return dt.strftime("%H:%M")

def get_event_message(event):
    if event == "guerra":
        return ("@everyone Guerreros, mañana es la 💥GUERRA TERRITORIAL💥 Demuestren su fuerza, estrategia y honor en el campo de batalla. "
                "NO OLVIDEN MARCAR EL BOT. 🔥⚔️La victoria será nuestra🔥⚔️.")
    elif event == "entrenamiento":
        return ("@everyone Guerreros, es nuestro deber seguir mejorando, así que los invitamos cordialmente a un 💥ENTRENAMIENTO💥 "
                "La excelencia no es un acto, sino un hábito. NO OLVIDEN MARCAR EL BOT.")
    else:
        return None

def get_event_datetime(event_date):
    # El evento empieza a las 22:00 hora Argentina
    dt_arg = tz_argentina.localize(datetime.combine(event_date, time(22, 0)))
    return dt_arg

def get_all_times(event_date):
    dt_arg = get_event_datetime(event_date)
    times = {
        "Argentina": format_time(dt_arg.astimezone(tz_argentina)) + " (UTC-3)",
        "México": format_time(dt_arg.astimezone(tz_mx)) + " (UTC-5/-6 dependiendo horario)",
        "Perú": format_time(dt_arg.astimezone(tz_peru)) + " (UTC-5)",
        "Colombia": format_time(dt_arg.astimezone(tz_col)) + " (UTC-5)",
        "Venezuela": format_time(dt_arg.astimezone(tz_ven)) + " (UTC-4)",
        "Chile": format_time(dt_arg.astimezone(tz_chile)) + " (UTC-3/-4 dependiendo horario)",
        "Brasil": format_time(dt_arg.astimezone(tz_brasil)) + " (UTC-3)",
        "España": format_time(dt_arg.astimezone(tz_esp)) + " (UTC+1/+2 dependiendo horario)",
    }
    return times

async def send_reminder():
    if current_event is None:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("No se encontró el canal")
        return

    # El recordatorio es el día antes del evento, a las 17:00 Argentina
    ahora_arg = datetime.now(tz_argentina)
    # Calcular fecha del evento dependiendo del evento y día actual:
    # Para guerra: eventos martes y sábados (hora Argentina)
    # Recordatorios lunes y viernes 17:00

    # La función solo envía cuando es el día correcto para el evento seleccionado, pero el scheduler se encarga de llamar este método solo los lunes y viernes.

    event_date = None
    if current_event == "guerra":
        # El evento es mañana si hoy es lunes o viernes y mañana es martes o sábado
        manana = ahora_arg + timedelta(days=1)
        if manana.weekday() in [1, 5]:  # martes=1, sábado=5
            event_date = manana.date()
        else:
            return  # no enviar
    elif current_event == "entrenamiento":
        # El entrenamiento puede ser cualquier día, asumiremos que es todos los días.
        manana = ahora_arg + timedelta(days=1)
        event_date = manana.date()

    if event_date is None:
        return

    mensaje = get_event_message(current_event)
    horarios = get_all_times(event_date)

    horarios_str = "\n".join([f"**{pais}:** {hora}" for pais, hora in horarios.items()])

    texto_final = f"{mensaje}\n\n🕒 Horarios de inicio según países:\n{horarios_str}"

    await channel.send(texto_final)


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
    mensaje = get_event_message(current_event)
    horarios = get_all_times(event_date)
    horarios_str = "\n".join([f"**{pais}:** {hora}" for pais, hora in horarios.items()])
    texto_final = f"{mensaje}\n\n🕒 Horarios de inicio según países:\n{horarios_str}"
    await ctx.send(texto_final)

@bot.event
async def on_ready():
    print(f'Bot listo! Conectado como {bot.user}')
    # Programar el recordatorio automático a las 17:00 de Argentina los lunes y viernes
    scheduler.remove_all_jobs()

    # Scheduler para recordatorios lunes y viernes 17:00 hora Argentina
    # Usamos cron: minute hour day_of_month month day_of_week
    # día de la semana: lunes=0, viernes=4
    scheduler.add_job(send_reminder, 'cron', day_of_week='mon,fri', hour=17, minute=0, timezone=tz_argentina)
    scheduler.start()

bot.run(TOKEN)
