import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time, timedelta
import pytz
from flask import Flask
from threading import Thread

# --- Web server básico para keep-alive (UptimeRobot) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot recordatorio activo 🕒"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --------------------------------------------------------

# Enlace de invitación del bot:
# https://discord.com/oauth2/authorize?client_id=1380597605754605801&permissions=142336&integration_type=0&scope=bot

load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1379477200298053784

intents = discord.Intents.default()
intents.message_content = True
allowed_mentions = discord.AllowedMentions(roles=True)

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
    return dt.strftime("%H:%M %Z")

def get_event_message(event):
    if event == "guerra":
        return ("¡GUERREROS! Les recordamos que mañana es la 💥GUERRA TERRITORIAL💥."
                " No olviden marcar el bot, subir su barracón y conectarse 30 minutos antes para revisar la Micro y la Macro. 🔥⚔️LA VICTORIA SERÁ NUESTRA🔥⚔️.")
    elif event == "entrenamiento":
        return ("¡ATENCIÓN GUERREROS! Mañana tenemos 💥ENTRENAMIENTO💥."
                " No olviden marcar el bot, subir su barracón y conectarse 30 minutos antes para revisar la Micro y la Macro. 🔥⚔️LA VICTORIA SERÁ NUESTRA🔥⚔️.")
    else:
        return None

def get_event_datetime(event_date):
    return tz_argentina.localize(datetime.combine(event_date, time(22, 0)))

def get_all_times(event_date):
    dt_arg = get_event_datetime(event_date)
    times = {
        "México": format_time(dt_arg.astimezone(tz_mx)),
        "Perú": format_time(dt_arg.astimezone(tz_peru)),
        "Colombia": format_time(dt_arg.astimezone(tz_col)),
        "Venezuela": format_time(dt_arg.astimezone(tz_ven)),
        "Chile": format_time(dt_arg.astimezone(tz_chile)),
        "Argentina": format_time(dt_arg.astimezone(tz_argentina)),
        "Brasil": format_time(dt_arg.astimezone(tz_brasil)),
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

    guild = channel.guild
    miembros_rol = discord.utils.find(lambda r: r.name.lower() == "miembros", guild.roles)
    mention_rol = miembros_rol.mention if miembros_rol else "@miembros"

    ahora_arg = datetime.now(tz_argentina)
    event_date = None

    if current_event == "guerra":
        manana = ahora_arg + timedelta(days=1)
        if manana.weekday() in [1, 5]:
            event_date = manana.date()
        else:
            return
    elif current_event == "entrenamiento":
        manana = ahora_arg + timedelta(days=1)
        event_date = manana.date()

    if event_date is None:
        return

    if last_reminder_message_id:
        try:
            msg = await channel.fetch_message(last_reminder_message_id)
            await msg.delete()
        except Exception as e:
            print(f"No se pudo borrar el mensaje anterior: {e}")

    mensaje = f"{mention_rol} " + get_event_message(current_event)
    horarios = get_all_times(event_date)
    horarios_str = "\n".join([f"**{pais}:** {hora}" for pais, hora in horarios.items()])
    texto_final = f"{mensaje}\n\n🕒 Horarios de inicio según países:\n{horarios_str}"

    msg = await channel.send(texto_final)
    last_reminder_message_id = msg.id
    last_event_date = event_date

    event_dt = get_event_datetime(event_date)
    print(f"🗑️ Mensaje programado para borrarse el {event_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    scheduler.add_job(delete_reminder, 'date', run_date=event_dt, args=[CHANNEL_ID, msg.id])

async def delete_reminder(channel_id, message_id):
    try:
        channel = await bot.fetch_channel(channel_id)
        msg = await channel.fetch_message(message_id)
        await msg.delete()
        print(f"✅ Mensaje {message_id} borrado correctamente.")
    except discord.NotFound:
        print(f"⚠️ El mensaje {message_id} ya no existe o fue eliminado.")
    except discord.Forbidden:
        print(f"❌ Permisos insuficientes para borrar el mensaje {message_id}.")
    except discord.HTTPException as e:
        print(f"❌ Error de Discord al borrar el mensaje {message_id}: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

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

    miembros_rol = discord.utils.find(lambda r: r.name.lower() == "miembros", ctx.guild.roles)
    mention_rol = miembros_rol.mention if miembros_rol else "@miembros"

    event_date = datetime.now(tz_argentina).date() + timedelta(days=1)
    mensaje = f"{mention_rol} " + get_event_message(current_event)
    horarios = get_all_times(event_date)
    horarios_str = "\n".join([f"**{pais}:** {hora}" for pais, hora in horarios.items()])
    texto_final = f"{mensaje}\n\n🕒 Horarios de inicio según países:\n{horarios_str}"
    await ctx.send(texto_final)

@bot.command()
async def borrar(ctx):
    msg = await ctx.send("Este mensaje se autodestruirá en 10 segundos...")
    scheduler.add_job(delete_reminder, 'date',
                      run_date=datetime.now(tz_argentina) + timedelta(seconds=10),
                      args=[ctx.channel.id, msg.id])

@bot.command()
async def probarhoy(ctx):
    canal = bot.get_channel(CHANNEL_ID)
    if canal is None:
        await ctx.send("No se encontró el canal.")
        return

    if current_event is None:
        await ctx.send("❌ No hay evento configurado. Usa !guerra o !entrenamiento primero.")
        return

    ahora = datetime.now(tz_argentina)
    envio = ahora.replace(hour=23, minute=45, second=0, microsecond=0)
    borrado = ahora.replace(hour=23, minute=50, second=0, microsecond=0)

    if envio < ahora:
        await ctx.send("⚠️ Ya pasaron las 23:45 de hoy. Espera a mañana o ajusta la hora.")
        return

    async def enviar_y_borrar():
        miembros_rol = discord.utils.find(lambda r: r.name.lower() == "miembros", canal.guild.roles)
        mention_rol = miembros_rol.mention if miembros_rol else "@miembros"

        mensaje_texto = f"{mention_rol} " + get_event_message(current_event)
        horarios = get_all_times(envio.date())
        horarios_str = "\n".join([f"**{pais}:** {hora}" for pais, hora in horarios.items()])
        texto_final = f"{mensaje_texto}\n\n🕒 Horarios de inicio según países:\n{horarios_str}"

        mensaje = await canal.send(texto_final)
        print(f"✅ Mensaje de prueba enviado.")
        scheduler.add_job(delete_reminder, 'date', run_date=borrado, args=[CHANNEL_ID, mensaje.id])

    scheduler.add_job(enviar_y_borrar, 'date', run_date=envio)
    await ctx.send(f"✅ Mensaje de prueba programado para las {envio.strftime('%H:%M')} y se borrará a las {borrado.strftime('%H:%M')} (hora Argentina).")

@bot.event
async def on_ready():
    print(f'🤖 Bot listo! Conectado como {bot.user}')
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="sus partidas")
    )
    scheduler.remove_all_jobs()
    scheduler.add_job(send_reminder, 'cron', day_of_week='mon,fri', hour=17, minute=0, timezone=tz_argentina)
    scheduler.start()

# 🔁 Inicia keep-alive y corre el bot
keep_alive()
bot.run(TOKEN)
