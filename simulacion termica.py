import time
import requests
import pyvjoy
import ctypes
import threading
import json
import os
import socket
import sys
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from http.server import HTTPServer, BaseHTTPRequestHandler

# 🛑 PROTECCIÓN PARA PYINSTALLER (--noconsole)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# Ruta absoluta robusta para script de Python y archivo .exe portable
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
CONFIG_FILE = os.path.join(script_dir, "config_frenos.json")

def cargar_config_disco():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def guardar_config_disco(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception:
        pass

# ==========================================
# DICCIONARIO DE IDIOMAS (ESPAÑOL / ENGLISH)
# ==========================================
TEXTOS = {
    "es": {
        "cfg_title": "Configuración de simulación térmica ATS by Flacoo x Gemini",
        "cfg_header": "⚙️ CONFIGURACIÓN DE SIMULACIÓN TÉRMICA ATS BY FLACOO X GEMINI",
        "lang_label": "Idioma / Language:",
        "device_q": "¿Qué dispositivo vas a usar?",
        "dev_options": ["Volante con Pedales", "Mando / Control (Gamepad)"],
        "select_id": "Selecciona el ID de tu Mando / Volante:",
        "inv_acel": "🔄 Invertir Eje Acelerador (Recomendado en Pedales)",
        "diag_title": "🔍 Comprobación de Controles en Tiempo Real",
        "wheel": "Volante:",
        "throttle": "Acelerador:",
        "brake": "Freno:",
        "wait_ctrl": "Mueve tu control/volante para comprobar la entrada",
        "heat_lbl": "Sensibilidad Calor (Izquierda: Lento | Derecha: Rápido):",
        "cool_lbl": "Velocidad Enfriamiento (Izquierda: Lento | Derecha: Rápido):",
        "reset_cal": "🔄 Restablecer Calibración Realista",
        "start_sim": "🚀 INICIAR SIMULACIÓN",
        
        "heat_ext": "🔥 Calentamiento Extremo (Se queman al roce)",
        "heat_rap": "⚡ Calentamiento Rápido (Carga pesada crítica)",
        "heat_rea": "🚛 Realista (Equilibrado / Recomendado)",
        "heat_len": "🧊 Calentamiento Lento (Mucha durabilidad)",
        
        "cool_rap": "❄️ Enfriamiento Rápido (Instantáneo al soltar)",
        "cool_nor": "⚖️ Enfriamiento Normal (Realista / Recomendado)",
        "cool_len": "🌋 Enfriamiento Lento (Retienen calor en bajadas)",

        "menu_server": "Servidor",
        "menu_tray": "Minimizar a la Bandeja",
        "menu_exit": "Salir del Programa",
        "menu_tools": "Herramientas",
        "menu_settings": "⚙️ Configuración & Sensibilidad",
        "menu_diag": "🔍 Comprobación de Controles (Diagnóstico)",
        "menu_lang": "🌐 Idioma / Language",
        "menu_help": "Ayuda",
        "menu_credits": "⭐ Créditos & Agradecimientos (Funbit)",
        
        "flow_title": "🔥 SIMULACIÓN TÉRMICA DE FRENOS ATS",
        "server_status": " Estado del Servidor ",
        "waiting_game": "🔴 Esperando conexión con el juego (ATS)...",
        "web_active": "🟢 Servidor Web Activo en http://",
        "links_frame": " Enlaces de Acceso (Móvil & OBS) ",
        "link_mob": "📱 Dashboard Móvil:",
        "link_top": "💻 OBS Overlay Superior:",
        "link_bot": "💻 OBS Overlay Inferior:",
        "footer_tray": "💡 Minimiza la ventana para enviarla a los íconos ocultos de Windows.",
        
        "tray_title": "ATS Thermal Brakes",
        "tray_msg": "Simulación térmica minimizada.\nDoble clic para restaurar la ventana."
    },
    "en": {
        "cfg_title": "ATS Thermal Simulation Configuration by Flacoo x Gemini",
        "cfg_header": "⚙️ ATS THERMAL SIMULATION CONFIGURATION BY FLACOO X GEMINI",
        "lang_label": "Language / Idioma:",
        "device_q": "Which device will you use?",
        "dev_options": ["Wheel with Pedals", "Gamepad / Controller"],
        "select_id": "Select your Controller / Wheel ID:",
        "inv_acel": "🔄 Invert Accelerator Axis (Recommended for Pedals)",
        "diag_title": "🔍 Real-Time Controls Diagnostics",
        "wheel": "Wheel:",
        "throttle": "Throttle:",
        "brake": "Brake:",
        "wait_ctrl": "Move your controller/wheel to test input",
        "heat_lbl": "Heating Sensitivity (Left: Slow | Right: Fast):",
        "cool_lbl": "Cooling Speed (Left: Slow | Right: Fast):",
        "reset_cal": "🔄 Reset Realistic Calibration",
        "start_sim": "🚀 START SIMULATION",
        
        "heat_ext": "🔥 Extreme Heating (Burn quickly on friction)",
        "heat_rap": "⚡ Fast Heating (Critical heavy load)",
        "heat_rea": "🚛 Realistic (Balanced / Recommended)",
        "heat_len": "🧊 Slow Heating (High durability)",
        
        "cool_rap": "❄️ Fast Cooling (Instant on release)",
        "cool_nor": "⚖️ Normal Cooling (Realistic / Recommended)",
        "cool_len": "🌋 Slow Cooling (Retain heat on downhills)",

        "menu_server": "Server",
        "menu_tray": "Minimize to Tray",
        "menu_exit": "Exit Program",
        "menu_tools": "Tools",
        "menu_settings": "⚙️ Configuration & Sensitivity",
        "menu_diag": "🔍 Controls Diagnostics",
        "menu_lang": "🌐 Language / Idioma",
        "menu_help": "Help",
        "menu_credits": "⭐ Credits & Acknowledgements (Funbit)",
        
        "flow_title": "🔥 ATS THERMAL BRAKES SIMULATION",
        "server_status": " Server Status ",
        "waiting_game": "🔴 Waiting for game connection (ATS)...",
        "web_active": "🟢 Web Server Active at http://",
        "links_frame": " Access Links (Mobile & OBS) ",
        "link_mob": "📱 Mobile Dashboard:",
        "link_top": "💻 OBS Top Overlay:",
        "link_bot": "💻 OBS Bottom Overlay:",
        "footer_tray": "💡 Minimize window to send it to Windows system tray.",
        
        "tray_title": "ATS Thermal Brakes",
        "tray_msg": "Thermal simulation minimized.\nDouble-click to restore window."
    }
}

# Intentar importar 'inputs' para mandos
try:
    from inputs import get_gamepad
    INPUTS_DISPONIBLE = True
except ImportError:
    INPUTS_DISPONIBLE = False

# Intentar importar pystray para la bandeja de sistema
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_DISPONIBLE = True
except ImportError:
    PYSTRAY_DISPONIBLE = False

# ==========================================
# DETECCIÓN Y CALIBRACIÓN DE DISPOSITIVOS
# ==========================================
class JOYINFOEX(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
        ("dwXpos", ctypes.c_ulong), ("dwYpos", ctypes.c_ulong),
        ("dwZpos", ctypes.c_ulong), ("dwRpos", ctypes.c_ulong),
        ("dwUpos", ctypes.c_ulong), ("dwVpos", ctypes.c_ulong),
        ("dwButtons", ctypes.c_ulong), ("dwButtonNumber", ctypes.c_ulong),
        ("dwPOV", ctypes.c_ulong), ("dwReserved1", ctypes.c_ulong),
        ("dwReserved2", ctypes.c_ulong),
    ]

def obtener_dispositivos_activos():
    dispositivos = []
    for joy_id in range(4):
        try:
            joy = JOYINFOEX()
            joy.dwSize = ctypes.sizeof(JOYINFOEX)
            joy.dwFlags = 0x000000FF
            res = ctypes.windll.winmm.joyGetPosEx(joy_id, ctypes.byref(joy))
            if res == 0:
                dispositivos.append((f"🎮 Dispositivo / Mando ID {joy_id}", joy_id))
        except Exception:
            pass
    if not dispositivos:
        dispositivos.append(("🎮 Volante Genérico (ID 0)", 0))
    return dispositivos

mando_volante = 0.5   
mando_acelerador = 0.0 
mando_freno = 0.0      

def hilo_lectura_mando():
    global mando_volante, mando_acelerador, mando_freno
    if not INPUTS_DISPONIBLE:
        return
    while True:
        try:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_X':
                    mando_volante = (float(event.state) + 32768.0) / 65535.0
                elif event.code == 'ABS_Z':
                    mando_freno = float(event.state) / 255.0
                elif event.code == 'ABS_RZ':
                    mando_acelerador = float(event.state) / 255.0
        except Exception:
            time.sleep(0.5)

if INPUTS_DISPONIBLE:
    threading.Thread(target=hilo_lectura_mando, daemon=True).start()

def leer_ejes_dispositivo(device_id, tipo_dispositivo, invertir_acel=False):
    if tipo_dispositivo == "mando":
        return mando_volante, mando_acelerador, mando_freno, 0
    else:
        try:
            joy = JOYINFOEX()
            joy.dwSize = ctypes.sizeof(JOYINFOEX)
            joy.dwFlags = 0x000000FF
            if ctypes.windll.winmm.joyGetPosEx(device_id, ctypes.byref(joy)) == 0:
                vol = float(joy.dwXpos) / 65535.0
                raw_acel = float(joy.dwYpos) / 65535.0
                
                # Calibración limpia y completa de pedales (0% a 100% real)
                if invertir_acel:
                    if raw_acel >= 0.45 and raw_acel <= 0.55:
                        acel = 0.0
                    elif raw_acel < 0.5:
                        acel = min(1.0, (0.5 - raw_acel) * 2.0)
                    else:
                        acel = 0.0
                else:
                    acel = raw_acel
                    
                freno = 1.0 - (float(joy.dwRpos) / 65535.0)
                return max(0.0, min(1.0, vol)), max(0.0, min(1.0, acel)), max(0.0, min(1.0, freno)), joy.dwButtons
        except Exception:
            pass
    return 0.5, 0.0, 0.0, 0

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ==========================================
# VARIABLES GLOBALES DE FÍSICA Y TELEMETRÍA
# ==========================================
velocidad_actual = 0.0
rpm_actual = 0.0
marcha_actual = "N"
combustible_litros = 0.0
combustible_capacidad = 909.0
temp_agua = 55.4
presion_aire = 114.4
freno_mano = False
juego_conectado = False
juego_pausado = False
timestamp_juego_anterior = None

camion_marca = "Kenworth"
camion_modelo = "W900"
motor_brake_on = False
retarder_step = 0
retarder_max = 0
cruise_control_on = False
cruise_control_speed = 0.0
speed_limit = 56.0
beacon_on = False
adblue_litros = 65.9

wear_engine = 0.0
wear_trans = 0.0
wear_chassis = 0.0
wear_wheels = 0.0
wear_trailer = 0.0

cargo_nombre = "Sin carga"
cargo_peso = 0.0
cargo_ingresos = 0
origen_ciudad = "--"
destino_ciudad = "--"
tiempo_restante_contrato_str = "--"
tiempo_sueño_str = "--"
distancia_restante_km = 0.0
tiempo_llegada_str = "--"

temp_frenos = 25.0
eficacia_global = 1.0
freno_vis_global = 0.0

def parsear_tiempo_iso(iso_str):
    try:
        if not iso_str: return "--"
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        dias = dt.day - 1
        horas = dt.hour + (dias * 24)
        minutos = dt.minute
        if horas > 0:
            return f"{horas} h {minutos} min"
        else:
            return f"{minutos} min"
    except Exception:
        return "--"

def consultar_telemetria():
    global velocidad_actual, rpm_actual, marcha_actual, combustible_litros, combustible_capacidad, temp_agua, presion_aire, freno_mano, juego_conectado, juego_pausado
    global camion_marca, camion_modelo, cargo_nombre, cargo_peso, cargo_ingresos, origen_ciudad, destino_ciudad, tiempo_restante_contrato_str, tiempo_sueño_str, distancia_restante_km, tiempo_llegada_str
    global motor_brake_on, retarder_step, retarder_max, cruise_control_on, cruise_control_speed, speed_limit, beacon_on, adblue_litros
    global wear_engine, wear_trans, wear_chassis, wear_wheels, wear_trailer, timestamp_juego_anterior, temp_frenos
    
    while True:
        try:
            response = requests.get("http://localhost:25555/api/ets2/telemetry", timeout=0.2)
            data = response.json()
            game_info = data.get("game", {})
            if game_info.get("connected", False):
                juego_conectado = True
                juego_pausado = game_info.get("paused", False)
                try:
                    time_str = game_info.get("time")
                    if time_str and isinstance(time_str, str):
                        dt_juego = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
                        if timestamp_juego_anterior is not None:
                            diferencia_tiempo = (dt_juego - timestamp_juego_anterior).total_seconds()
                            if diferencia_tiempo > 60.0:
                                saved_cfg = cargar_config_disco()
                                t_enf = saved_cfg.get("enf", 0.002)
                                tasa_efectiva = max(t_enf, 0.0001)
                                enfriamiento_masivo = diferencia_tiempo * tasa_efectiva * 15.0
                                temp_frenos = max(25.0, temp_frenos - enfriamiento_masivo)
                        timestamp_juego_anterior = dt_juego
                except Exception:
                    pass

                truck = data.get("truck", {})
                trailer = data.get("trailer", {})
                job = data.get("job", {})
                navigation = data.get("navigation", {})
                
                velocidad_actual = abs(truck.get("speed", 0.0))
                rpm_actual = truck.get("engineRpm", 0.0)
                if truck.get("make"): camion_marca = str(truck.get("make"))
                if truck.get("model"): camion_modelo = str(truck.get("model"))

                gear_val = truck.get("gear", 0)
                if gear_val == 0: marcha_actual = "N"
                elif gear_val < 0: marcha_actual = f"R{abs(gear_val)}"
                else: marcha_actual = str(gear_val)
                
                combustible_litros = truck.get("fuel", 0.0)
                combustible_capacidad = truck.get("fuelCapacity", 909.0)
                temp_agua = truck.get("waterTemperature", 55.4)
                presion_aire = truck.get("airPressure", 114.4)
                freno_mano = truck.get("parkBrakeOn", False)
                motor_brake_on = truck.get("motorBrakeOn", False)
                retarder_step = truck.get("retarderBrake", 0)
                retarder_max = truck.get("retarderStepCount", 0)
                cruise_control_on = truck.get("cruiseControlOn", False)
                cruise_control_speed = abs(truck.get("cruiseControlSpeed", 0.0))
                speed_limit = abs(navigation.get("speedLimit", 56.0))
                beacon_on = truck.get("lightsBeaconOn", False)
                adblue_litros = truck.get("adblue", 65.9)
                
                wear_engine = truck.get("wearEngine", 0.0) * 100.0
                wear_trans = truck.get("wearTransmission", 0.0) * 100.0
                wear_chassis = truck.get("wearChassis", 0.0) * 100.0
                wear_wheels = truck.get("wearWheels", 0.0) * 100.0
                wear_trailer = trailer.get("wear", 0.0) * 100.0
                
                t_name = trailer.get("name")
                cargo_nombre = str(t_name) if t_name and str(t_name).strip() != "" else "Sin carga / Remolque libre"
                t_mass = trailer.get("mass", 0.0)
                cargo_peso = (t_mass / 1000.0) if t_mass > 0 else 0.0

                ing = job.get("income", 0)
                if ing > 0: cargo_ingresos = ing
                src = job.get("sourceCity")
                if src and str(src).strip() != "": origen_ciudad = str(src)
                dst = job.get("destinationCity")
                if dst and str(dst).strip() != "": destino_ciudad = str(dst)
                
                rem_time_iso = job.get("remainingTime", "")
                if rem_time_iso: tiempo_restante_contrato_str = parsear_tiempo_iso(rem_time_iso)
                rest_time_iso = game_info.get("nextRestStopTime", "")
                if rest_time_iso: tiempo_sueño_str = parsear_tiempo_iso(rest_time_iso)
                dist_m = navigation.get("estimatedDistance", 0.0)
                if dist_m > 0: distancia_restante_km = dist_m / 1000.0
                est_time_iso = navigation.get("estimatedTime", "")
                if est_time_iso: tiempo_llegada_str = parsear_tiempo_iso(est_time_iso)
            else:
                juego_conectado = False
                juego_pausado = False
        except Exception:
            juego_conectado = False
            juego_pausado = False
        time.sleep(0.1)

threading.Thread(target=consultar_telemetria, daemon=True).start()

# ==========================================
# INICIALIZACIÓN DE VJOY Y FÍSICA
# ==========================================
vj = None
try:
    vj = pyvjoy.VJoyDevice(1)
except Exception as e:
    root_err = tk.Tk()
    root_err.withdraw()
    messagebox.showerror("Error de vJoy", f"No se pudo inicializar vJoy ID 1.\n\nAsegúrate de tener vJoy instalado y habilitado.\n\nDetalle: {e}")
    root_err.destroy()
    sys.exit()

def bucle_fisica_y_controles():
    global eficacia_global, freno_vis_global, temp_frenos
    while True:
        try:
            saved_cfg = cargar_config_disco()
            physical_id = saved_cfg.get("device_id", 0)
            tipo_disp = saved_cfg.get("tipo", "volante")
            invertir_acel = saved_cfg.get("invertir_acel", True)
            mult_calor = saved_cfg.get("calor", 0.078)
            tasa_enf = saved_cfg.get("enf", 0.002)

            volante, acelerador, freno_fisico, botones_mask = leer_ejes_dispositivo(physical_id, tipo_disp, invertir_acel)
            
            if tipo_disp != "mando" and vj:
                for i in range(8):
                    estado_boton = 1 if (botones_mask & (1 << i)) != 0 else 0
                    try: vj.set_button(i + 1, estado_boton)
                    except Exception: pass
                vj.set_axis(pyvjoy.HID_USAGE_X, int(volante * 32767))
                vj.set_axis(pyvjoy.HID_USAGE_Y, int(acelerador * 32767))

            if juego_conectado and vj:
                if not juego_pausado:
                    if freno_fisico > 0.05:
                        peso_camion_base = 8.5  
                        peso_total = peso_camion_base + cargo_peso
                        factor_peso = peso_total / 15.0
                        calor = freno_fisico * (velocidad_actual / 30.0) * mult_calor * factor_peso
                        temp_frenos += calor
                    else:
                        enfriamiento = ((tasa_enf * 20.0) * (velocidad_actual / 50.0) + tasa_enf) if velocidad_actual > 5.0 else tasa_enf
                        temp_frenos -= enfriamiento
                    temp_frenos = max(25.0, min(450.0, temp_frenos))

            if temp_frenos >= 450.0:
                eficacia = 0.0
            elif temp_frenos > 200.0:
                eficacia = max(0.0, 1.0 - ((temp_frenos - 200.0) / 250.0))
            else:
                eficacia = 1.0

            if vj:
                vj.set_axis(pyvjoy.HID_USAGE_Z, int(freno_fisico * 32767 * eficacia))

            eficacia_global = eficacia
            freno_vis_global = freno_fisico * 100.0
        except Exception:
            pass
        time.sleep(0.033)

threading.Thread(target=bucle_fisica_y_controles, daemon=True).start()

# ==========================================
# SERVIDOR WEB (MÓVIL & OBS)
# ==========================================
class MobileDashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>ATS Mobile Stream Dashboard</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <style>
                    * { box-sizing: border-box; }
                    body { background: #0b0b0e; color: #fff; font-family: 'Segoe UI', Arial, sans-serif; text-align: center; margin: 0; padding: 2px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; }
                    .container { max-width: 380px; width: 100%; margin: 0 auto; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
                    .nav-tabs { display: flex; gap: 2px; margin-bottom: 2px; }
                    .tab-btn { flex: 1; background: #16161f; border: 1px solid #00ffcc; color: #00ffcc; padding: 4px 0; font-size: 9px; font-weight: bold; border-radius: 5px; cursor: pointer; text-transform: uppercase; white-space: nowrap; overflow: hidden; }
                    .tab-btn.active { background: #00ffcc; color: #0b0b0e; }
                    .tab-content { display: none; flex-grow: 1; flex-direction: column; justify-content: space-around; }
                    .tab-content.active { display: flex; }
                    .card { background: #16161f; border: 1.5px solid #00ffcc; border-radius: 6px; padding: 4px; margin: 1px 0; box-shadow: 0 0 8px rgba(0,255,204,0.12); }
                    h2 { color: #00ffcc; margin: 1px 0; font-size: 9px; letter-spacing: 0.5px; text-transform: uppercase; }
                    .value { font-size: 20px; font-weight: bold; margin: 1px 0; }
                    .optimal { color: #00ff66; }
                    .danger { color: #ff3333; text-shadow: 0 0 6px #ff3333; }
                    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px; }
                    .cell { background: #111118; padding: 4px 2px; border-radius: 4px; text-align: center; border: 1px solid #222230; }
                    .cell-full { grid-column: span 2; padding: 3px; }
                    .label { font-size: 7.5px; color: #888899; text-transform: uppercase; display: block; margin-bottom: 1px; }
                    .data-val { font-size: 11.5px; font-weight: bold; color: #00ffcc; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="nav-tabs">
                        <button class="tab-btn active" id="btn-t1" onclick="switchTab(1)">📊 Telemetría</button>
                        <button class="tab-btn" id="btn-t2" onclick="switchTab(2)">📦 Trabajo</button>
                        <button class="tab-btn" id="btn-t3" onclick="switchTab(3)">🔧 Daños</button>
                    </div>

                    <div id="tab-1" class="tab-content active">
                        <div>
                            <h2>🔥 Temp. Frenos (Realista 450°C)</h2>
                            <div class="card">
                                <div id="m-temp" class="value optimal">25.0 °C</div>
                                <div id="m-estado" style="font-weight: bold; font-size: 9px;">SISTEMA ÓPTIMO</div>
                            </div>
                        </div>
                        <div>
                            <h2>🚛 Telemetría General</h2>
                            <div class="card">
                                <div class="grid">
                                    <div class="cell"><span class="label">Velocidad / Marcha</span><span class="data-val"><span id="m-vel">0</span> km/h | <span id="m-gear">1</span></span></div>
                                    <div class="cell"><span class="label">RPM Motor</span><span class="data-val" id="m-rpm">0</span></div>
                                    <div class="cell"><span class="label">Presión Aire</span><span class="data-val"><span id="m-aire">120</span> PSI</span></div>
                                    <div class="cell"><span class="label">Descanso / Baliza</span><span class="data-val"><span id="m-rest" style="color: #ffaa00;">--</span> | <span id="m-beacon">OFF</span></span></div>
                                    <div class="cell"><span class="label">Combustible</span><span class="data-val" id="m-comb">0 L</span></div>
                                    <div class="cell"><span class="label">Freno de Motor</span><span class="data-val" id="m-motor-brake">OFF</span></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="tab-2" class="tab-content">
                        <h2>📦 Información del Contrato</h2>
                        <div class="card">
                            <div class="grid">
                                <div class="cell cell-full"><span class="label">Mercancía (Carga)</span><span class="data-val" id="m-cargo-nombre" style="font-size: 12px; color: #ffaa00;">--</span></div>
                                <div class="cell"><span class="label">Peso Carga</span><span class="data-val"><span id="m-cargo-peso">0</span> t</span></div>
                                <div class="cell"><span class="label">Ingresos</span><span class="data-val" id="m-cargo-ingresos" style="color: #00ff66;">$0</span></div>
                                <div class="cell cell-full"><span class="label">Ruta (Origen ➔ Destino)</span><span class="data-val" style="font-size: 10px;"><span id="m-origen">--</span> ➔ <span id="m-destino">--</span></span></div>
                                <div class="cell"><span class="label">Km Faltantes</span><span class="data-val" id="m-distancia-km">0 km</span></div>
                                <div class="cell"><span class="label">ETA Llegada</span><span class="data-val" id="m-eta-llegada">--</span></div>
                            </div>
                        </div>
                    </div>

                    <div id="tab-3" class="tab-content">
                        <h2>🔧 Daños y Estado</h2>
                        <div class="card">
                            <div class="grid">
                                <div class="cell"><span class="label">Motor</span><span class="data-val" id="m-wear-eng">0.0%</span></div>
                                <div class="cell"><span class="label">Transmisión</span><span class="data-val" id="m-wear-tra">0.0%</span></div>
                                <div class="cell"><span class="label">Chasis</span><span class="data-val" id="m-wear-cha">0.0%</span></div>
                                <div class="cell"><span class="label">Neumáticos</span><span class="data-val" id="m-wear-whe">0.0%</span></div>
                                <div class="cell"><span class="label">Remolque</span><span class="data-val" id="m-wear-trl" style="color: #ffaa00;">0.0%</span></div>
                                <div class="cell"><span class="label">AdBlue</span><span class="data-val" id="m-adblue">0 L</span></div>
                            </div>
                        </div>
                    </div>
                </div>
                <script>
                    function switchTab(n) {
                        for(let i=1; i<=3; i++) {
                            document.getElementById('tab-'+i).classList.remove('active');
                            document.getElementById('btn-t'+i).classList.remove('active');
                        }
                        document.getElementById('tab-'+n).classList.add('active');
                        document.getElementById('btn-t'+n).classList.add('active');
                    }
                    setInterval(() => {
                        fetch('/data').then(res => res.json()).then(data => {
                            let tempEl = document.getElementById('m-temp');
                            tempEl.innerText = data.temp.toFixed(1) + " °C";
                            let estEl = document.getElementById('m-estado');
                            if(data.temp >= 450) {
                                tempEl.className = "value danger";
                                estEl.innerText = "🚨 ¡CRISTALIZACIÓN (450°C)!";
                            } else if(data.temp > 200) {
                                tempEl.className = "value danger";
                                estEl.innerText = "⚠️ ¡FADING SEVERO!";
                            } else {
                                tempEl.className = "value optimal";
                                estEl.innerText = "SISTEMA ÓPTIMO";
                            }
                            document.getElementById('m-vel').innerText = data.vel.toFixed(0);
                            document.getElementById('m-gear').innerText = data.gear;
                            document.getElementById('m-rpm').innerText = data.rpm.toFixed(0);
                            document.getElementById('m-aire').innerText = data.aire.toFixed(0);
                            document.getElementById('m-comb').innerText = data.comb.toFixed(0) + " L";
                            document.getElementById('m-rest').innerText = data.sueño;
                            let mbMob = document.getElementById('m-motor-brake');
                            if(data.mb_on) { mbMob.innerText = "ON"; mbMob.style.color = "#00ff66"; } else { mbMob.innerText = "OFF"; mbMob.style.color = "#00ffcc"; }
                            document.getElementById('m-cargo-nombre').innerText = data.cargo;
                            document.getElementById('m-cargo-peso').innerText = data.peso.toFixed(1);
                            document.getElementById('m-cargo-ingresos').innerText = "$" + data.ingresos.toLocaleString();
                            document.getElementById('m-origen').innerText = data.origen;
                            document.getElementById('m-destino').innerText = data.destino;
                            document.getElementById('m-distancia-km').innerText = data.dist_km.toFixed(1) + " km";
                            document.getElementById('m-eta-llegada').innerText = data.eta;
                            document.getElementById('m-wear-eng').innerText = data.w_eng.toFixed(1) + "%";
                            document.getElementById('m-wear-tra').innerText = data.w_tra.toFixed(1) + "%";
                            document.getElementById('m-wear-cha').innerText = data.w_cha.toFixed(1) + "%";
                            document.getElementById('m-wear-whe').innerText = data.w_whe.toFixed(1) + "%";
                            document.getElementById('m-wear-trl').innerText = data.w_trl.toFixed(1) + "%";
                            document.getElementById('m-adblue').innerText = data.adblue.toFixed(0) + " L";
                        });
                    }, 200);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
            
        elif self.path == '/obs_top':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_top = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>ATS Top OBS</title>
                <style>
                    * { box-sizing: border-box; }
                    body { background: transparent; color: #fff; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 4px; width: 100vw; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
                    .top-container { background: rgba(10, 12, 18, 0.99); border: 3px solid #3b82f6; border-radius: 14px; padding: 10px; box-shadow: 0 0 35px rgba(0,0,0,0.95); display: flex; flex-direction: column; gap: 6px; height: 100%; justify-content: space-between; width: 100%; }
                    .header-truck { text-align: center; color: #00ffcc; font-size: 22px; font-weight: 900; text-transform: uppercase; letter-spacing: 3px; border-bottom: 2px solid #1f2636; padding-bottom: 3px; text-shadow: 0 0 10px rgba(0,255,204,0.5); }
                    .main-row { display: flex; gap: 10px; align-items: stretch; justify-content: space-between; flex-grow: 1; }
                    .side-box-left { flex: 1; background: #121622; border: 2px solid #334155; border-radius: 12px; padding: 10px; display: flex; flex-direction: column; justify-content: space-around; text-align: center; }
                    .box-title { font-size: 16px; color: #94a3b8; text-transform: uppercase; font-weight: 800; border-bottom: 2px solid #1a202c; padding-bottom: 3px; letter-spacing: 1px; }
                    .vel-num { font-size: 58px; font-weight: 900; color: #fff; line-height: 1; text-shadow: 0 0 15px rgba(255,255,255,0.6); }
                    .gear-val { font-size: 36px; font-weight: 900; color: #ffaa00; text-shadow: 0 0 8px rgba(255,170,0,0.5); }
                    .brake-pod { flex: 1.5; background: #121622; border: 3px solid #00ffcc; border-radius: 14px; padding: 6px; text-align: center; position: relative; box-shadow: inset 0 0 25px rgba(0,0,0,0.9); display: flex; flex-direction: column; justify-content: center; align-items: center; }
                    .brake-num { font-size: 65px; font-weight: 900; color: #00ff66; line-height: 1; text-shadow: 0 0 18px rgba(0,255,102,0.7); }
                    .brake-lbl { font-size: 12px; color: #ffaa00; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }
                    .brake-status { font-size: 15px; font-weight: 900; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }
                    .side-box-right { flex: 1.3; background: #121622; border: 2px solid #334155; border-radius: 12px; padding: 10px; display: flex; flex-direction: column; justify-content: space-around; font-size: 16px; font-weight: 800; color: #ffffff; }
                    .sys-row { display: flex; justify-content: space-between; border-bottom: 1px solid #1a202c; padding-bottom: 3px; align-items: center; }
                    .sys-val { color: #aaa; font-size: 17px; font-weight: 900; }
                    
                    .retard-label { font-size: 16px; font-weight: 900; transition: color 0.2s ease; }
                    .retard-label.off { color: #ff3333; text-shadow: 0 0 8px rgba(255,51,51,0.6); }
                    .retard-label.on { color: #ffffff; text-shadow: 0 0 5px rgba(255,255,255,0.8); }
                    .retard-steps-container { display: flex; gap: 3px; align-items: center; }
                    .retard-btn { width: 22px; height: 22px; border-radius: 4px; background: #1a202c; border: 1px solid #334155; color: #556677; font-size: 11px; font-weight: 900; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease; }
                    .retard-btn.active { background: #00ff66; border-color: #00ff66; color: #0b0b0e; box-shadow: 0 0 10px rgba(0,255,102,0.8); }
                </style>
            </head>
            <body>
                <div class="top-container">
                    <div class="header-truck">🚛 <span id="top-truck">Kenworth W900</span></div>
                    <div class="main-row">
                        <div class="side-box-left">
                            <span class="box-title">⚡ Velocidad</span>
                            <div><span class="vel-num" id="top-vel">0</span><span style="font-size: 13px; color: #94a3b8; font-weight: 800;"> KM/H</span></div>
                            <div><span style="font-size: 12px; color: #94a3b8; display: block; font-weight: 800;">MARCHA</span><span class="gear-val" id="top-gear">N</span></div>
                        </div>
                        <div id="brake-container" class="brake-pod">
                            <span class="brake-lbl">🔥 TEMP. FRENOS (MÁX 450°C)</span>
                            <span class="brake-num" id="top-brake-temp">25.0°</span>
                            <span id="top-brake-status" class="brake-status" style="color: #00ff66;">SISTEMA ÓPTIMO</span>
                        </div>
                        <div class="side-box-right">
                            <span class="box-title">🕹️ Controles</span>
                            <div class="sys-row"><span>F. Motor:</span> <span id="top-mb" class="sys-val">OFF</span></div>
                            <div class="sys-row">
                                <span id="top-ret-lbl" class="retard-label off">Retard:</span> 
                                <div class="retard-steps-container">
                                    <div id="ret-b1" class="retard-btn">1</div>
                                    <div id="ret-b2" class="retard-btn">2</div>
                                    <div id="ret-b3" class="retard-btn">3</div>
                                    <div id="ret-b4" class="retard-btn">4</div>
                                    <div id="ret-b5" class="retard-btn">5</div>
                                </div>
                            </div>
                            <div class="sys-row"><span>Crucero:</span> <span id="top-cc" class="sys-val">OFF</span></div>
                            <div class="sys-row"><span>Balizas:</span> <span id="top-beacon" class="sys-val">OFF</span></div>
                        </div>
                    </div>
                </div>
                <script>
                    setInterval(() => {
                        fetch('/data').then(res => res.json()).then(data => {
                            document.getElementById('top-truck').innerText = data.marca + " " + data.modelo;
                            document.getElementById('top-vel').innerText = data.vel.toFixed(0);
                            document.getElementById('top-gear').innerText = data.gear;
                            let temp = data.temp;
                            let tempEl = document.getElementById('top-brake-temp');
                            let statusEl = document.getElementById('top-brake-status');
                            let containerEl = document.getElementById('brake-container');
                            tempEl.innerText = temp.toFixed(1) + "°";
                            if(temp >= 450) {
                                containerEl.style.borderColor = "#ff3333";
                                tempEl.style.color = "#ff3333";
                                statusEl.innerText = "🚨 ¡CRISTALIZACIÓN (450°C)!";
                                statusEl.style.color = "#ff3333";
                            } else if(temp > 200) {
                                containerEl.style.borderColor = "#ffaa00";
                                tempEl.style.color = "#ffaa00";
                                statusEl.innerText = "⚠️ FADING SEVERO";
                                statusEl.style.color = "#ffaa00";
                            } else {
                                containerEl.style.borderColor = "#00ffcc";
                                tempEl.style.color = "#00ff66";
                                statusEl.innerText = "SISTEMA ÓPTIMO";
                                statusEl.style.color = "#00ff66";
                            }
                            let mb = document.getElementById('top-mb');
                            if(data.mb_on) { mb.innerText = "ON"; mb.style.color = "#00ff66"; } else { mb.innerText = "OFF"; mb.style.color = "#888"; }
                            
                            let retLbl = document.getElementById('top-ret-lbl');
                            let retLevel = data.retarder || data.retarder_step || 0;

                            if (retLevel > 0) {
                                retLbl.className = "retard-label on";
                            } else {
                                retLbl.className = "retard-label off";
                            }

                            for (let i = 1; i <= 5; i++) {
                                 let btn = document.getElementById('ret-b' + i);
                                 if (i === retLevel) {
                                     btn.className = "retard-btn active";
                                 } else {
                                     btn.className = "retard-btn";
                                 }
                             }

                            let cc = document.getElementById('top-cc');
                            if(data.cc_on) { cc.innerText = data.cc_speed.toFixed(0) + " km/h"; cc.style.color = "#00ff66"; } else { cc.innerText = "OFF"; cc.style.color = "#888"; }
                            let bc = document.getElementById('top-beacon');
                            if(data.beacon) { bc.innerText = "ON"; bc.style.color = "#ffaa00"; } else { bc.innerText = "OFF"; bc.style.color = "#888"; }
                        });
                    }, 200);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html_top.encode("utf-8"))

        elif self.path == '/obs_bottom':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_bot = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>ATS Bottom Cleaned</title>
                <style>
                    * { box-sizing: border-box; }
                    body { background: transparent; color: #fff; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 4px; width: 100vw; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
                    .bot-container { background: rgba(10, 12, 18, 0.99); border: 3px solid #3b82f6; border-radius: 14px; padding: 12px; box-shadow: 0 0 35px rgba(0,0,0,0.95); display: flex; flex-direction: column; gap: 10px; height: 100%; justify-content: space-between; width: 100%; }
                    .card-block { background: #121622; border: 2px solid #334155; border-radius: 12px; padding: 12px 16px; display: flex; flex-direction: column; justify-content: space-around; flex: 1; }
                    .block-title { font-size: 15px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.5px; border-bottom: 2px solid #1a202c; padding-bottom: 4px; font-weight: 800; }
                    .row-double { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
                    .val-giant { font-size: 28px; font-weight: 900; color: #ffaa00; text-shadow: 0 0 8px rgba(255,170,0,0.5); }
                    .val-green { font-size: 26px; font-weight: 900; color: #00ff66; text-shadow: 0 0 8px rgba(0,255,102,0.5); }
                    .val-cyan { font-size: 24px; font-weight: 900; color: #00ffcc; text-shadow: 0 0 8px rgba(0,255,204,0.5); }
                    .lbl-sub { font-size: 14px; color: #a0aec0; font-weight: 800; text-transform: uppercase; }
                </style>
            </head>
            <body>
                <div class="bot-container">
                    <div class="card-block" style="border-left: 5px solid #ffaa00;">
                        <span class="block-title">📦 Mercancía & Pago</span>
                        <div class="row-double">
                            <div><span class="lbl-sub" style="display:block;">Carga</span> <span id="bot-cargo" class="val-giant">Sin carga</span></div>
                            <div style="text-align: right;"><span class="lbl-sub" style="display:block;">Ingreso</span> <span id="bot-pago" class="val-green">$0</span></div>
                        </div>
                    </div>
                    <div class="card-block" style="border-left: 5px solid #3b82f6;">
                        <span class="block-title">🛣️ Navegación de Contrato</span>
                        <div class="row-double">
                            <div><span class="lbl-sub" style="display:block;">Ruta</span> <span id="bot-ruta" class="val-cyan" style="font-size: 24px;">-- ➔ --</span></div>
                            <div style="text-align: right;"><span class="lbl-sub" style="display:block;">Límite Tiempo</span> <span id="bot-tiempo" class="val-giant" style="font-size: 24px; color:#ffaa00;">--</span></div>
                        </div>
                    </div>
                    <div class="card-block" style="border-left: 5px solid #00ffcc;">
                        <span class="block-title">🚚 Estado del Vehículo</span>
                        <div class="row-double">
                            <div><span class="lbl-sub">Presión Aire:</span> <span id="bot-aire" class="val-cyan">120 PSI</span></div>
                            <div><span class="lbl-sub">Combustible:</span> <span id="bot-comb" class="val-cyan">527 L</span></div>
                        </div>
                        <div class="row-double" style="margin-top: 6px;">
                            <div><span class="lbl-sub">Daños Camión / Carga:</span> <span id="bot-daños" class="val-cyan" style="color:#00ffcc; font-size: 24px;">0% / 0%</span></div>
                        </div>
                    </div>
                </div>
                <script>
                    setInterval(() => {
                        fetch('/data').then(res => res.json()).then(data => {
                            document.getElementById('bot-cargo').innerText = data.cargo + (data.peso > 0 ? " (" + data.peso.toFixed(1) + "t)" : "");
                            document.getElementById('bot-pago').innerText = "$" + data.ingresos.toLocaleString();
                            document.getElementById('bot-ruta').innerText = data.origen + " ➔ " + data.destino;
                            document.getElementById('bot-tiempo').innerText = data.t_restante;
                            document.getElementById('bot-aire').innerText = data.aire.toFixed(0) + " PSI";
                            document.getElementById('bot-comb').innerText = data.comb.toFixed(0) + " L";
                            let maxCamion = Math.max(data.w_eng, data.w_tra, data.w_cha);
                            document.getElementById('bot-daños').innerText = maxCamion.toFixed(0) + "% / " + data.w_trl.toFixed(0) + "%";
                        });
                    }, 200);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html_bot.encode("utf-8"))

        elif self.path == '/data':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            data = {
                "temp": temp_frenos, "vel": velocidad_actual, "rpm": rpm_actual, "gear": marcha_actual,
                "aire": presion_aire, "comb": combustible_litros, "cap": combustible_capacidad,
                "marca": camion_marca, "modelo": camion_modelo, "cargo": cargo_nombre, "peso": cargo_peso,
                "ingresos": cargo_ingresos, "origen": origen_ciudad, "destino": destino_ciudad,
                "dist_km": distancia_restante_km, "eta": tiempo_llegada_str, "t_restante": tiempo_restante_contrato_str,
                "sueño": tiempo_sueño_str, "mb_on": motor_brake_on, "retarder": retarder_step, "retarder_max": retarder_max,
                "cc_on": cruise_control_on, "cc_speed": cruise_control_speed, "limit": speed_limit, "beacon": beacon_on,
                "w_eng": wear_engine, "w_tra": wear_trans, "w_cha": wear_chassis, "w_whe": wear_wheels, "w_trl": wear_trailer, "adblue": adblue_litros
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def iniciar_servidor_web():
    try:
        server = HTTPServer(('0.0.0.0', 8080), MobileDashboardHandler)
        server.serve_forever()
    except Exception:
        pass

threading.Thread(target=iniciar_servidor_web, daemon=True).start()

# ==========================================
# 1. VENTANA DE CONFIGURACIÓN INICIAL
# ==========================================
config_final = None

def mostrar_configuracion():
    global config_final
    saved_cfg = cargar_config_disco()
    lang_code = saved_cfg.get("idioma", "es")

    root = tk.Tk()
    root.geometry("460x770")
    root.config(bg="#121216")
    root.resizable(False, False)

    lbl_title = tk.Label(root, fg="#00ffcc", bg="#121216", font=("Segoe UI", 10, "bold"), wraplength=420)
    lbl_title.pack(pady=8)

    lbl_lang = tk.Label(root, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "bold"))
    lbl_lang.pack(anchor="w", padx=25, pady=2)
    
    combo_lang = ttk.Combobox(root, values=["Español (ES)", "English (EN)"], state="readonly", width=42)
    combo_lang.pack(padx=25, pady=4)
    if lang_code == "en":
        combo_lang.set("English (EN)")
    else:
        combo_lang.set("Español (ES)")

    lbl_tipo = tk.Label(root, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "bold"))
    lbl_tipo.pack(anchor="w", padx=25, pady=2)

    combo_tipo = ttk.Combobox(root, state="readonly", width=42)
    combo_tipo.pack(padx=25, pady=4)

    lbl_disp = tk.Label(root, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "bold"))
    lbl_disp.pack(anchor="w", padx=25, pady=(6, 2))

    dispositivos = obtener_dispositivos_activos()
    combo_disp = ttk.Combobox(root, values=[d[0] for d in dispositivos], state="readonly", width=42)
    combo_disp.pack(padx=25, pady=4)
    
    dev_guardado = saved_cfg.get("device_id", 0)
    match_idx = 0
    for i, d in enumerate(dispositivos):
        if d[1] == dev_guardado:
            match_idx = i
            break
    combo_disp.current(match_idx)

    inv_guardado = saved_cfg.get("invertir_acel", True)
    var_invertir = tk.BooleanVar(value=inv_guardado)
    chk_invertir = tk.Checkbutton(root, variable=var_invertir, bg="#121216", fg="#00ffcc", selectcolor="#121216", activebackground="#121216", activeforeground="#00ffcc", font=("Segoe UI", 8, "bold"))
    chk_invertir.pack(anchor="w", padx=25, pady=2)

    frame_test = tk.Frame(root, bg="#1a1a22", highlightbackground="#333344", highlightthickness=1)
    frame_test.pack(fill="x", padx=25, pady=6)

    lbl_test_title = tk.Label(frame_test, fg="#ffaa00", bg="#1a1a22", font=("Segoe UI", 8, "bold"))
    lbl_test_title.pack(anchor="w", padx=10, pady=(4, 2))

    frame_v = tk.Frame(frame_test, bg="#1a1a22")
    frame_v.pack(fill="x", padx=10, pady=2)
    lbl_v = tk.Label(frame_v, fg="#a0aec0", bg="#1a1a22", font=("Segoe UI", 8), width=10, anchor="w")
    lbl_v.pack(side="left")
    bar_vol = ttk.Progressbar(frame_v, orient="horizontal", mode="determinate")
    bar_vol.pack(side="left", fill="x", expand=True)

    frame_a = tk.Frame(frame_test, bg="#1a1a22")
    frame_a.pack(fill="x", padx=10, pady=2)
    lbl_a = tk.Label(frame_a, fg="#a0aec0", bg="#1a1a22", font=("Segoe UI", 8), width=10, anchor="w")
    lbl_a.pack(side="left")
    bar_acel = ttk.Progressbar(frame_a, orient="horizontal", mode="determinate")
    bar_acel.pack(side="left", fill="x", expand=True)

    frame_f = tk.Frame(frame_test, bg="#1a1a22")
    frame_f.pack(fill="x", padx=10, pady=2)
    lbl_f = tk.Label(frame_f, fg="#a0aec0", bg="#1a1a22", font=("Segoe UI", 8), width=10, anchor="w")
    lbl_f.pack(side="left")
    bar_freno = ttk.Progressbar(frame_f, orient="horizontal", mode="determinate")
    bar_freno.pack(side="left", fill="x", expand=True)

    lbl_status_test = tk.Label(frame_test, fg="#888899", bg="#1a1a22", font=("Segoe UI", 8))
    lbl_status_test.pack(anchor="w", padx=10, pady=(2, 4))

    lbl_calor = tk.Label(root, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "bold"))
    lbl_calor.pack(anchor="w", padx=25, pady=(6, 2))
    
    calor_guardado = saved_cfg.get("calor", 0.078)
    slider_calor = ttk.Scale(root, from_=0.001, to=0.800, value=calor_guardado, orient="horizontal")
    slider_calor.pack(fill="x", padx=25, pady=2)
    
    lbl_calor_val = tk.Label(root, fg="#ffffff", bg="#121216", font=("Segoe UI", 8))
    lbl_calor_val.pack(anchor="w", padx=25)

    lbl_enf = tk.Label(root, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "bold"))
    lbl_enf.pack(anchor="w", padx=25, pady=(6, 2))
    
    enf_guardado = saved_cfg.get("enf", 0.002)
    slider_enf = ttk.Scale(root, from_=0.0001, to=0.0500, value=enf_guardado, orient="horizontal")
    slider_enf.pack(fill="x", padx=25, pady=2)
    
    lbl_enf_val = tk.Label(root, fg="#ffffff", bg="#121216", font=("Segoe UI", 8))
    lbl_enf_val.pack(anchor="w", padx=25)

    btn_reset_ini = tk.Button(root, bg="#222230", fg="#00ffcc", font=("Segoe UI", 8, "bold"))
    btn_reset_ini.pack(fill="x", padx=25, pady=(8, 2))

    btn_start = tk.Button(root, bg="#00ffcc", fg="#0b0b0e", font=("Segoe UI", 10, "bold"))
    btn_start.pack(fill="x", padx=25, pady=10)

    def actualizar_textos_ui(*args):
        curr_lang = "en" if "English" in combo_lang.get() else "es"
        t = TEXTOS[curr_lang]
        
        root.title("Configuración de simulación térmica ATS by Flacoo x Gemini" if curr_lang=="es" else "ATS Thermal Simulation Configuration by Flacoo x Gemini")
        lbl_title.config(text=t["cfg_header"])
        lbl_lang.config(text=t["lang_label"])
        lbl_tipo.config(text=t["device_q"])
        
        curr_type_idx = combo_tipo.current() if combo_tipo.current() >= 0 else 0
        combo_tipo.config(values=t["dev_options"])
        combo_tipo.current(curr_type_idx)

        lbl_disp.config(text=t["select_id"])
        chk_invertir.config(text=t["inv_acel"])
        lbl_test_title.config(text=t["diag_title"])
        lbl_v.config(text=t["wheel"])
        lbl_a.config(text=t["throttle"])
        lbl_f.config(text=t["brake"])
        lbl_status_test.config(text=t["wait_ctrl"])
        
        lbl_calor.config(text=t["heat_lbl"])
        lbl_enf.config(text=t["cool_lbl"])
        btn_reset_ini.config(text=t["reset_cal"])
        btn_start.config(text=t["start_sim"])

        act_calor(slider_calor.get())
        act_enf(slider_enf.get())

    def act_calor(val):
        curr_lang = "en" if "English" in combo_lang.get() else "es"
        loc = TEXTOS[curr_lang]
        v = float(val)
        if v > 0.300: desc = loc["heat_ext"]
        elif v > 0.120: desc = loc["heat_rap"]
        elif v >= 0.050: desc = loc["heat_rea"]
        else: desc = loc["heat_len"]
        lbl_calor_val.config(text=f"Valor: {v:.3f} - {desc}")

    def act_enf(val):
        curr_lang = "en" if "English" in combo_lang.get() else "es"
        loc = TEXTOS[curr_lang]
        v = float(val)
        if v > 0.0200: desc = loc["cool_rap"]
        elif v >= 0.0020: desc = loc["cool_nor"]
        else: desc = loc["cool_len"]
        lbl_enf_val.config(text=f"Valor: {v:.4f} - {desc}")

    slider_calor.configure(command=act_calor)
    slider_enf.configure(command=act_enf)
    combo_lang.bind("<<ComboboxSelected>>", actualizar_textos_ui)

    def actualizar_probador():
        if root.winfo_exists():
            idx = combo_disp.current()
            dev_id = dispositivos[idx][1]
            tipo_sel = "mando" if "Mando" in combo_tipo.get() or "Gamepad" in combo_tipo.get() else "volante"
            inv_acel = var_invertir.get()
            
            vol, acel, freno, _ = leer_ejes_dispositivo(dev_id, tipo_sel, inv_acel)
            
            bar_vol['value'] = int(vol * 100)
            bar_acel['value'] = int(acel * 100)
            bar_freno['value'] = int(freno * 100)
            root.after(40, actualizar_probador)

    actualizar_probador()

    def restablecer_inicio():
        slider_calor.set(0.078)
        slider_enf.set(0.002)
        act_calor(0.078)
        act_enf(0.002)

    btn_reset_ini.config(command=restablecer_inicio)

    def iniciar():
        global config_final
        idx = combo_disp.current()
        selected_lang = "en" if "English" in combo_lang.get() else "es"
        config_final = {
            "idioma": selected_lang,
            "device_id": dispositivos[idx][1],
            "tipo": "mando" if "Mando" in combo_tipo.get() or "Gamepad" in combo_tipo.get() else "volante",
            "invertir_acel": var_invertir.get(),
            "calor": float(slider_calor.get()),
            "enf": float(slider_enf.get())
        }
        guardar_config_disco(config_final)
        root.destroy()

    btn_start.config(command=iniciar)
    actualizar_textos_ui()
    root.mainloop()


# ==========================================
# 2. INTERFAZ GRÁFICA PRINCIPAL
# ==========================================
class AppVentanaPrincipal:
    def __init__(self):
        saved_cfg = cargar_config_disco()
        self.lang = saved_cfg.get("idioma", "es")
        self.t = TEXTOS[self.lang]

        self.root = tk.Tk()
        self.root.title("Configuración de simulación térmica ATS by Flacoo x Gemini")
        self.root.geometry("540x480")
        self.root.config(bg="#f0f0f4")
        self.root.resizable(False, False)

        self.construir_menu()

        header_frame = tk.Frame(self.root, bg="#121216", pady=10)
        header_frame.pack(fill="x")
        
        lbl_flow = tk.Label(header_frame, text=self.t["flow_title"], fg="#00ffcc", bg="#121216", font=("Segoe UI", 12, "bold"))
        lbl_flow.pack()
        lbl_author = tk.Label(header_frame, text="by El Flacooo x Gemini", fg="#ffaa00", bg="#121216", font=("Segoe UI", 9, "italic"))
        lbl_author.pack()

        status_frame = ttk.LabelFrame(self.root, text=self.t["server_status"])
        status_frame.pack(fill="x", padx=15, pady=10)

        self.lbl_estado_juego = tk.Label(status_frame, text=self.t["waiting_game"], fg="#cc0000", font=("Segoe UI", 9, "bold"))
        self.lbl_estado_juego.pack(anchor="w", padx=10, pady=5)

        self.lbl_estado_web = tk.Label(status_frame, text=f"{self.t['web_active']}{obtener_ip_local()}:8080/", fg="#008844", font=("Segoe UI", 9))
        self.lbl_estado_web.pack(anchor="w", padx=10, pady=(0, 5))

        links_frame = ttk.LabelFrame(self.root, text=self.t["links_frame"])
        links_frame.pack(fill="both", expand=True, padx=15, pady=5)

        ip_local = obtener_ip_local()
        self.crear_fila_enlace(links_frame, self.t["link_mob"], f"http://{ip_local}:8080/")
        self.crear_fila_enlace(links_frame, self.t["link_top"], "http://127.0.0.1:8080/obs_top")
        self.crear_fila_enlace(links_frame, self.t["link_bot"], "http://127.0.0.1:8080/obs_bottom")

        footer_lbl = tk.Label(self.root, text=self.t["footer_tray"], fg="#666677", bg="#f0f0f4", font=("Segoe UI", 8))
        footer_lbl.pack(pady=5)

        # 🛑 AQUÍ APLICAMOS EL MINIMIZAR CON NOTIFICACIÓN FLOTANTE (BALLOON TIP)
        self.root.protocol("WM_DELETE_WINDOW", self.salir_programa)
        self.root.bind("<Unmap>", self.al_minimizar)

        threading.Thread(target=self.actualizar_estado_ui, daemon=True).start()

        self.tray_icon = None
        if PYSTRAY_DISPONIBLE:
            threading.Thread(target=self.iniciar_system_tray, daemon=True).start()

        self.root.mainloop()

    def al_minimizar(self, event):
        if event.widget == self.root and self.root.state() == 'iconic':
            self.minimizar_a_bandeja()

    def construir_menu(self):
        menubar = tk.Menu(self.root)
        
        server_menu = tk.Menu(menubar, tearoff=0)
        server_menu.add_command(label=self.t["menu_tray"], command=self.minimizar_a_bandeja)
        server_menu.add_separator()
        server_menu.add_command(label=self.t["menu_exit"], command=self.salir_programa)
        menubar.add_cascade(label=self.t["menu_server"], menu=server_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label=self.t["menu_settings"], command=self.abrir_configuracion)
        tools_menu.add_command(label=self.t["menu_diag"], command=self.abrir_diagnostico)
        menubar.add_cascade(label=self.t["menu_tools"], menu=tools_menu)

        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="🇪🇸 Español", command=lambda: self.cambiar_idioma("es"))
        lang_menu.add_command(label="🇬🇧 English", command=lambda: self.cambiar_idioma("en"))
        menubar.add_cascade(label=self.t["menu_lang"], menu=lang_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.t["menu_credits"], command=self.abrir_creditos)
        menubar.add_cascade(label=self.t["menu_help"], menu=help_menu)

        self.root.config(menu=menubar)

    def cambiar_idioma(self, nuevo_idioma):
        saved_cfg = cargar_config_disco()
        saved_cfg["idioma"] = nuevo_idioma
        guardar_config_disco(saved_cfg)
        messagebox.showinfo("Idioma / Language", "Idioma cambiado. Por favor reinicia la aplicación para aplicar todos los cambios." if nuevo_idioma == "es" else "Language changed. Please restart the application to apply all changes.")

    def crear_fila_enlace(self, parent, etiqueta, url):
        frame = tk.Frame(parent, bg="#ffffff", pady=4)
        frame.pack(fill="x", padx=10, pady=3)
        
        lbl_title = tk.Label(frame, text=etiqueta, font=("Segoe UI", 9, "bold"), bg="#ffffff", width=24, anchor="w")
        lbl_title.pack(side="left")

        link_btn = tk.Label(frame, text=url, fg="#0066cc", bg="#ffffff", font=("Segoe UI", 9, "underline"), cursor="hand2")
        link_btn.pack(side="left", padx=5)
        link_btn.bind("<Button-1>", lambda e: webbrowser.open(url))

        copy_btn = tk.Button(frame, text="Copiar" if self.lang=="es" else "Copy", font=("Segoe UI", 8), command=lambda: self.copiar_url(url), width=7)
        copy_btn.pack(side="right")

    def copiar_url(self, url):
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        messagebox.showinfo("Copiado" if self.lang=="es" else "Copied", "¡Enlace copiado al portapapeles!" if self.lang=="es" else "Link copied to clipboard!")

    def actualizar_estado_ui(self):
        while True:
            try:
                if self.root.winfo_exists():
                    if juego_conectado:
                        self.lbl_estado_juego.config(text=f"🟢 Conectado al simulador ({camion_marca} {camion_modelo})" if self.lang=="es" else f"🟢 Connected to simulator ({camion_marca} {camion_modelo})", fg="#008844")
                    else:
                        self.lbl_estado_juego.config(text=self.t["waiting_game"], fg="#cc0000")
            except Exception:
                break
            time.sleep(1)

    def abrir_configuracion(self):
        saved_cfg = cargar_config_disco()
        cfg_win = tk.Toplevel(self.root)
        cfg_win.title("Configuración de Sensibilidad" if self.lang=="es" else "Sensitivity Configuration")
        cfg_win.geometry("420x390")
        cfg_win.config(bg="#121216")
        cfg_win.resizable(False, False)

        tk.Label(cfg_win, text="⚙️ AJUSTAR SENSIBILIDAD" if self.lang=="es" else "⚙️ ADJUST SENSITIVITY", fg="#00ffcc", bg="#121216", font=("Segoe UI", 11, "bold")).pack(pady=10)

        lbl_c_txt = "Sensibilidad Calor (Izquierda: Lento | Derecha: Rápido):" if self.lang=="es" else "Heating Sensitivity (Left: Slow | Right: Fast):"
        tk.Label(cfg_win, text=lbl_c_txt, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(5, 2))
        
        calor_val = saved_cfg.get("calor", 0.078)
        s_calor = ttk.Scale(cfg_win, from_=0.001, to=0.800, value=calor_val, orient="horizontal")
        s_calor.pack(fill="x", padx=20, pady=2)
        
        lbl_calor_desc = tk.Label(cfg_win, text="", fg="#ffffff", bg="#121216", font=("Segoe UI", 8))
        lbl_calor_desc.pack(anchor="w", padx=20)

        def act_calor_desc(val):
            loc = TEXTOS[self.lang]
            v = float(val)
            if v > 0.300: desc = loc["heat_ext"]
            elif v > 0.120: desc = loc["heat_rap"]
            elif v >= 0.050: desc = loc["heat_rea"]
            else: desc = loc["heat_len"]
            lbl_calor_desc.config(text=f"Valor: {v:.3f} - {desc}")

        s_calor.configure(command=act_calor_desc)
        act_calor_desc(calor_val)

        lbl_e_txt = "Velocidad Enfriamiento (Izquierda: Lento | Derecha: Rápido):" if self.lang=="es" else "Cooling Speed (Left: Slow | Right: Fast):"
        tk.Label(cfg_win, text=lbl_e_txt, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 2))
        
        enf_val = saved_cfg.get("enf", 0.002)
        s_enf = ttk.Scale(cfg_win, from_=0.0001, to=0.0500, value=enf_val, orient="horizontal")
        s_enf.pack(fill="x", padx=20, pady=2)
        
        lbl_enf_desc = tk.Label(cfg_win, text="", fg="#ffffff", bg="#121216", font=("Segoe UI", 8))
        lbl_enf_desc.pack(anchor="w", padx=20)

        def act_enf_desc(val):
            loc = TEXTOS[self.lang]
            v = float(val)
            if v > 0.0200: desc = loc["cool_rap"]
            elif v >= 0.0020: desc = loc["cool_nor"]
            else: desc = loc["cool_len"]
            lbl_enf_desc.config(text=f"Valor: {v:.4f} - {desc}")

        s_enf.configure(command=act_enf_desc)
        act_enf_desc(enf_val)

        def restablecer_predeterminados():
            s_calor.set(0.078)
            s_enf.set(0.002)
            act_calor_desc(0.078)
            act_enf_desc(0.002)
            messagebox.showinfo("Restablecido", "Valores restablecidos a la calibración realista predeterminada." if self.lang=="es" else "Values reset to default realistic calibration.")

        btn_reset = tk.Button(cfg_win, text=self.t["reset_cal"], bg="#333344", fg="#00ffcc", font=("Segoe UI", 8, "bold"), command=restablecer_predeterminados)
        btn_reset.pack(pady=10)

        def guardar():
            cfg = saved_cfg.copy()
            cfg["calor"] = float(s_calor.get())
            cfg["enf"] = float(s_enf.get())
            guardar_config_disco(cfg)
            messagebox.showinfo("Guardado", "¡Configuración de sensibilidad actualizada correctamente!" if self.lang=="es" else "Sensitivity configuration updated successfully!")
            cfg_win.destroy()

        tk.Button(cfg_win, text="💾 GUARDAR CAMBIOS" if self.lang=="es" else "💾 SAVE CHANGES", bg="#00ffcc", fg="#0b0b0e", font=("Segoe UI", 9, "bold"), command=guardar).pack(pady=5)

    def abrir_diagnostico(self):
        diag_win = tk.Toplevel(self.root)
        diag_win.title("Diagnóstico de Controles y Frenos" if self.lang=="es" else "Controls and Brakes Diagnostics")
        diag_win.geometry("360x320")
        diag_win.config(bg="#1a1a22")
        diag_win.resizable(False, False)

        tk.Label(diag_win, text="🔍 DIAGNÓSTICO EN TIEMPO REAL" if self.lang=="es" else "🔍 REAL-TIME DIAGNOSTICS", fg="#ffaa00", bg="#1a1a22", font=("Segoe UI", 10, "bold")).pack(pady=10)

        saved_cfg = cargar_config_disco()
        dev_id = saved_cfg.get("device_id", 0)
        tipo = saved_cfg.get("tipo", "volante")
        invertir = saved_cfg.get("invertir_acel", True)

        lbl_v = tk.Label(diag_win, text="Volante: 0%" if self.lang=="es" else "Wheel: 0%", fg="#fff", bg="#1a1a22")
        lbl_v.pack(pady=2)
        lbl_a = tk.Label(diag_win, text="Acelerador: 0%" if self.lang=="es" else "Throttle: 0%", fg="#fff", bg="#1a1a22")
        lbl_a.pack(pady=2)
        lbl_f = tk.Label(diag_win, text="Freno: 0%" if self.lang=="es" else "Brake: 0%", fg="#fff", bg="#1a1a22")
        lbl_f.pack(pady=2)
        lbl_t = tk.Label(diag_win, text="Temp. Frenos: 25.0 °C" if self.lang=="es" else "Brake Temp: 25.0 °C", fg="#00ffcc", bg="#1a1a22", font=("Segoe UI", 11, "bold"))
        lbl_t.pack(pady=10)

        def actualizar():
            if diag_win.winfo_exists():
                vol, acel, freno, _ = leer_ejes_dispositivo(dev_id, tipo, invertir)
                w_lbl = "Volante" if self.lang=="es" else "Wheel"
                a_lbl = "Acelerador" if self.lang=="es" else "Throttle"
                f_lbl = "Freno" if self.lang=="es" else "Brake"
                t_lbl = "Temp. Frenos" if self.lang=="es" else "Brake Temp"
                lbl_v.config(text=f"{w_lbl}: {int(vol*100)}%")
                lbl_a.config(text=f"{a_lbl}: {int(acel*100)}%")
                lbl_f.config(text=f"{f_lbl}: {int(freno*100)}%")
                lbl_t.config(text=f"{t_lbl}: {temp_frenos:.1f} °C")
                diag_win.after(50, actualizar)

        actualizar()

    def abrir_creditos(self):
        cred_win = tk.Toplevel(self.root)
        cred_win.title("Créditos y Agradecimientos" if self.lang=="es" else "Credits and Acknowledgements")
        cred_win.geometry("420x260")
        cred_win.config(bg="#121216")
        cred_win.resizable(False, False)

        tk.Label(cred_win, text="⭐ CRÉDITOS Y AGRADECIMIENTOS" if self.lang=="es" else "⭐ CREDITS AND ACKNOWLEDGEMENTS", fg="#00ffcc", bg="#121216", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        texto = (
            "Este programa de simulación térmica utiliza como base indispensable "
            "el servidor de telemetría de Funbit para American Truck Simulator y Euro Truck Simulator 2.\n\n"
            "¡Un agradecimiento especial a Funbit por su excelente trabajo de código abierto!"
            if self.lang=="es" else
            "This thermal simulation program uses Funbit's telemetry server "
            "for American Truck Simulator and Euro Truck Simulator 2 as an indispensable base.\n\n"
            "Special thanks to Funbit for their excellent open source work!"
        )
        tk.Label(cred_win, text=texto, fg="#cccccc", bg="#121216", wraplength=380, justify="center", font=("Segoe UI", 9)).pack(pady=5)

        url = "https://github.com/funbit/ets2-telemetry-server"
        link_btn = tk.Label(cred_win, text=url, fg="#00ffcc", bg="#121216", font=("Segoe UI", 9, "underline"), cursor="hand2")
        link_btn.pack(pady=10)
        link_btn.bind("<Button-1>", lambda e: webbrowser.open(url))

        tk.Button(cred_win, text="Cerrar" if self.lang=="es" else "Close", bg="#333344", fg="#ffffff", command=cred_win.destroy).pack(pady=5)

    def minimizar_a_bandeja(self):
        self.root.withdraw()
        if self.tray_icon:
            try:
                self.tray_icon.notify(self.t["tray_msg"], self.t["tray_title"])
            except Exception:
                pass

    def restaurar_desde_bandeja(self, icon=None, item=None):
        if self.root:
            self.root.deiconify()

    def salir_programa(self, icon=None, item=None):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit()

    def iniciar_system_tray(self):
        if not PYSTRAY_DISPONIBLE:
            return
        try:
            image = Image.new('RGB', (64, 64), color=(18, 18, 22))
            dc = ImageDraw.Draw(image)
            dc.rectangle((16, 16, 48, 48), fill=(0, 255, 204))

            menu = pystray.Menu(
                pystray.MenuItem('Restaurar Ventana' if self.lang=="es" else 'Restore Window', self.restaurar_desde_bandeja, default=True),
                pystray.MenuItem('Salir' if self.lang=="es" else 'Exit', self.salir_programa)
            )
            self.tray_icon = pystray.Icon("ATS Thermal Brakes", image, "ATS Thermal Brakes", menu)
            self.tray_icon.run()
        except Exception:
            pass


# ==========================================
# FLUJO DE EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    mostrar_configuracion()
    AppVentanaPrincipal()