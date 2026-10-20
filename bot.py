import os
import random
import datetime
import discord
from ftplib import FTP
import paramiko

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
CANAL_AVISOS_ID = int(os.environ.get("CANAL_AVISOS_ID"))

SFTP_HOST = os.environ.get("FTP_HOST")
SFTP_USER = os.environ.get("FTP_USER")
SFTP_PASS = os.environ.get("FTP_PASS")
SFTP_PORT = 2022  # Puerto SFTP de Minehost

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def elegir_aleatorio():
    if not os.path.exists('circuitos.txt') or not os.path.exists('autos.txt'):
        raise FileNotFoundError("No se encuentran los archivos circuitos.txt o autos.txt")

    with open('circuitos.txt', 'r', encoding='utf-8') as f:
        circuitos = [line.strip() for line in f if line.strip()]
        
    with open('autos.txt', 'r', encoding='utf-8') as f:
        autos = [line.strip() for line in f if line.strip()]

    if not circuitos or not autos:
        raise ValueError("Uno de los archivos de texto está vacío.")

    return random.choice(circuitos), random.choice(autos)

def actualizar_servidor_sftp(circuito, auto):
    try:
        print(f"Conectando por SFTP a {SFTP_HOST}:{SFTP_PORT}...")
        
        # Conexión SSH / SFTP
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print("¡Conectado por SFTP con éxito!")
        
        # Ruta remota del archivo en Minehost (dentro de cfg/)
        ruta_remota = 'cfg/server_cfg.ini'
        archivo_local = 'server_cfg.ini'
        
        # Descargar archivo del servidor
        sftp.get(ruta_remota, archivo_local)
        print("Archivo de configuración descargado.")
        
        # Modificar localmente
        with open(archivo_local, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        with open(archivo_local, 'w', encoding='utf-8') as f:
            for linea in lineas:
                if linea.startswith('TRACK='):
                    f.write(f'TRACK={circuito}\n')
                elif linea.startswith('CONFIG_TRACK='):
                    f.write('CONFIG_TRACK=\n')
                else:
                    f.write(linea)
                    
        # Subir el archivo modificado de vuelta al servidor
        sftp.put(archivo_local, ruta_remota)
        print("¡Archivo modificado y subido al servidor con éxito!")
        
        sftp.close()
        transport.close()
    except Exception as e:
        print(f"ERROR CRÍTICO EN SFTP: {e}")

@client.event
async def on_ready():
    print(f'Bot ejecutándose en la nube de GitHub Actions...')
    
    circuito, auto = elegir_aleatorio()
    actualizar_servidor_sftp(circuito, auto)
    
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
    
    await client.close()

client.run(DISCORD_TOKEN)
