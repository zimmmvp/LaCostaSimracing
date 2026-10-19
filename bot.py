import os
import random
import datetime
import pytz
import discord
from discord.ext import tasks
from ftplib import FTP

# --- CONFIGURACIÓN ---
DISCORD_TOKEN = "PEGAR_AQUI_TU_TOKEN_DE_DISCORD"
CANAL_AVISOS_ID = 123456789012345678  # Reemplaza con el ID numérico de tu canal de Discord

# Datos de tu FTP (te los da tu proveedor de hosting de Assetto Corsa)
FTP_HOST = "ftp.tu-servidor.com"
FTP_USER = "tu_usuario_ftp"
FTP_PASS = "tu_contraseña_ftp"
FTP_PORT = 21  # Generalmente es 21

# Zona horaria
TZ = pytz.timezone('America/Argentina/Buenos_Aires')

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def elegir_aleatorio():
    # Lee circuitos
    with open('circuitos.txt', 'r', encoding='utf-8') as f:
        circuitos = [line.strip() for line in f if line.strip()]
    # Lee autos
    with open('autos.txt', 'r', encoding='utf-8') as f:
        autos = [line.strip() for line in f if line.strip()]
        
    return random.choice(circuitos), random.choice(autos)

def actualizar_servidor_ftp(circuito, auto):
    try:
        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        
        # Nota: Dependiendo del hosting, el server_cfg.ini suele estar en la raíz o en una carpeta cfg/
        # Descargamos el archivo de configuración actual
        with open('server_cfg.ini', 'wb') as f:
            ftp.retrbinary('RETR cfg/server_cfg.ini', f.write) # Cambiar la ruta si tu hosting usa otra
            
        # Modificamos el archivo localmente
        with open('server_cfg.ini', 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        with open('server_cfg.ini', 'w', encoding='utf-8') as f:
            for linea in lineas:
                if linea.startswith('TRACK='):
                    f.write(f'TRACK={circuito}\n')
                elif linea.startswith('CONFIG_TRACK='):
                    f.write('CONFIG_TRACK=\n') # Por si usa variante vacía
                elif 'MODEL=' in linea: # Para asegurar el auto en la entry list o config principal
                    # Depende de cómo estructures tu entry_list.ini, pero por ahora actualizamos el cfg principal
                    f.write(linea)
                else:
                    f.write(linea)
                    
        # Volvemos a subir el archivo modificado por FTP
        with open('server_cfg.ini', 'rb') as f:
            ftp.storbinary('STOR cfg/server_cfg.ini', f)
            
        ftp.quit()
        print("¡Servidor actualizado por FTP con éxito!")
    except Exception as e:
        print(f"Error al actualizar por FTP: {e}")

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    rotacion_diaria.start()

@tasks.loop(time=datetime.time(hour=5, minute=0, tzinfo=TZ))
async def rotacion_diaria():
    circuito, auto = elegir_aleatorio()
    
    # Actualizar servidor de Assetto Corsa vía FTP
    actualizar_servidor_ftp(circuito, auto)
    
    # Mandar aviso a Discord
    canal = client.get_channel(CANAL_AVISOS_ID)
    if canal:
        embed = discord.Embed(
            title="🏁 ¡NUEVA ROTACIÓN DIARIA EN COSTA SIM RACING! 🏁",
            description="El sistema ha seleccionado al azar los nuevos retos para las próximas 24 horas.",
            color=discord.Color.green()
        )
        embed.add_field(name="📍 Circuito", value=f"`{circuito}`", inline=False)
        embed.add_field(name="🏎️ Auto Asignado", value=f"`{auto}`", inline=False)
        embed.set_footer(text="Actualización automática de las 05:00 AM | Costa Sim Racing")
        
        await canal.send(embed=embed)

client.run(DISCORD_TOKEN)