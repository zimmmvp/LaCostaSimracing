import os
import random
import datetime
from ftplib import FTP
import discord

# --- LEER DATOS SEGUROS DESDE GITHUB SECRETS ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
CANAL_AVISOS_ID = int(os.environ.get("CANAL_AVISOS_ID"))

FTP_HOST = os.environ.get("FTP_HOST")
FTP_USER = os.environ.get("FTP_USER")
FTP_PASS = os.environ.get("FTP_PASS")
FTP_PORT = 21

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def elegir_aleatorio():
    with open('circuitos.txt', 'r', encoding='utf-8') as f:
        circuitos = [line.strip() for line in f if line.strip()]
    with open('autos.txt', 'r', encoding='utf-8') as f:
        autos = [line.strip() for line in f if line.strip()]
    return random.choice(circuitos), random.choice(autos)

def actualizar_servidor_ftp(circuito, auto):
    try:
        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        
        # Descargamos el archivo de configuración actual
        with open('server_cfg.ini', 'wb') as f:
            ftp.retrbinary('RETR cfg/server_cfg.ini', f.write)
            
        # Modificamos el circuito localmente
        with open('server_cfg.ini', 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        with open('server_cfg.ini', 'w', encoding='utf-8') as f:
            for linea in lineas:
                if linea.startswith('TRACK='):
                    f.write(f'TRACK={circuito}\n')
                elif linea.startswith('CONFIG_TRACK='):
                    f.write('CONFIG_TRACK=\n')
                else:
                    f.write(linea)
                    
        # Volvemos a subir el archivo modificado
        with open('server_cfg.ini', 'rb') as f:
            ftp.storbinary('STOR cfg/server_cfg.ini', f)
            
        ftp.quit()
        print("¡Servidor actualizado por FTP con éxito!")
    except Exception as e:
        print(f"Error al actualizar por FTP: {e}")

@client.event
async def on_ready():
    print(f'Bot ejecutándose en la nube de GitHub Actions...')
    
    # 1. Elegir circuito y auto
    circuito, auto = elegir_aleatorio()
    
    # 2. Actualizar el servidor de Assetto Corsa por FTP
    actualizar_servidor_ftp(circuito, auto)
    
    # 3. Mandar el aviso a Discord
    canal = client.get_channel(CANAL_AVISOS_ID)
    if canal:
        embed = discord.Embed(
            title="🏁 ¡NUEVA ROTACIÓN DIARIA EN COSTA SIM RACING! 🏁",
            description="El sistema ha seleccionado al azar los nuevos retos para las próximas 24 horas.",
            color=discord.Color.green()
        )
        embed.add_field(name="📍 Circuito", value=f"`{circuito}`", inline=False)
        embed.add_field(name="🏎️ Auto Asignado", value=f"`{auto}`", inline=False)
        embed.set_footer(text="Actualización automática diaria | Costa Sim Racing")
        
        await canal.send(embed=embed)
    
    # Cerramos el bot una vez que cumple su tarea en GitHub Actions
    await client.close()

client.run(DISCORD_TOKEN)
