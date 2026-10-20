import os
import random
import datetime
import discord
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
        
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("¡Conectado por SFTP con éxito!")
        
        # 1. ACTUALIZAR CIRCUITO EN server_cfg.ini
        ruta_cfg = 'cfg/server_cfg.ini'
        local_cfg = 'server_cfg.ini'
        
        sftp.get(ruta_cfg, local_cfg)
        
        with open(local_cfg, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        with open(local_cfg, 'w', encoding='utf-8') as f:
            for linea in lineas:
                if linea.startswith('TRACK='):
                    f.write(f'TRACK={circuito}\n')
                elif linea.startswith('CONFIG_TRACK='):
                    f.write('CONFIG_TRACK=\n')
                else:
                    f.write(linea)
                    
        sftp.put(local_cfg, ruta_cfg)
        print("¡Circuito actualizado en server_cfg.ini con éxito!")

        # 2. ACTUALIZAR AUTOS EN entry_list.ini
        ruta_entry = 'cfg/entry_list.ini'
        local_entry = 'entry_list.ini'
        
        sftp.get(ruta_entry, local_entry)
        
        with open(local_entry, 'r', encoding='utf-8') as f:
            lineas_entry = f.readlines()
            
        with open(local_entry, 'w', encoding='utf-8') as f:
            for linea in lineas_entry:
                # Reemplazamos el MODEL en cada slot de la grilla
                if linea.startswith('MODEL='):
                    f.write(f'MODEL={auto}\n')
                else:
                    f.write(linea)
                    
        sftp.put(local_entry, ruta_entry)
        print("¡Grilla de autos actualizada en entry_list.ini con éxito!")
        
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
