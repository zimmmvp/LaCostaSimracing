import os
import random
import datetime
from ftplib import FTP
import discord

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
CANAL_AVISOS_ID = int(os.environ.get("CANAL_AVISOS_ID"))

FTP_HOST = os.environ.get("FTP_HOST")
FTP_USER = os.environ.get("FTP_USER")
FTP_PASS = os.environ.get("FTP_PASS")
FTP_PORT = 21

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def elegir_aleatorio():
    # Asegurarnos de leer bien los archivos de texto
    if not os.path.exists('circuitos.txt') or not os.path.exists('autos.txt'):
        raise FileNotFoundError("No se encuentran los archivos circuitos.txt o autos.txt en el repositorio.")

    with open('circuitos.txt', 'r', encoding='utf-8') as f:
        circuitos = [line.strip() for line in f if line.strip()]
        
    with open('autos.txt', 'r', encoding='utf-8') as f:
        autos = [line.strip() for line in f if line.strip()]

    if not circuitos or not autos:
        raise ValueError("¡Atención! Uno de los archivos (circuitos.txt o autos.txt) está vacío.")

    return random.choice(circuitos), random.choice(autos)

def actualizar_servidor_ftp(circuito, auto):
    try:
        ftp = FTP()
        print(f"Conectando a FTP: {FTP_HOST}...")
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        print("¡Conectado al FTP con éxito!")
        
        # Probamos descargar el archivo desde la carpeta cfg/
        nombre_archivo = 'server_cfg.ini'
        try:
            ftp.cwd('cfg')
            print("Entró a la carpeta cfg/")
        except Exception:
            print("No se pudo entrar a la carpeta cfg/, intentando en la raíz...")
            
        with open(nombre_archivo, 'wb') as f:
            ftp.retrbinary(f'RETR {nombre_archivo}', f.write)
            
        # Modificamos el archivo localmente
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            for linea in lineas:
                if linea.startswith('TRACK='):
                    f.write(f'TRACK={circuito}\n')
                elif linea.startswith('CONFIG_TRACK='):
                    f.write('CONFIG_TRACK=\n')
                else:
                    f.write(linea)
                    
        # Volvemos a subir el archivo modificado
        with open(nombre_archivo, 'rb') as f:
            ftp.storbinary(f'STOR {nombre_archivo}', f)
            
        ftp.quit()
        print("¡Servidor actualizado y subido por FTP con éxito!")
    except Exception as e:
        print(f"ERROR CRÍTICO EN FTP: {e}")

@client.event
async def on_ready():
    print(f'Bot ejecutándose en la nube de GitHub Actions...')
    
    circuito, auto = elegir_aleatorio()
    actualizar_servidor_ftp(circuito, auto)
    
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
