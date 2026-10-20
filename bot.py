import os
import random
import json
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

def elegir_combinacion():
    if not os.path.exists('categorias.json'):
        raise FileNotFoundError("No se encuentra el archivo categorias.json en el repositorio.")

    with open('categorias.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    circuitos = data.get("circuitos", [])
    categorias = data.get("categorias", [])

    if not circuitos or not categorias:
        raise ValueError("El archivo categorias.json está incompleto o vacío.")

    circuito_elegido = random.choice(circuitos)
    categoria_elegida = random.choice(categorias)

    return circuito_elegido, categoria_elegida

def actualizar_servidor_sftp(circuito, categoria):
    try:
        print(f"Conectando por SFTP a {SFTP_HOST}:{SFTP_PORT}...")
        
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("¡Conectado por SFTP con éxito!")
        
        # Obtenemos la lista de autos definidos en la categoría y los unimos con ';'
        lista_cars = categoria.get("cars", ["bmw_m3_e30"])
        cars_string = ";".join(lista_cars)
        slots = categoria.get("slots", [])
        
        # 1. ACTUALIZAR CIRCUITO Y CARS EN server_cfg.ini
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
                elif linea.startswith('CARS='):
                    # Asigna todos los modelos separados por punto y coma para el servidor
                    f.write(f'CARS={cars_string}\n')
                else:
                    f.write(linea)
                    
        sftp.put(local_cfg, ruta_cfg)
        print(f"¡Circuito ({circuito}) y Cars ({cars_string}) actualizados en server_cfg.ini con éxito!")

        # 2. GENERAR Y ACTUALIZAR EL entry_list.ini
        ruta_entry = 'cfg/entry_list.ini'
        
        contenido_entry = ""
        for index, auto in enumerate(slots):
            contenido_entry += f"[CAR_{index}]\n"
            contenido_entry += f"MODEL={auto['model']}\n"
            contenido_entry += f"SKIN={auto['skin']}\n"
            contenido_entry += "SPECTATOR_MODE=0\n"
            contenido_entry += "DRIVERNAME=\n"
            contenido_entry += "TEAM=\n"
            contenido_entry += "GUID=\n"
            contenido_entry += "BALLAST=0\n\n"

        local_entry = 'entry_list.ini'
        with open(local_entry, 'w', encoding='utf-8') as f:
            f.write(contenido_entry)
            
        sftp.put(local_entry, ruta_entry)
        print(f"¡Grilla de la categoría '{categoria['nombre']}' actualizada en entry_list.ini con éxito!")
        
        sftp.close()
        transport.close()
    except Exception as e:
        print(f"ERROR CRÍTICO EN SFTP: {e}")

@client.event
async def on_ready():
    print(f'Bot ejecutándose en la nube de GitHub Actions...')
    
    circuito, categoria = elegir_combinacion()
    actualizar_servidor_sftp(circuito, categoria)
    
    canal = client.get_channel(CANAL_AVISOS_ID)
    if canal:
        embed = discord.Embed(
            title="🏁 ¡NUEVA CATEGORÍA Y ROTACIÓN DIARIA! 🏁",
            description="El sistema ha seleccionado una nueva categoría de vehículos y circuito para las próximas 24 horas.",
            color=discord.Color.green()
        )
        embed.add_field(name="🏆 Categoría Asignada", value=f"`{categoria['nombre']}`", inline=False)
        embed.add_field(name="📍 Circuito", value=f"`{circuito}`", inline=False)
        embed.set_footer(text="Actualización automática diaria | Costa Sim Racing")
        
        await canal.send(embed=embed)
    
    await client.close()

client.run(DISCORD_TOKEN)
