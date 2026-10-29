# =============================================================================
# simulacion_termica_3.pyw - VERSION FINAL DE LA CALIBRACION DEL FRENADO A FONDO (informe v10)
# Calibrado y validado (+-5 % en tiempo y distancia) con el Kenworth W900: tractor solo, remolque vacio
# y cargas de 20, 27, 35 y 56 t, en frio y en caliente. APRENDER_SIN_ID = True (definitivo).
# Sin cambios de comportamiento respecto a la version anterior: solo se anade esta cabecera.
# Pendiente (no calibrado): freno de motor, retarder, freno de remolque (boton), otros camiones.
# =============================================================================
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
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import atexit
import math

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
PANEL_FILE = os.path.join(script_dir, "sim_panel_button_box.html")

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

_cfg_cache = {"mtime": None, "data": {}, "revisado": 0.0}

def cargar_config_cacheada():
    """Igual que cargar_config_disco(), pero sin leer el disco 30 veces por segundo.
    Solo revisa si el archivo cambió como máximo una vez por segundo."""
    ahora = time.time()
    if _cfg_cache["mtime"] is not None and ahora - _cfg_cache["revisado"] < 1.0:
        return _cfg_cache["data"]
    _cfg_cache["revisado"] = ahora
    try:
        mtime = os.path.getmtime(CONFIG_FILE)
    except OSError:
        mtime = -1
    if mtime != _cfg_cache["mtime"]:
        _cfg_cache["data"] = cargar_config_disco()
        _cfg_cache["mtime"] = mtime
    return _cfg_cache["data"]

# ==========================================
# DICCIONARIO DE IDIOMAS (ESPAÑOL / ENGLISH)
# ==========================================
TEXTOS = {
    "es": {
        "cfg_title": "Termofreno - Configuración de simulación térmica ATS by El Flacooo",
        "cfg_header": "⚙️ TERMOFRENO · CONFIGURACIÓN DE SIMULACIÓN TÉRMICA ATS · BY EL FLACOOO",
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
        
        "flow_title": "🔥 TERMOFRENO · SIMULACIÓN TÉRMICA DE FRENOS ATS",
        "server_status": " Estado del Servidor ",
        "waiting_game": "🔴 Esperando conexión con el juego (ATS)...",
        "web_active": "🟢 Servidor Web Activo en http://",
        "links_frame": " Enlaces de Acceso (Móvil, OBS & Panel) ",
        "link_mob": "📱 Dashboard Móvil:",
        "link_top": "💻 OBS Overlay Superior:",
        "link_bot": "💻 OBS Overlay Inferior:",
        "link_panel": "🎮 Panel de Botones (/panel):",
        "footer_tray": "💡 Minimiza la ventana para enviarla a los íconos ocultos de Windows.",
        
        "tray_title": "Termofreno",
        "tray_msg": "Simulación térmica minimizada.\nDoble clic para restaurar la ventana."
    },
    "en": {
        "cfg_title": "Termofreno - ATS Thermal Simulation Configuration by El Flacooo",
        "cfg_header": "⚙️ TERMOFRENO · ATS THERMAL SIMULATION CONFIGURATION · BY EL FLACOOO",
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
        
        "flow_title": "🔥 TERMOFRENO · ATS THERMAL BRAKES SIMULATION",
        "server_status": " Server Status ",
        "waiting_game": "🔴 Waiting for game connection (ATS)...",
        "web_active": "🟢 Web Server Active at http://",
        "links_frame": " Access Links (Mobile, OBS & Panel) ",
        "link_mob": "📱 Mobile Dashboard:",
        "link_top": "💻 OBS Top Overlay:",
        "link_bot": "💻 OBS Bottom Overlay:",
        "link_panel": "🎮 Button Panel (/panel):",
        "footer_tray": "💡 Minimize window to send it to Windows system tray.",
        
        "tray_title": "Termofreno",
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
# SIMULACIÓN DE TECLADO CON SCAN CODES (DIRECTINPUT OPTIMIZADO)
# ==========================================
# Solo se aceptan estas teclas desde la red (las que usan los paneles).
# Cualquier otra se rechaza con 403, para que nadie en tu WiFi pueda escribir en tu PC.
TECLAS_PERMITIDAS = (set("abcdefghijklmnopqrstuvwxyz0123456789;,.(ñ-=[]/\\`'")
                     | {'space', 'escape', 'enter', 'tab'}
                     | {f'f{n}' for n in range(1, 13)})

# Si una tecla mantenida no se refresca en este tiempo, se suelta sola
# (por ejemplo si la tablet pierde el WiFi con el dedo puesto en un botón).
MAX_SEGUNDOS_TECLA_MANTENIDA = 20.0

KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

_lock_teclado = threading.RLock()
_teclas_mantenidas = {}   # tecla -> (vk, [modificadores], último_refresco)

def obtener_vk_y_mods(key_str):
    """Devuelve (vk, [vk de modificadores]). Ahora respeta Shift/Ctrl/Alt (AltGr)
    que exige el teclado de Windows para escribir ese carácter."""
    key_str = key_str.lower()
    if key_str == 'space': return 0x20, []
    if key_str == 'escape': return 0x1B, []
    if key_str == 'enter': return 0x0D, []
    if key_str == 'tab': return 0x09, []
    if len(key_str) in (2, 3) and key_str[0] == 'f' and key_str[1:].isdigit() and 1 <= int(key_str[1:]) <= 12:
        return 0x70 + int(key_str[1:]) - 1, []
    if len(key_str) == 1:
        c = key_str.upper()
        if 'A' <= c <= 'Z' or '0' <= c <= '9':
            return ord(c), []
        try:
            fn = ctypes.windll.user32.VkKeyScanW
            fn.restype = ctypes.c_short
            res = fn(ord(key_str))
        except Exception:
            return 0, []
        if res == -1:
            return 0, []
        vk = res & 0xFF
        estado = (res >> 8) & 0xFF
        mods = []
        if estado & 1: mods.append(0x10)   # Shift
        if estado & 2: mods.append(0x11)   # Ctrl
        if estado & 4: mods.append(0x12)   # Alt
        return vk, mods
    return 0, []

def _evento_tecla(vk, subir=False):
    user32 = ctypes.windll.user32
    scancode = user32.MapVirtualKeyW(vk, 0)
    flags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if subir else 0)
    user32.keybd_event(vk, scancode, flags, 0)

def simular_tecla_press(key_str):
    vk, mods = obtener_vk_y_mods(key_str)
    if not vk:
        return
    with _lock_teclado:
        for m in mods: _evento_tecla(m)
        _evento_tecla(vk)
        time.sleep(0.06)
        _evento_tecla(vk, True)
        for m in reversed(mods): _evento_tecla(m, True)

def simular_tecla_down(key_str):
    key_str = key_str.lower()
    vk, mods = obtener_vk_y_mods(key_str)
    if not vk:
        return
    with _lock_teclado:
        if key_str in _teclas_mantenidas:
            # Ya estaba presionada: solo se refresca el reloj de seguridad
            vk0, mods0, _ = _teclas_mantenidas[key_str]
            _teclas_mantenidas[key_str] = (vk0, mods0, time.time())
            return
        for m in mods: _evento_tecla(m)
        _evento_tecla(vk)
        _teclas_mantenidas[key_str] = (vk, mods, time.time())

def simular_tecla_up(key_str):
    key_str = key_str.lower()
    with _lock_teclado:
        info = _teclas_mantenidas.pop(key_str, None)
        if info:
            vk, mods, _ = info
            _evento_tecla(vk, True)
            for m in reversed(mods): _evento_tecla(m, True)
        else:
            # No estaba registrada: se suelta igual por seguridad
            vk, _mods = obtener_vk_y_mods(key_str)
            if vk:
                _evento_tecla(vk, True)

def liberar_todas_las_teclas():
    with _lock_teclado:
        pendientes = list(_teclas_mantenidas.items())
        _teclas_mantenidas.clear()
        for _k, (vk, mods, _t) in pendientes:
            try:
                _evento_tecla(vk, True)
                for m in reversed(mods): _evento_tecla(m, True)
            except Exception:
                pass

def _vigilante_teclas():
    while True:
        time.sleep(0.5)
        try:
            ahora = time.time()
            with _lock_teclado:
                vencidas = [k for k, (_vk, _m, t) in _teclas_mantenidas.items()
                            if ahora - t > MAX_SEGUNDOS_TECLA_MANTENIDA]
            for k in vencidas:
                simular_tecla_up(k)
        except Exception:
            pass

atexit.register(liberar_todas_las_teclas)
threading.Thread(target=_vigilante_teclas, daemon=True).start()

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
terreno_actual = {"pitch": None, "roll": None, "acc_z": None, "temp_juego": None}   # inclinación y aceleración del camión (para la ventana de calibración)
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
# La telemetría a veces pierde la carga del remolque (id vacío y masa 0) con el remolque enganchado. Se conserva la última
# lectura válida mientras siga enganchado; se olvida al desengancharlo (CARGA_RET_FUERA_LECTURAS lecturas seguidas).
carga_retenida = False                 # True mientras la masa y el id vienen de la última lectura válida y no de la telemetría
_carga_ret = {"id": None, "masa_t": 0.0, "fuera": 0}
CARGA_RET_FUERA_LECTURAS = 3
APRENDER_SIN_ID = True                 # False: no se aprende ni se guarda k en la clave "sin_id|0t" (carga perdida o remolque sin id)
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
freno_tope = 1.0   # límite del pedal de freno (0.25 / 0.5 / 0.75 / 1.0). Solo para pruebas de calibración

# Estado real del camión (lo lee el panel para que los LEDs coincidan con el juego)
estado_juego = {
    "motor": False, "electrico": False, "freno_mano": False, "luces": 0, "altas": False,
    "torretas": False, "limpiadores": False, "int_izq": False, "int_der": False,
    "hazards": False, "remolque": False, "freno_motor": False, "crucero": False,
}

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

# ==========================================
# MODELO TÉRMICO DE FRENOS (unidades SI, basado en datos reales)
#  - El calor de cada frenada es la energía cinética real que se pierde (potencia = masa x deceleración x velocidad).
#  - Los tambores son hierro fundido: se calientan según su masa real (Gunite 16.5x7 ~ 43-51 kg, dirección 15x4 ~ 30 kg).
#  - Se enfrían por convección (depende de la velocidad) y radiación (crece mucho con la temperatura).
#  - La eficacia baja con la temperatura (fading): normal hasta ~150 °C, límite recomendado ~260 °C (500 °F),
#    crítico ~315 °C (600 °F) y sin efecto hacia ~450 °C.
# Todo se puede ajustar con las constantes de abajo al probarlo en el juego.
# ==========================================
T_AMB = 25.0                 # temperatura ambiente (°C)
T_MAX = 600.0                # tope físico del modelo
T_PERDIDA_TOTAL = 450.0      # a esta temperatura los frenos ya no frenan
T_INICIO_FADING = 260.0      # límite recomendado de los sistemas de pendiente (500 °F)
MASA_TRACTOR_KG = 8500.0
MASA_REMOLQUE_KG = 7000.0    # remolque vacío
MASA_FRENOS_TRACTOR_KG = 252.0   # 2 tambores de dirección (30 kg) + 4 de tracción (48 kg)
MASA_FRENOS_REMOLQUE_KG = 192.0  # 4 tambores de remolque (48 kg)
AREA_FRENOS_TRACTOR_M2 = 2.1
AREA_FRENOS_REMOLQUE_M2 = 1.4
DECEL_VACIO = 5.0            # m/s2: tractor vacío (norma FMVSS 121: 60 mph en 235 ft)
DECEL_GVWR = 4.72            # m/s2: cargado a su peso máximo (60 mph en 250 ft)
MASA_VACIO_T = 15.5
MASA_GVWR_T = 36.3           # 80 000 lb
FUERZA_FRENADO_MAX_N = 257000.0   # calibrada en el juego: ~71.5 t de 95 a 0 km/h en 7.34 s
ESCALA_ENFRIAMIENTO_PARADO = 6.0    # parado, el enfriamiento corre 6x más rápido que en tiempo real (antes 19x, el reloj del juego; con 6x parado tarda ~4 veces más que a 90 km/h, como en la realidad)
ESCALA_ENFRIAMIENTO_MARCHA = 6.0    # en marcha (10 km/h o más) igual que parado: 6x (antes 1x: de 300 a 100 °C tardaba ~22 min a 90 km/h; ahora ~3.7). Ajustable al probar.
SIGMA = 5.670e-8

CURVA_EFICACIA = [(0.0, 1.0), (150.0, 1.0), (200.0, 0.95), (260.0, 0.85), (315.0, 0.60),
                  (370.0, 0.30), (430.0, 0.05), (450.0, 0.0)]

def eficacia_por_temp(T):
    if T <= CURVA_EFICACIA[0][0]:
        return CURVA_EFICACIA[0][1]
    for (t0, e0), (t1, e1) in zip(CURVA_EFICACIA, CURVA_EFICACIA[1:]):
        if T <= t1:
            return e0 + (e1 - e0) * (T - t0) / (t1 - t0)
    return 0.0

# Piso de eficacia a baja velocidad: con los frenos muy calientes (modelo > ~370 °C) la eficacia llega casi a 0 y el camión
# no se detenía (en una prueba rodó ~15 s a 2 km/h). A baja velocidad casi no entra calor, así que siempre queda algo de freno:
# EFICACIA_PISO a 15 km/h o menos, bajando en línea recta hasta 0 a 40 km/h. No cambia nada mientras la eficacia normal esté por encima.
EFICACIA_PISO = 0.30
PISO_V_PLENO_KMH = 15.0
PISO_V_FIN_KMH = 40.0

def eficacia_con_piso(efic, v_kmh):
    """Eficacia de la curva de temperatura, con el piso de baja velocidad como mínimo."""
    try:
        v = abs(float(v_kmh))
    except Exception:
        return efic
    f = max(0.0, min(1.0, (PISO_V_FIN_KMH - v) / max(1.0, PISO_V_FIN_KMH - PISO_V_PLENO_KMH)))
    return max(efic, EFICACIA_PISO * f)

def masa_total_kg():
    m = MASA_TRACTOR_KG
    if estado_juego.get("remolque"):
        m += MASA_REMOLQUE_KG
    return m + max(0.0, float(cargo_peso)) * 1000.0

def masa_frenos_kg():
    return MASA_FRENOS_TRACTOR_KG + (MASA_FRENOS_REMOLQUE_KG if estado_juego.get("remolque") else 0.0)

def area_frenos_m2():
    return AREA_FRENOS_TRACTOR_M2 + (AREA_FRENOS_REMOLQUE_M2 if estado_juego.get("remolque") else 0.0)

# --- FRENADO ---------------------------------------------------------------------------------
# Medido en el juego con el fading propio anulado (max_brake_temperature alto), 18 pruebas:
#   - El freno entrega unos 11.5 m/s2 por cada 1.0 de eje de freno, con cualquier carga.
#   - Con eje alto, el agarre de las llantas limita la frenada a unos 9.3 m/s2.
# Con el mod así, el programa controla la fuerza: el eje que se envía al juego se escala para que, a fondo y en frío,
# el camión frene como uno real (el fading lo aplica la eficacia, que baja con la temperatura).
K_DECEL_POR_EJE = 14.5          # m/s2 por eje 1.0: valor fijo, solo se usa si "freno_adaptativo" está apagado
DECEL_AGARRE = 9.3              # m/s2 máximos por agarre (medido)
DECEL_OBJETIVO_MAX = 5.8        # m/s2 a fondo en frío con un camión ligero (real: la norma pide >= 5.0 vacío)
FUERZA_FRENOS_NOMINAL_N = 200000.0   # YA NO se usa para el objetivo (ver DECEL_LEGAL_TABLA); se deja por compatibilidad
# Objetivo de frenado a fondo en frío según la masa total: el límite legal de EE. UU. (FMVSS 121, desde 60 mph, camión cargado):
# 250 ft = 4.7 m/s2 hasta ~36 t; 310 ft = 3.8 m/s2 para combinaciones muy pesadas (servicio severo). Entre puntos se interpola.
# Es un límite máximo permitido, no lo que logra un camión moderno: se usa a propósito para que el camión "se sienta" pesado.
DECEL_LEGAL_TABLA = [(8.5, 5.8), (36.3, 4.7), (50.0, 3.8)]   # (masa total en t, m/s2)
FRENADO_PROGRAMA = True         # se puede apagar con "frenado_programa": false en la config
FRENO_ADAPTATIVO = True         # aprende la fuerza por eje de cada camión y remolque mientras frenas ("freno_adaptativo")
# El freno del juego pierde fuerza al calentarse (medido en 5 frenadas, 33 a 200 °C del juego: k = 29.5 - 0.0747 T, R2 0.89,
# sin relación con la velocidad). Por eso se aprende un valor BASE (frenos a 0 °C) y se aplica la temperatura que reporta el juego.
K_BASE_INICIAL = 31.3           # m/s2 por eje 1.0 (ya sin el descuento del eje) con los frenos del juego a 0 °C (Kenworth W900 sin remolque); antes 27.6 con el descuento incluido; se ajusta solo
FADING_JUEGO = 0.002535         # fracción de fuerza que pierde el freno del juego por cada °C (tractor solo)
FADING_JUEGO_REMOLQUE = 0.0007  # con remolque pierde menos por °C (serie 1 de 56 t con el mod nuevo: 0.07 %/°C, ±0.003; con 0.0020 el programa sobrefrenaba a más de 150 °C y el k base se inflaba)
TJ_APRENDER_MAX = 150.0         # por encima de esta temperatura del juego no se aprende el k: la telemetría se satura en 200 °C y la corrección deja de ser fiable
TJ_TOPE = 200.0                 # la telemetría no pasa de 200 °C
FADING_VEL = 0.0023             # el freno del juego rinde más a baja velocidad: k(v) = k(100 km/h) x (1 + FADING_VEL x (100 - v)); ~15 % más a 20 km/h (medido en la serie 1 de 56 t). Con 0 se apaga
K_BASE_INICIAL_REMOLQUE = 14.4  # k base de partida para una combinación con remolque que aún no conoce (ya sin el descuento del eje; antes 14.0 con él: medidos 12.7 a 14.3 y 17.4, que pasan a 13.9 a 15.0 y 19.4); se ajusta solo en la primera frenada
# Pérdida de fuerza por °C con remolque, según la masa total (t): ~20 t de carga (35.8 t en total) pierde ~0.18 %/°C (serie 20 t: k a 200 °C = 64 % del k a 0 °C),
# 35 t y 56 t de carga (50 t o más en total) pierden ~0.07 %/°C. Entre los dos puntos se interpola (no medido); fuera, se mantiene el valor del extremo.
FADING_REMOLQUE_TABLA = [(36.3, 0.0018), (50.0, 0.0007)]   # (masa total en t, fracción por °C)
# Zona saturada: la telemetría no pasa de 200 °C, así que desde la 2.ª frenada seguida casi todo ocurre ahí y la curva lineal no la describe bien.
# Por eso se aprende además un k propio de esa zona (k_sat, a 100 km/h) y se mezcla con la curva entre TJ_MEZCLA_INI y TJ_SAT_MIN.
TJ_MEZCLA_INI = 150.0           # hasta aquí manda solo la curva de temperatura (k base x factor_temp)
TJ_SAT_MIN = 190.0              # desde aquí manda el k_sat aprendido (si ya tiene muestras suficientes)
K_SAT_MUESTRAS_MIN = 4          # muestras mínimas del k_sat para empezar a usarlo
K_MEMORIA_VERSION = 5   # sube cuando cambia la curva de temperatura: los valores guardados con otra versión se descartan (4: fading por masa y k_sat; 5: k sin el descuento del eje, con compensación)
# El juego descuenta ~0.023 del eje de freno que recibe (medido en 15 CSV: freno_juego = 1.02 x eje - 0.0205; deceleración = ~12.8 x (eje - 0.023)).
# Con el eje a fondo se nota poco (~8 %), pero con el pedal suave casi no frena (25 % de pedal con 56 t dio -25 %). Se compensa sumando ese valor al eje enviado.
COMP_EJE_FRENO = 0.023          # se suma al eje enviado a vJoy (solo con frenado_programa); el aprendizaje usa el eje pedido, sin la compensación
COMP_EJE_MIN = 0.003            # por debajo de este eje pedido no se compensa (pedal suelto o ruido del sensor)
K_MEMORIA_FILE = os.path.join(script_dir, "k_freno_guardado.json")   # k base aprendido de cada combinación camión + remolque + carga (se guarda solo)
_kfreno = {"k": K_BASE_INICIAL, "n": 0, "t_freno": None, "clave": None, "cand": None, "cand_n": 0, "nuevo": 0, "ks": None, "ns": 0, "nuevo_s": 0}
_kmem = {"cargada": False, "datos": {}}

def factor_temp_juego(tj):
    """Cuánta fuerza conserva el freno del juego a esa temperatura (1.0 a 0 °C). Sin dato, se supone caliente (200 °C)."""
    try:
        tj = TJ_TOPE if tj is None else float(tj)
    except Exception:
        tj = TJ_TOPE
    pend_c = pendiente_fading_remolque(masa_total_kg()) if estado_juego.get("remolque") else FADING_JUEGO
    return max(0.3, 1.0 - pend_c * max(0.0, min(TJ_TOPE, tj)))

def pendiente_fading_remolque(m_kg):
    """Fracción de fuerza que pierde el freno del juego por °C con remolque, según la masa total (tabla interpolada)."""
    t = m_kg / 1000.0
    pts = FADING_REMOLQUE_TABLA
    if not pts:
        return FADING_JUEGO_REMOLQUE
    if t <= pts[0][0]:
        return pts[0][1]
    if t >= pts[-1][0]:
        return pts[-1][1]
    for (t0, a0), (t1, a1) in zip(pts, pts[1:]):
        if t <= t1:
            return a0 + (a1 - a0) * (t - t0) / (t1 - t0)
    return pts[-1][1]

def k_por_temp(tj):
    """k (a 100 km/h) con los frenos del juego a la temperatura tj: la curva k base x factor_temp, y en la zona saturada
    (tj >= TJ_SAT_MIN) el k_sat aprendido, mezclados entre TJ_MEZCLA_INI y TJ_SAT_MIN para que no haya saltos."""
    st = _kfreno
    kc = st["k"] * factor_temp_juego(tj)
    ks = st.get("ks")
    if ks is None or st.get("ns", 0) < K_SAT_MUESTRAS_MIN:
        return kc
    try:
        t = TJ_TOPE if tj is None else float(tj)
    except Exception:
        t = TJ_TOPE
    w = max(0.0, min(1.0, (t - TJ_MEZCLA_INI) / max(1.0, TJ_SAT_MIN - TJ_MEZCLA_INI)))
    return (1.0 - w) * kc + w * ks

def factor_vel(v_kmh):
    """Cuánta más fuerza da el freno del juego a esa velocidad respecto a 100 km/h (1.0 a 100 km/h o más).
    Se limita a 20-100 km/h, que es el rango medido."""
    try:
        v = max(20.0, min(100.0, float(v_kmh)))
    except Exception:
        return 1.0
    return 1.0 + FADING_VEL * (100.0 - v)

def k_freno(v_kmh=None):
    """m/s2 por cada 1.0 de eje con los frenos del juego a la temperatura y velocidad de este instante."""
    if not FRENO_ADAPTATIVO:
        return K_DECEL_POR_EJE
    if v_kmh is None:
        v_kmh = velocidad_actual
    return k_por_temp(terreno_actual.get("temp_juego")) * factor_vel(v_kmh)

def _kmem_cargar():
    if _kmem["cargada"]:
        return
    _kmem["cargada"] = True
    try:
        with open(K_MEMORIA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and d.get("_v") == K_MEMORIA_VERSION:
            _kmem["datos"] = {k: v for k, v in d.items() if k != "_v"}
    except Exception:
        pass

def _kmem_guardar():
    try:
        tmp = K_MEMORIA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dict(_kmem["datos"], _v=K_MEMORIA_VERSION), f, indent=1, ensure_ascii=False)
        os.replace(tmp, K_MEMORIA_FILE)
    except Exception:
        pass

def clave_combinacion(marca, modelo, id_remolque, con_remolque, carga_t):
    """Identifica camión + remolque + carga (la carga en tramos de 5 t: 20.3 t -> 20, 56.0 t -> 55)."""
    base = f"{marca}|{modelo}"
    if not con_remolque:
        return base + "|sin_remolque"
    return f"{base}|{id_remolque or 'sin_id'}|{int(round(max(0.0, float(carga_t)) / 5.0) * 5)}t"

def guardar_k_si_toca():
    """Guarda el k base de la combinación actual si aprendió algo nuevo (se llama al soltar el pedal)."""
    st = _kfreno
    if st["clave"] and (st["nuevo"] >= 8 or st.get("nuevo_s", 0) >= 8):
        rec = {"k": round(st["k"], 2), "n": int(st["n"]), "fecha": time.strftime("%Y-%m-%d %H:%M:%S")}
        if st.get("ks") is not None:
            rec["ks"] = round(st["ks"], 2)
            rec["ns"] = int(st.get("ns", 0))
        _kmem["datos"][st["clave"]] = rec
        st["nuevo"] = 0
        st["nuevo_s"] = 0
        _kmem_guardar()

def seleccionar_combinacion(clave, con_remolque):
    """Cambia al k base de la combinación actual: el guardado si ya la conoce, o un valor de partida si es nueva.
    El cambio debe repetirse 3 lecturas seguidas, para que un tirón de la telemetría no reinicie el aprendizaje."""
    st = _kfreno
    _kmem_cargar()
    if clave == st["clave"]:
        st["cand"], st["cand_n"] = None, 0
        return
    if clave != st["cand"]:
        st["cand"], st["cand_n"] = clave, 1
        return
    st["cand_n"] += 1
    if st["cand_n"] < 3:
        return
    guardar_k_si_toca()
    st["clave"], st["cand"], st["cand_n"] = clave, None, 0
    rec = _kmem["datos"].get(clave)
    if rec:
        st.update({"k": float(rec["k"]), "n": min(int(rec.get("n", 0)), 6), "t_freno": None, "nuevo": 0,
                   "ks": (float(rec["ks"]) if rec.get("ks") is not None else None), "ns": min(int(rec.get("ns", 0)), 6), "nuevo_s": 0})
    else:
        st.update({"k": K_BASE_INICIAL_REMOLQUE if con_remolque else K_BASE_INICIAL, "n": 0, "t_freno": None, "nuevo": 0,
                   "ks": None, "ns": 0, "nuevo_s": 0})

def reiniciar_k_freno():
    """Cambio de camión, partida recargada o teletransporte: guarda lo aprendido y deja que la combinación se vuelva a cargar."""
    guardar_k_si_toca()
    _kfreno.update({"k": K_BASE_INICIAL, "n": 0, "t_freno": None, "clave": None, "cand": None, "cand_n": 0, "nuevo": 0, "ks": None, "ns": 0, "nuevo_s": 0})

def actualizar_k_freno(vel_kmh, pedal, acc_dec, pitch, mb, retarder, ahora):
    """Aprende cuánto frena de verdad el juego por cada 1.0 de eje (cada remolque frena distinto).
    Solo usa frenadas limpias: sin freno de motor ni retarder, ya con el aire dentro, sin agarre al límite."""
    st = _kfreno
    if not (FRENADO_PROGRAMA and FRENO_ADAPTATIVO):
        return
    if not APRENDER_SIN_ID and str(st["clave"] or "").endswith("|sin_id|0t"):
        return          # carga perdida o remolque sin id: aprender aquí contaminaría la clave compartida
    if pedal <= 0.1:
        st["t_freno"] = None
        guardar_k_si_toca()
        return
    if st["t_freno"] is None:
        st["t_freno"] = ahora
    if acc_dec is None or mb or retarder:
        return
    if ahora - st["t_freno"] < 0.9 or vel_kmh < 20.0:      # el aire tarda ~0.7 s en entrar
        return
    eje = pedal * eficacia_global * escala_eje_freno(masa_total_kg())
    if eje < 0.06:      # con eje muy bajo un pequeño error de la compensación pesa demasiado en el k (antes 0.04)
        return
    pend = math.tan(math.radians((pitch or 0.0) * 360.0))     # + = subida
    if abs(pend) > 0.04:
        return
    a_freno = acc_dec - 0.08 - 9.81 * pend                    # quita resistencias (~0.08) y la pendiente
    if a_freno < 1.0 or a_freno > DECEL_AGARRE - 0.4:   # solo frenadas claras: un error de pendiente pesaría demasiado en las suaves
        return
    tj = terreno_actual.get("temp_juego")
    if tj is None:
        return
    if tj > TJ_APRENDER_MAX:
        # Zona saturada (la telemetría no pasa de 200 °C): no sirve para el k base, pero sí para el k_sat (llevado a 100 km/h)
        if tj < TJ_SAT_MIN:
            return
        sat_i = max(5.0, min(45.0, a_freno / eje / factor_vel(vel_kmh)))
        if st.get("ks") is None:
            st["ks"], st["ns"] = sat_i, 1
        else:
            st["ks"] += max(0.12, 1.0 / (st["ns"] + 1.5)) * (sat_i - st["ks"])
            st["ns"] += 1
        st["nuevo_s"] = st.get("nuevo_s", 0) + 1
        return
    k_i = max(6.0, min(45.0, a_freno / eje))                  # lo que frenó el juego con la temperatura de ahora
    base_i = max(10.0, min(60.0, k_i / factor_temp_juego(terreno_actual.get("temp_juego")) / factor_vel(vel_kmh)))   # llevado a frenos a 0 °C y 100 km/h
    st["k"] += max(0.12, 1.0 / (st["n"] + 1.5)) * (base_i - st["k"])   # al principio aprende rápido, luego suave
    st["n"] += 1
    st["nuevo"] += 1

def decel_objetivo(m_kg):
    """Deceleración objetivo (m/s2) a fondo y en frío: límite legal según la masa total, interpolado entre los puntos de la tabla."""
    t = m_kg / 1000.0
    pts = DECEL_LEGAL_TABLA
    if t <= pts[0][0]:
        a = pts[0][1]
    elif t >= pts[-1][0]:
        a = pts[-1][1]
    else:
        a = pts[-1][1]
        for (t0, a0), (t1, a1) in zip(pts, pts[1:]):
            if t <= t1:
                a = a0 + (a1 - a0) * (t - t0) / (t1 - t0)
                break
    return min(DECEL_OBJETIVO_MAX, a)

def eje_enviado(pedal, efic, m_kg):
    """Eje de freno que se manda a vJoy: pedal x eficacia x escala (lo pedido) más la compensación del descuento del juego."""
    eje = max(0.0, pedal) * efic * escala_eje_freno(m_kg)
    if FRENADO_PROGRAMA and eje >= COMP_EJE_MIN:
        eje += COMP_EJE_FRENO
    return max(0.0, min(1.0, eje))

def escala_eje_freno(m_kg):
    """Cuánto del eje de freno se envía al juego para que frene lo que debe (1.0 = sin limitar)."""
    if not FRENADO_PROGRAMA:
        return 1.0
    return min(1.0, decel_objetivo(m_kg) / k_freno())

# Tabla anterior (mod con el fading del juego activo): solo se usa si "frenado_programa" está apagado
DECEL_FRIO_TABLA = [(8.5, 4.45), (35.9, 5.05), (71.5, 4.90)]   # (masa total en t, m/s2)

def decel_max(m_kg):
    """Deceleración con el pedal a fondo y los frenos fríos (m/s2) según la masa total."""
    if FRENADO_PROGRAMA:
        return decel_objetivo(m_kg)
    t = m_kg / 1000.0
    pts = DECEL_FRIO_TABLA
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, a0), (t1, a1) in zip(pts, pts[1:]):
        if t <= t1:
            return a0 + (a1 - a0) * (t - t0) / (t1 - t0)
    return pts[-1][1]

def cp_hierro(T):
    return 450.0 + 0.28 * T      # J/(kg K), hierro fundido

def potencia_disipada(T, v_ms, area):
    tk, ta = T + 273.15, T_AMB + 273.15
    h = 10.0 + 3.5 * (max(v_ms, 0.0) ** 0.8)                  # convección (W/m2K), mejora con el viento
    rad = 0.6 * 0.75 * SIGMA * (tk ** 4 - ta ** 4) / max(T - T_AMB, 0.1)   # radiación (equivalente en W/m2K)
    return area * (h + rad) * (T - T_AMB)

def decel_freno_medida():
    """Deceleración que dan los frenos de servicio ahora mismo (m/s2), según la aceleración que reporta el juego,
    sin resistencias ni pendiente (igual que en actualizar_k_freno). None si no hay dato."""
    a = terreno_actual.get("acc_z")
    if a is None:
        return None
    try:
        pend = math.tan(math.radians(float(terreno_actual.get("pitch") or 0.0) * 360.0))
        return min(12.0, max(0.0, float(a) - 0.08 - 9.81 * pend))
    except Exception:
        return None

# La aceleración que reporta la telemetría se queda ~1 s atrás al soltar el pedal: si el calor se cortara al instante, en el
# frenado a pulsos (bajadas) se perdería ~25 % de la energía. Se sigue calentando HOLD_CALOR_S tras el último pedal > 0.05.
# Con 0 se vuelve al comportamiento anterior (calor solo con el pedal pisado).
HOLD_CALOR_S = 1.0
_calor_hold = {"resto": 0.0}

def paso_termico(T, pedal, v_kmh, efic, dt, k_calor, k_enf, a_med=None):
    v = max(0.0, v_kmh) / 3.6
    m = masa_total_kg()
    p_in = 0.0
    if pedal > 0.05:
        _calor_hold["resto"] = HOLD_CALOR_S
    else:
        _calor_hold["resto"] = max(0.0, _calor_hold["resto"] - dt)
    if (pedal > 0.05 or _calor_hold["resto"] > 0.0) and v > 0.3:
        # El calor es la energía que realmente pierde el camión (masa x deceleración medida x velocidad).
        # Si no hay dato, o si el retarder / freno de motor ayudan (parte de la frenada no calienta los tambores), se usa la nominal como tope.
        a_nom = pedal * decel_max(m) * efic
        if a_med is None:
            a_cal = a_nom
        elif retarder_step or motor_brake_on:
            a_cal = min(a_nom, a_med)
        else:
            a_cal = a_med
        p_in = m * a_cal * v * max(k_calor, 0.01)
    esc = ESCALA_ENFRIAMIENTO_MARCHA + (ESCALA_ENFRIAMIENTO_PARADO - ESCALA_ENFRIAMIENTO_MARCHA) * max(0.0, 1.0 - v_kmh / 10.0)
    p_out = potencia_disipada(T, v, area_frenos_m2()) * max(k_enf, 0.01) * esc
    T += (p_in - p_out) / (masa_frenos_kg() * cp_hierro(T)) * dt
    return max(T_AMB, min(T_MAX, T))

# ==========================================
# MEMORIA TÉRMICA
# Recuerda la temperatura de los frenos según el tiempo y la posición del juego:
#  - Si cargas una partida anterior, vuelves a la temperatura que tenías en ese punto.
#  - Si el tiempo salta hacia adelante (grúa/"volver a la carretera", dormir, copia más nueva),
#    los frenos se enfrían según los minutos de juego que pasaron.
# Se guarda en memoria_termica.json (bórralo para olvidar todo; "memoria_termica": false en la config la apaga).
# ==========================================
MEMORIA_FILE = os.path.join(script_dir, "memoria_termica.json")
TAU_BASE_MIN = 35.0      # minutos de juego que tardan los frenos parados en perder ~63% de su calor
ESCALA_TIEMPO = 19.0     # minutos de juego por minuto real (valor normal de ETS2/ATS)
MAX_RECUERDOS = 4000
_mem = {"snaps": [], "cargada": False, "t_prev": None, "real_prev": 0.0,
        "snap_real": 0.0, "ult_snap": None, "guardado": 0.0,
        "id_prev": None, "odo_prev": None, "pos_prev": None}

def _min_juego(dt):
    return (dt - datetime(1, 1, 1)).total_seconds() / 60.0

def enfriar_por_tiempo(temp, minutos, enf_cfg):
    """Enfría un camión parado durante 'minutos' de tiempo de juego."""
    if minutos <= 0:
        return temp
    k = max(enf_cfg / 0.002, 0.01)
    mb, area = masa_frenos_kg(), area_frenos_m2()
    restante = min(minutos, 1440.0) * 60.0
    while restante > 0 and temp > T_AMB + 0.05:
        dt = min(10.0, restante)
        temp -= potencia_disipada(temp, 0.0, area) * k / (mb * cp_hierro(temp)) * dt
        restante -= dt
    return max(T_AMB, temp)

def _cargar_memoria():
    try:
        with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        _mem["snaps"] = [list(r) for r in datos.get("snaps", []) if isinstance(r, list) and len(r) == 4]
    except Exception:
        _mem["snaps"] = []
    _mem["cargada"] = True

def _guardar_memoria(forzar=False):
    ahora = time.time()
    if not forzar and ahora - _mem["guardado"] < 30.0:
        return
    _mem["guardado"] = ahora
    try:
        tmp = MEMORIA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"v": 1, "snaps": _mem["snaps"]}, f)
        os.replace(tmp, MEMORIA_FILE)
    except Exception:
        pass

def _mejor_recuerdo(t_now, x, z, radio=600.0):
    """Recuerdo más cercano en tiempo (y a menos de 'radio' metros) a este momento del juego."""
    mejor = None
    for r in _mem["snaps"]:
        dt = t_now - r[0]
        if dt < -1.5:
            continue
        if x is not None and z is not None and math.hypot(x - r[1], z - r[2]) > radio:
            continue
        if mejor is None or abs(dt) < abs(t_now - mejor[0]):
            mejor = r
    return mejor

def procesar_memoria_termica(dt_juego, x, z, pausado, id_camion=None, odometro=None):
    global temp_frenos, timestamp_juego_anterior
    if dt_juego is None:
        return
    cfg = cargar_config_cacheada()
    if not cfg.get("memoria_termica", True):
        timestamp_juego_anterior = dt_juego
        return
    if not _mem["cargada"]:
        _cargar_memoria()
    ahora = time.time()
    t_now = _min_juego(dt_juego)
    enf = cfg.get("enf", 0.002)
    t_prev = _mem["t_prev"]
    if t_prev is None:
        # Primera lectura: recupera lo que recordaba de este momento y lugar
        r = _mejor_recuerdo(t_now, x, z)
        if r is None:
            previos = [q for q in _mem["snaps"] if q[0] <= t_now + 1.5]
            r = max(previos, key=lambda q: q[0]) if previos else None
        if r is not None:
            temp_frenos = enfriar_por_tiempo(r[3], max(0.0, t_now - r[0]), enf)
    else:
        esperado = (ahora - _mem["real_prev"]) / 60.0 * ESCALA_TIEMPO
        dgame = t_now - t_prev
        # ¿Otro camión? (otra marca/modelo, o un odómetro que no cuadra con el anterior)
        cambio_camion = False
        if id_camion and _mem["id_prev"] and id_camion != _mem["id_prev"]:
            cambio_camion = True
        elif odometro is not None and _mem["odo_prev"] is not None:
            d_odo = odometro - _mem["odo_prev"]
            if d_odo < -0.5 or d_odo > 25.0:
                cambio_camion = True
        # ¿Se movió de golpe sin que pase el tiempo? (viaje rápido, garaje...)
        salto_pos = False
        if x is not None and z is not None and _mem["pos_prev"] is not None:
            salto_pos = math.hypot(x - _mem["pos_prev"][0], z - _mem["pos_prev"][1]) > 400.0
        restaurado = False
        if dgame < -2.0:
            # Cargaste una partida anterior: vuelve a la temperatura que había en ese punto
            r = _mejor_recuerdo(t_now, x, z)
            if r is not None:
                temp_frenos = enfriar_por_tiempo(r[3], max(0.0, t_now - r[0]), enf)
                _mem["snaps"] = [q for q in _mem["snaps"] if q[0] <= t_now + 1.5]
                _mem["ult_snap"] = None
                _guardar_memoria(True)
                restaurado = True
        if restaurado:
            pass
        elif cambio_camion:
            temp_frenos = T_AMB          # camión nuevo: frenos fríos
            reiniciar_k_freno()
            _mem["ult_snap"] = None
        elif dgame > 3.0 + 2.0 * esperado:
            # Salto hacia adelante (grúa, dormir, copia más nueva): enfría según los minutos de juego que pasaron
            temp_frenos = enfriar_por_tiempo(temp_frenos, dgame - esperado, enf)
        elif salto_pos:
            temp_frenos = T_AMB          # viaje rápido: el tiempo no cambia pero el camión apareció en otro lugar
            _mem["ult_snap"] = None
    _mem["t_prev"] = t_now
    _mem["real_prev"] = ahora
    if id_camion:
        _mem["id_prev"] = id_camion
    if odometro is not None:
        _mem["odo_prev"] = odometro
    if x is not None and z is not None:
        _mem["pos_prev"] = (x, z)
    timestamp_juego_anterior = dt_juego
    # Guarda un recuerdo cada ~4 s reales si te moviste o cambió la temperatura
    if not pausado and ahora - _mem["snap_real"] >= 4.0:
        ult = _mem["ult_snap"]
        movido = x is not None and z is not None and (ult is None or math.hypot(x - ult[1], z - ult[2]) > 20.0)
        cambio = ult is None or abs(temp_frenos - ult[3]) >= 0.5
        if movido or cambio:
            rec = [round(t_now, 2), round(x or 0.0, 1), round(z or 0.0, 1), round(temp_frenos, 1)]
            _mem["snaps"].append(rec)
            _mem["ult_snap"] = rec
            _mem["snap_real"] = ahora
            if len(_mem["snaps"]) > MAX_RECUERDOS:
                del _mem["snaps"][:500]
            _guardar_memoria()

# ==========================================
# MODO CALIBRACIÓN: graba cada frenada de 100 a 0 km/h
# Guarda un archivo por prueba en la carpeta pruebas_frenado y una línea por prueba en resumen.csv.
# Solo graba si el modo está activado (pestaña Calibración) y descarta las pruebas incompletas.
# ==========================================
import csv
PRUEBAS_DIR = os.path.join(script_dir, "pruebas_frenado")
VEL_INICIO_PRUEBA = 100.0
_cal = {"activo": False, "estado": "apagado", "detalle": "", "armado": False, "grabando": False,
        "filas": [], "sin_pedal": None, "ultima": None, "prev": None, "t100": None, "n": 0, "etiqueta": "",
        "tj_antes": None, "tp_antes": None, "tj_ini": None, "tp_ini": None}

def calibracion_etiqueta(texto):
    """Nombre de la serie de pruebas (ej.: C_35t_T250_maxT600). Va en el archivo y en resumen.csv."""
    import re
    limpio = re.sub(r"[^A-Za-z0-9_\-]", "_", str(texto or "").strip())[:40].strip("_")
    _cal["etiqueta"] = limpio
    return limpio

def fijar_temperatura_frenos(valor):
    """Pone los frenos a una temperatura concreta para empezar una prueba desde ahí."""
    global temp_frenos
    if _cal["grabando"]:
        return {"ok": False, "motivo": "Hay una prueba grabándose."}
    try:
        v = float(valor)
    except Exception:
        return {"ok": False, "motivo": "Temperatura no válida."}
    temp_frenos = max(T_AMB, min(T_MAX, v))
    _mem["ult_snap"] = None
    return {"ok": True, "temp": round(temp_frenos, 1)}

def fijar_tope_freno(valor):
    """Limita el pedal de freno a un máximo (0.25, 0.5, 0.75 o 1.0) para repetir pruebas con la misma intensidad."""
    global freno_tope
    try:
        v = float(valor)
    except Exception:
        return {"ok": False, "motivo": "Valor no válido."}
    if v > 1.0:
        v /= 100.0                      # acepta 25 / 50 / 75 / 100 además de 0.25 ...
    freno_tope = max(0.05, min(1.0, v))
    return {"ok": True, "tope": round(freno_tope, 2)}

def calibracion_activar(on):
    global freno_tope
    if not on:
        freno_tope = 1.0                # al salir del modo calibración el freno vuelve a funcionar al 100 %
    _cal.update({"activo": bool(on), "armado": False, "grabando": False, "filas": [], "sin_pedal": None})
    _cal["estado"] = "esperando" if on else "apagado"
    _cal["detalle"] = "Acelera hasta 100 km/h en un tramo recto y plano." if on else ""

def _cal_descartar(motivo):
    _cal.update({"grabando": False, "armado": False, "filas": [], "sin_pedal": None, "prev": None})
    _cal["estado"] = "descartada"
    _cal["detalle"] = motivo + " Ya está lista la siguiente: acelera a 100 km/h."

def _cal_guardar(filas, t_fin, camion, t100=None):
    # Si se conoce el instante exacto en que cruzó los 100 km/h, el tiempo cuenta desde ahí
    t0 = t100 if t100 is not None else filas[0]["t"]
    tiempo = t_fin - t0
    v0 = VEL_INICIO_PRUEBA if t100 is not None else filas[0]["vel"]
    # distancia: integral de la velocidad (trapecios) hasta el instante en que llega a 0
    dist = 0.5 * (v0 + filas[0]["vel"]) / 3.6 * (filas[0]["t"] - t0) if t100 is not None else 0.0
    for a, b in zip(filas, filas[1:]):
        dist += 0.5 * (a["vel"] + b["vel"]) / 3.6 * (b["t"] - a["t"])
    dist += 0.5 * filas[-1]["vel"] / 3.6 * max(0.0, t_fin - filas[-1]["t"])
    # deceleración fila a fila (m/s2) y su pico suavizado con 3 muestras
    dec = [0.0]
    for a, b in zip(filas, filas[1:]):
        dt = b["t"] - a["t"]
        dec.append((a["vel"] - b["vel"]) / 3.6 / dt if dt > 0 else 0.0)
    suav = [sum(dec[max(1, i - 1):i + 2]) / len(dec[max(1, i - 1):i + 2]) for i in range(1, len(dec))] or [0.0]
    pedales = [f["pedal"] for f in filas]
    pitches = [f["pitch"] for f in filas if f["pitch"] is not None]
    pend = math.tan(math.radians(sum(pitches) / len(pitches) * 360.0)) * 100.0 if pitches else 0.0
    cfg = cargar_config_cacheada()
    ahora = time.strftime("%Y%m%d_%H%M%S")
    tj_ini = _cal.get("tj_ini")
    if tj_ini is None:
        tj_ini = filas[0]["temp_juego"]
    tp_ini = _cal.get("tp_ini")
    if tp_ini is None:
        tp_ini = filas[0]["temp"]
    # la etiqueta lleva sola la temperatura del juego al empezar a frenar (juego_26), más lo que hayas escrito tú
    etq = "_".join(x for x in (_cal.get("etiqueta", ""), "" if tj_ini is None else "juego_" + str(int(round(float(tj_ini))))) if x)
    nombre = "prueba_" + ahora + ("_" + etq if etq else "") + ".csv"
    res = {
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"), "archivo": nombre, "etiqueta": etq, "camion": camion,
        "vel_inicial_kmh": round(v0, 1), "tiempo_s": round(tiempo, 2), "distancia_m": round(dist, 1),
        "decel_media_ms2": round(v0 / 3.6 / tiempo, 2) if tiempo > 0 else 0,
        "decel_max_ms2": round(max(suav), 2),
        "pedal_medio": round(sum(pedales) / len(pedales), 2), "pedal_max": round(max(pedales), 2), "pedal_min": round(min(pedales), 2),
        "temp_ini_c": round(tp_ini, 1), "temp_fin_c": round(filas[-1]["temp"], 1),
        "delta_temp_c": round(filas[-1]["temp"] - tp_ini, 1),
        "temp_juego_ini_c": None if tj_ini is None else round(float(tj_ini), 1),
        "temp_juego_fin_c": None if filas[-1]["temp_juego"] is None else round(filas[-1]["temp_juego"], 1),
        "eficacia_min": round(min(f["efic"] for f in filas), 2),
        "carga_t": round(float(cargo_peso), 2), "carga_retenida": bool(carga_retenida), "masa_total_modelo_kg": round(masa_total_kg()),
        "remolque": bool(estado_juego.get("remolque")), "pendiente_media_pct": round(pend, 2),
        "retarder_max_nivel": max(int(f["retarder"] or 0) for f in filas),
        "freno_motor_usado": any(f["mb"] for f in filas),
        "calor_mult": round(cfg.get("calor", 0.078) / 0.078, 2), "enf_mult": round(cfg.get("enf", 0.002) / 0.002, 2),
        "decel_frio_modelo_ms2": round(decel_max(masa_total_kg()), 2),
        "escala_eje_freno": round(escala_eje_freno(masa_total_kg()), 3), "frenado_programa": bool(FRENADO_PROGRAMA), "comp_eje_freno": COMP_EJE_FRENO,
        "k_freno_aprendido": round(k_freno(), 2), "k_base_aprendido": round(_kfreno["k"], 2),
        "k_sat_aprendido": (None if _kfreno.get("ks") is None else round(_kfreno["ks"], 2)), "k_sat_muestras": int(_kfreno.get("ns", 0)),
        "fading_modelo_pct_c": (round(pendiente_fading_remolque(masa_total_kg()) * 100, 3) if estado_juego.get("remolque") else round(FADING_JUEGO * 100, 3)),
        "freno_adaptativo": bool(FRENO_ADAPTATIVO),
        "combinacion": _kfreno["clave"],
    }
    try:
        os.makedirs(PRUEBAS_DIR, exist_ok=True)
        with open(os.path.join(PRUEBAS_DIR, nombre), "w", newline="", encoding="utf-8") as f:
            for k, v in res.items():
                f.write("# " + k + ": " + str(v) + "\n")
            w = csv.writer(f)
            w.writerow(["t_s", "vel_kmh", "pedal", "freno_enviado", "freno_juego", "freno_usuario", "temp_c", "temp_juego_c", "eficacia",
                        "decel_ms2", "acel_z_juego", "pitch_deg", "retarder", "freno_motor", "x", "z"])
            for fila, d in zip(filas, dec):
                w.writerow([round(fila["t"] - t0, 3), round(fila["vel"], 2), round(fila["pedal"], 3), round(fila["enviado"], 3),
                            fila["juego"], fila["usuario"], round(fila["temp"], 1),
                            None if fila["temp_juego"] is None else round(fila["temp_juego"], 1), round(fila["efic"], 3), round(d, 3),
                            fila["acc_z"], None if fila["pitch"] is None else round(fila["pitch"] * 360.0, 2),
                            fila["retarder"], int(bool(fila["mb"])), fila["x"], fila["z"]])
        ruta_res = os.path.join(PRUEBAS_DIR, "resumen.csv")
        cabecera = ",".join(res.keys())
        if os.path.exists(ruta_res):
            with open(ruta_res, "r", encoding="utf-8") as f:
                primera = f.readline().strip()
            if primera != cabecera:       # las columnas cambiaron: se guarda el archivo viejo y se empieza uno nuevo
                os.replace(ruta_res, os.path.join(PRUEBAS_DIR, "resumen_anterior_" + ahora + ".csv"))
        nuevo = not os.path.exists(ruta_res)
        with open(ruta_res, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if nuevo:
                w.writerow(list(res.keys()))
            w.writerow(list(res.values()))
        _cal["n"] += 1
        _cal["estado"] = "guardada"
        _cal["detalle"] = ("Prueba " + str(_cal["n"]) + " guardada: " + str(res["tiempo_s"]) + " s con " + str(res["carga_t"]) +
                           " t. Ya está lista la siguiente: acelera a 100 km/h.")
        _cal["ultima"] = res
    except Exception as e:
        _cal["estado"] = "descartada"
        _cal["detalle"] = "No se pudo guardar el archivo: " + str(e)
    _cal.update({"grabando": False, "armado": False, "filas": [], "sin_pedal": None, "prev": None})

# ==========================================
# REGISTRO CONTINUO (enfriamiento, bajadas largas, freno de motor)
# Graba un CSV con una fila cada REG_PERIODO_S segundos y sin límite de duración, en la carpeta pruebas_frenado.
# Se activa con la casilla "Registro continuo" de la pestaña Calibración, o solo con el modo calibración encendido y una
# etiqueta que empiece por "REG" (ej.: REG_enf_56t_parado). Se cierra al desmarcar la casilla, apagar el modo calibración
# (en el modo por etiqueta), cambiar esa etiqueta o cerrar el programa.
# No interfiere con la grabación de frenadas de 100 a 0 km/h (siguen funcionando igual).
# ==========================================
REG_PERIODO_S = 0.5
REG_COLUMNAS = ["t_s", "hora_juego", "min_juego", "vel_kmh", "pedal", "freno_enviado", "freno_juego", "freno_usuario",
                "temp_modelo_c", "temp_juego_c", "eficacia", "acel_z_juego", "pitch_deg", "retarder", "freno_motor",
                "marcha", "rpm", "acelerador", "freno_mano", "k_freno_actual", "escala_enf", "x", "z"]
_reg = {"f": None, "w": None, "ruta": None, "n": 0, "t0": None, "t_ult": 0.0, "t_flush": 0.0, "etq": "", "h0": None, "manual": False}

def _reg_cerrar():
    f = _reg["f"]
    _reg.update({"f": None, "w": None})
    if f is not None:
        try:
            f.flush()
            f.close()
        except Exception:
            pass

def _reg_abrir(m):
    os.makedirs(PRUEBAS_DIR, exist_ok=True)
    etq = _cal["etiqueta"] or "sin_etiqueta"
    ahora = time.strftime("%Y%m%d_%H%M%S")
    ruta = os.path.join(PRUEBAS_DIR, "registro_" + ahora + "_" + etq + ".csv")
    cfg = cargar_config_cacheada()
    cab = {
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"), "archivo": os.path.basename(ruta), "etiqueta": etq, "camion": m.get("camion"),
        "periodo_s": REG_PERIODO_S, "carga_t": round(float(cargo_peso), 2), "carga_retenida": bool(carga_retenida), "masa_total_modelo_kg": round(masa_total_kg()),
        "remolque": bool(estado_juego.get("remolque")), "combinacion": _kfreno["clave"],
        "masa_frenos_kg": masa_frenos_kg(), "area_frenos_m2": area_frenos_m2(),
        "calor_mult": round(cfg.get("calor", 0.078) / 0.078, 2), "enf_mult": round(cfg.get("enf", 0.002) / 0.002, 2),
        "escala_enf_parado": ESCALA_ENFRIAMIENTO_PARADO, "escala_enf_marcha": ESCALA_ENFRIAMIENTO_MARCHA,
        "comp_eje_freno": COMP_EJE_FRENO, "hold_calor_s": HOLD_CALOR_S, "k_base_aprendido": round(_kfreno["k"], 2),
        "k_sat_aprendido": (None if _kfreno.get("ks") is None else round(_kfreno["ks"], 2)),
        "frenado_programa": bool(FRENADO_PROGRAMA), "freno_adaptativo": bool(FRENO_ADAPTATIVO),
    }
    f = open(ruta, "w", newline="", encoding="utf-8")
    for k, v in cab.items():
        f.write("# " + k + ": " + str(v) + "\n")
    w = csv.writer(f)
    w.writerow(REG_COLUMNAS)
    _reg.update({"f": f, "w": w, "ruta": ruta, "n": 0, "t0": m["t"], "t_ult": 0.0, "t_flush": m["t"], "etq": etq, "h0": m.get("hora")})

atexit.register(_reg_cerrar)

def muestra_registro(m):
    """Se llama con cada lectura de la telemetría (unas 10 por segundo). Escribe una fila cada REG_PERIODO_S."""
    try:
        por_etiqueta = bool(_cal["activo"]) and str(_cal["etiqueta"]).upper().startswith("REG")
        quiere = por_etiqueta or bool(_reg["manual"])
        if _reg["f"] is not None and (not quiere or (not _reg["manual"] and _reg["etq"] != _cal["etiqueta"])):
            _reg_cerrar()
        if not quiere or m["pausado"] or not m["conectado"]:
            return
        if _reg["f"] is None:
            _reg_abrir(m)
        t = m["t"]
        if _reg["n"] > 0 and t - _reg["t_ult"] < REG_PERIODO_S:
            return
        _reg["t_ult"] = t
        v = float(m["vel"])
        hora = m.get("hora")
        esc = ESCALA_ENFRIAMIENTO_MARCHA + (ESCALA_ENFRIAMIENTO_PARADO - ESCALA_ENFRIAMIENTO_MARCHA) * max(0.0, 1.0 - v / 10.0)
        pitch = m.get("pitch")
        tj = m.get("temp_juego")
        _reg["w"].writerow([
            round(t - _reg["t0"], 2), "" if hora is None else hora.strftime("%Y-%m-%d %H:%M:%S"),
            "" if (hora is None or _reg["h0"] is None) else round((hora - _reg["h0"]).total_seconds() / 60.0, 2), round(v, 2), round(m["pedal"], 3), round(m["enviado"], 3),
            m["juego"], m["usuario"], round(m["temp"], 1), None if tj is None else round(float(tj), 1), round(m["efic"], 3),
            m["acc_z"], None if pitch is None else round(pitch * 360.0, 2), m["retarder"], int(bool(m["mb"])),
            m.get("marcha"), m.get("rpm"), m.get("acelerador"), int(bool(m.get("mano"))), round(k_freno(), 2), round(esc, 2),
            m["x"], m["z"]])
        _reg["n"] += 1
        if t - _reg["t_flush"] > 5.0:
            _reg["f"].flush()
            _reg["t_flush"] = t
    except Exception:
        _reg_cerrar()

def muestra_calibracion(m):
    """Se llama con cada lectura de la telemetría (unas 10 por segundo)."""
    if not _cal["activo"]:
        return
    v, t = float(m["vel"]), m["t"]
    if m["pausado"] or not m["conectado"]:
        if _cal["grabando"]:
            _cal_descartar("El juego se pausó durante la prueba.")
        _cal["armado"] = False
        return
    if not _cal["grabando"] and m["pedal"] <= 0.05:
        _cal["tj_antes"], _cal["tp_antes"] = m.get("temp_juego"), m["temp"]    # última lectura con el pedal suelto
    if not _cal["grabando"]:
        if v >= VEL_INICIO_PRUEBA:
            _cal["armado"] = True
            _cal["prev"] = {"t": t, "vel": v}
        elif v >= VEL_INICIO_PRUEBA - 1.0:
            _cal["armado"] = True          # tolerancia de 1 km/h entre el velocímetro y la telemetría
        if _cal["armado"]:
            if m["pedal"] > 0.05 and VEL_INICIO_PRUEBA - 3.0 <= v < VEL_INICIO_PRUEBA:
                p = _cal["prev"]
                t100 = None
                if p and p["vel"] >= VEL_INICIO_PRUEBA > v and t - p["t"] <= 1.0:
                    t100 = p["t"] + (t - p["t"]) * (p["vel"] - VEL_INICIO_PRUEBA) / (p["vel"] - v)
                _cal.update({"grabando": True, "filas": [], "sin_pedal": None, "t100": t100, "prev": None,
                              "tj_ini": _cal["tj_antes"], "tp_ini": _cal["tp_antes"]})     # temperaturas del momento de frenar
                _cal["estado"] = "grabando"
                _cal["detalle"] = "Grabando la frenada..."
            elif v >= VEL_INICIO_PRUEBA - 1.0:
                _cal["estado"] = "listo"
                _cal["detalle"] = "Ya vas a 100 km/h. Frena cuando quieras: se graba hasta llegar a 0."
            else:
                _cal["armado"] = False
                _cal["estado"] = "esperando"
                _cal["detalle"] = "Bajaste de 100 km/h sin frenar. Vuelve a subir a 100 km/h."
        if not _cal["grabando"]:
            return
    filas = _cal["filas"]
    if filas and m["x"] is not None and filas[-1]["x"] is not None and \
            math.hypot(m["x"] - filas[-1]["x"], m["z"] - filas[-1]["z"]) > 400.0:
        return _cal_descartar("El camión se teletransportó durante la prueba.")
    if filas and v > filas[0]["vel"] + 1.0:
        return _cal_descartar("La velocidad volvió a subir por encima de la de inicio.")
    if filas and t - filas[0]["t"] > 240.0:   # antes 90 s: una frenada con los frenos muy calientes puede tardar mas de un minuto
        return _cal_descartar("La prueba duró demasiado.")
    if m["pedal"] <= 0.05:
        if _cal["sin_pedal"] is None:
            _cal["sin_pedal"] = t
        elif t - _cal["sin_pedal"] > 2.0:
            return _cal_descartar("Soltaste el pedal de freno más de 2 segundos.")
    else:
        _cal["sin_pedal"] = None
    filas.append({"t": t, "vel": v, "pedal": m["pedal"], "enviado": m["enviado"], "juego": m["juego"], "usuario": m["usuario"],
                  "temp": m["temp"], "temp_juego": m.get("temp_juego"), "efic": m["efic"], "acc_z": m["acc_z"], "pitch": m["pitch"],
                  "retarder": m["retarder"], "mb": m["mb"], "x": m["x"], "z": m["z"]})
    if v <= 0.5:
        t_fin = t
        if len(filas) >= 2 and filas[-2]["vel"] > v:
            a = filas[-2]
            t_fin = a["t"] + (t - a["t"]) * a["vel"] / (a["vel"] - v)   # instante exacto en que llegó a 0
        try:
            _cal_guardar(filas, t_fin, m["camion"], _cal["t100"])
        except Exception as e:
            _cal_descartar("Error al calcular la prueba (" + str(e) + ").")

def consultar_telemetria():
    global velocidad_actual, rpm_actual, marcha_actual, combustible_litros, combustible_capacidad, temp_agua, presion_aire, freno_mano, juego_conectado, juego_pausado
    global camion_marca, camion_modelo, cargo_nombre, cargo_peso, carga_retenida, cargo_ingresos, origen_ciudad, destino_ciudad, tiempo_restante_contrato_str, tiempo_sueño_str, distancia_restante_km, tiempo_llegada_str
    global motor_brake_on, retarder_step, retarder_max, cruise_control_on, cruise_control_speed, speed_limit, beacon_on, adblue_litros
    global wear_engine, wear_trans, wear_chassis, wear_wheels, wear_trailer, timestamp_juego_anterior, temp_frenos
    sesion_telemetria = requests.Session()
    fallos_telemetria = 0
    
    while True:
        try:
            response = sesion_telemetria.get("http://localhost:25555/api/ets2/telemetry", timeout=0.5)
            data = response.json()
            fallos_telemetria = 0
            game_info = data.get("game", {})
            if game_info.get("connected", False):
                juego_conectado = True
                juego_pausado = game_info.get("paused", False)
                dt_juego = None
                try:
                    time_str = game_info.get("time")
                    if time_str and isinstance(time_str, str):
                        dt_juego = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
                except Exception:
                    dt_juego = None

                truck = data.get("truck", {})
                try:
                    _pl = truck.get("placement", {}) or {}
                    procesar_memoria_termica(dt_juego, _pl.get("x"), _pl.get("z"), juego_pausado,
                                            f'{truck.get("id", "")}|{truck.get("make", "")}|{truck.get("model", "")}',
                                            truck.get("odometer"))
                except Exception:
                    pass
                trailer = data.get("trailer", {})
                job = data.get("job", {})
                navigation = data.get("navigation", {})
                
                velocidad_actual = abs(truck.get("speed", 0.0))
                rpm_actual = truck.get("engineRpm", 0.0)
                if truck.get("make"): camion_marca = str(truck.get("make"))
                if truck.get("model"): camion_modelo = str(truck.get("model"))

                gear_val = truck.get("displayedGear", truck.get("gear", 0))
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

                izq = bool(truck.get("blinkerLeftOn", False))             # palanca puesta (estado fijo)
                der = bool(truck.get("blinkerRightOn", False))
                fase_izq = bool(truck.get("blinkerLeftActive", False))    # la luz está encendida en este instante (parpadea)
                fase_der = bool(truck.get("blinkerRightActive", False))
                estado_juego.update({
                    "motor": bool(truck.get("engineOn", False)),
                    "electrico": bool(truck.get("electricOn", False)),
                    "freno_mano": bool(freno_mano),
                    "luces": 2 if truck.get("lightsBeamLowOn", False) else (1 if truck.get("lightsParkingOn", False) else 0),
                    "altas": bool(truck.get("lightsBeamHighOn", False)),
                    "torretas": bool(beacon_on),
                    "limpiadores": bool(truck.get("wipersOn", False)),
                    "int_izq": izq,
                    "int_der": der,
                    "hazards": izq and der,
                    "fase_izq": fase_izq,
                    "fase_der": fase_der,
                    "remolque": bool(trailer.get("attached", False)),
                    "freno_motor": bool(motor_brake_on),
                    "crucero": bool(cruise_control_on),
                })
                try:
                    _pl2 = truck.get("placement", {}) or {}
                    _ac = truck.get("acceleration", {}) or {}
                    terreno_actual.update({"pitch": _pl2.get("pitch"), "roll": _pl2.get("roll"), "acc_z": _ac.get("z"), "temp_juego": truck.get("brakeTemperature")})
                    _m_cal = {
                        "t": time.perf_counter(), "vel": velocidad_actual, "pedal": freno_vis_global / 100.0,
                        "enviado": eje_enviado(freno_vis_global / 100.0, eficacia_global, masa_total_kg()), "juego": truck.get("gameBrake"),
                        "usuario": truck.get("userBrake"), "temp": temp_frenos, "temp_juego": truck.get("brakeTemperature"), "efic": eficacia_global,
                        "acc_z": _ac.get("z"), "pitch": _pl2.get("pitch"), "retarder": retarder_step, "mb": motor_brake_on,
                        "x": _pl2.get("x"), "z": _pl2.get("z"), "pausado": juego_pausado, "conectado": juego_conectado,
                        "camion": f'{truck.get("make", "")} {truck.get("model", "")}'.strip(),
                        "hora": dt_juego, "marcha": truck.get("displayedGear"), "rpm": truck.get("engineRpm"),
                        "acelerador": truck.get("userThrottle"), "mano": freno_mano}
                    muestra_calibracion(_m_cal)
                    muestra_registro(_m_cal)
                except Exception:
                    pass
                try:
                    actualizar_k_freno(velocidad_actual, freno_vis_global / 100.0, (truck.get("acceleration", {}) or {}).get("z"),
                                       (truck.get("placement", {}) or {}).get("pitch"), motor_brake_on, retarder_step, time.perf_counter())
                except Exception:
                    pass
                
                wear_engine = truck.get("wearEngine", 0.0) * 100.0
                wear_trans = truck.get("wearTransmission", 0.0) * 100.0
                wear_chassis = truck.get("wearChassis", 0.0) * 100.0
                wear_wheels = truck.get("wearWheels", 0.0) * 100.0
                wear_trailer = trailer.get("wear", 0.0) * 100.0
                
                t_name = trailer.get("name")
                cargo_nombre = str(t_name) if t_name and str(t_name).strip() != "" else "Sin carga / Remolque libre"
                t_mass = trailer.get("mass", 0.0)
                cargo_peso = (t_mass / 1000.0) if t_mass > 0 else 0.0
                _con_rem = bool(trailer.get("attached", False))
                _id_rem = trailer.get("id")
                carga_retenida = False
                try:
                    if _con_rem:
                        _carga_ret["fuera"] = 0
                        if cargo_peso > 0:
                            _carga_ret["id"], _carga_ret["masa_t"] = _id_rem, cargo_peso      # lectura válida: se recuerda
                        elif _carga_ret["masa_t"] > 0:
                            # la telemetría perdió la carga con el remolque enganchado: se usa la última válida
                            _id_rem, cargo_peso, carga_retenida = _carga_ret["id"], _carga_ret["masa_t"], True
                    else:
                        _carga_ret["fuera"] += 1
                        if _carga_ret["fuera"] >= CARGA_RET_FUERA_LECTURAS:
                            _carga_ret["id"], _carga_ret["masa_t"] = None, 0.0
                    seleccionar_combinacion(clave_combinacion(camion_marca, camion_modelo, _id_rem, _con_rem, cargo_peso), _con_rem)
                except Exception:
                    pass

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
            # Un solo fallo (por ejemplo un tirón del juego) ya no lo marca como desconectado
            fallos_telemetria += 1
            if fallos_telemetria >= 5:
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

# ------------------------------------------
# Cuidado de vJoy: reposo al abrir/cerrar y reinicio cuando el juego conecta
# (replica lo que haces a mano al abrir el programa con el juego ya abierto)
# ------------------------------------------
_lock_vjoy = threading.Lock()
ultimo_reinicio_vjoy = {"hora": None, "ok": None}

# True  = vJoy se maneja igual que en la versión antigua (sin reposo inicial, sin reinicio automático al conectar el juego
#         y sin soltar vJoy al salir). El botón "Reiniciar controles" sigue funcionando.
# False = activa esos tres cuidados extra.
VJOY_MODO_SIMPLE = True

VJOY_LOG = os.path.join(script_dir, "vjoy_log.txt")
_log_ult = {}
def _log_vjoy(donde, exc=None):
    """Anota en vjoy_log.txt los errores que antes se ignoraban (no repite el mismo error más de una vez cada 30 s)."""
    try:
        txt = donde + (": " + type(exc).__name__ + " " + str(exc) if exc is not None else "")
        ahora = time.time()
        if _log_ult.get(txt, 0) + 30 > ahora:
            return
        _log_ult[txt] = ahora
        with open(VJOY_LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "  " + txt + "\n")
    except Exception:
        pass
_log_vjoy("Programa iniciado (modo simple de vJoy: " + str(VJOY_MODO_SIMPLE) + ")")

def _neutro_vjoy():
    """Deja vJoy en reposo: volante al centro, pedales a 0, botones y cruceta sueltos."""
    if vj is None:
        return
    try:
        d = vj.data
        for nombre in ("bHats", "bHatsEx1", "bHatsEx2", "bHatsEx3"):
            if hasattr(d, nombre):
                setattr(d, nombre, 0xFFFFFFFF)      # cruceta sin pulsar
        if hasattr(d, "lButtons"):
            d.lButtons = 0
    except Exception:
        pass
    try:
        vj.set_axis(pyvjoy.HID_USAGE_X, 16384)
        vj.set_axis(pyvjoy.HID_USAGE_Y, 0)
        vj.set_axis(pyvjoy.HID_USAGE_Z, 0)
    except Exception:
        pass

def reiniciar_vjoy():
    """Suelta y vuelve a tomar vJoy y lo deja en reposo, sin cerrar el programa."""
    global vj
    ok = False
    with _lock_vjoy:
        try:
            if vj is not None:
                for fn in ("reset", "reset_buttons", "reset_povs"):
                    try:
                        getattr(vj, fn)()
                    except Exception:
                        pass
            _neutro_vjoy()
            time.sleep(0.15)
            try:
                vj = pyvjoy.VJoyDevice(1)           # vuelve a tomar el dispositivo, como al abrir el programa
            except Exception as e:
                _log_vjoy("reiniciar_vjoy: no se pudo volver a tomar vJoy 1", e)
            _neutro_vjoy()
            ok = vj is not None
        except Exception as e:
            _log_vjoy("reiniciar_vjoy", e)
            ok = False
    ultimo_reinicio_vjoy.update({"hora": time.strftime("%H:%M:%S"), "ok": ok})
    return ok

def _liberar_vjoy():
    try:
        _neutro_vjoy()
        if vj is not None:
            vj.reset()
    except Exception:
        pass

def _vigilante_vjoy():
    """Cuando el juego conecta tras haber estado cerrado, reinicia vJoy (a los 2 s y a los 12 s)."""
    antes, desde = False, None
    while True:
        time.sleep(0.5)
        ahora = bool(juego_conectado)
        if not ahora and antes:
            desde = time.time()
        if ahora and not antes:
            if desde is None or time.time() - desde > 8.0:    # ignora los parpadeos cortos de la telemetría
                for pausa in (2.0, 10.0):
                    time.sleep(pausa)
                    if not juego_conectado:
                        break
                    reiniciar_vjoy()
        antes = ahora

if not VJOY_MODO_SIMPLE:
    _neutro_vjoy()
    atexit.register(_liberar_vjoy)
    threading.Thread(target=_vigilante_vjoy, daemon=True).start()


def bucle_fisica_y_controles():
    global eficacia_global, freno_vis_global, temp_frenos, FRENADO_PROGRAMA, FRENO_ADAPTATIVO
    t_anterior_fis = time.perf_counter()
    factor_dt = 1.0
    while True:
        try:
            # Normaliza por el tiempo real transcurrido (las constantes siguen calibradas a ~33 ms)
            ahora_fis = time.perf_counter()
            factor_dt = max(0.0, min((ahora_fis - t_anterior_fis) / 0.033, 5.0))
            t_anterior_fis = ahora_fis

            saved_cfg = cargar_config_cacheada()
            FRENADO_PROGRAMA = bool(saved_cfg.get("frenado_programa", True))
            FRENO_ADAPTATIVO = bool(saved_cfg.get("freno_adaptativo", True))
            physical_id = saved_cfg.get("device_id", 0)
            tipo_disp = saved_cfg.get("tipo", "volante")
            invertir_acel = saved_cfg.get("invertir_acel", True)
            mult_calor = saved_cfg.get("calor", 0.078)
            tasa_enf = saved_cfg.get("enf", 0.002)

            volante, acelerador, freno_fisico, botones_mask = leer_ejes_dispositivo(physical_id, tipo_disp, invertir_acel)
            freno_fisico = min(freno_fisico, freno_tope)   # tope de calibración (1.0 = sin límite)
            
            if tipo_disp != "mando" and vj:
                with _lock_vjoy:
                    for i in range(8):
                        estado_boton = 1 if (botones_mask & (1 << i)) != 0 else 0
                        try: vj.set_button(i + 1, estado_boton)
                        except Exception: pass
                    vj.set_axis(pyvjoy.HID_USAGE_X, int(volante * 32767))
                    vj.set_axis(pyvjoy.HID_USAGE_Y, int(acelerador * 32767))

            if juego_conectado and vj:
                if not juego_pausado:
                    temp_frenos = paso_termico(temp_frenos, freno_fisico, velocidad_actual, eficacia_global,
                                               factor_dt * 0.033, mult_calor / 0.078, tasa_enf / 0.002, decel_freno_medida())

            eficacia = eficacia_con_piso(eficacia_por_temp(temp_frenos), velocidad_actual)

            if vj:
                with _lock_vjoy:
                    vj.set_axis(pyvjoy.HID_USAGE_Z, int(eje_enviado(freno_fisico, eficacia, masa_total_kg()) * 32767))

            eficacia_global = eficacia
            freno_vis_global = freno_fisico * 100.0
        except Exception as e:
            _log_vjoy("bucle de controles", e)
        time.sleep(0.033)

threading.Thread(target=bucle_fisica_y_controles, daemon=True).start()

# ==========================================
# SERVIDOR WEB (MÓVIL, OBS & BUTTON PANEL)
# ==========================================
class MobileDashboardHandler(BaseHTTPRequestHandler):
    timeout = 10   # un cliente colgado ya no bloquea nada

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        if path in ('/press', '/down', '/up'):
            key = query_params.get('key', [''])[0].lower()
            if key not in TECLAS_PERMITIDAS:
                self.send_response(403)
                self.end_headers()
                return
            if path == '/press':
                simular_tecla_press(key)
            elif path == '/down':
                simular_tecla_down(key)
            else:
                simular_tecla_up(key)
            self.send_response(200)
            self.end_headers()
            return

        # Paneles servidos desde archivos .html (editables sin tocar Python)
        ARCHIVOS_HTML = {'/': 'movil.html', '/panel': 'sim_panel_button_box.html', '/panel_min': 'sim_panel_minimalista.html',
                         '/obs_top': 'obs_top.html', '/obs_bottom': 'obs_bottom.html', '/video': 'video_overlay.html', '/video2': 'ATS Video Overlay.html'}
        if path in ARCHIVOS_HTML:
            ruta_html = os.path.join(script_dir, ARCHIVOS_HTML[path])
            if os.path.exists(ruta_html):
                with open(ruta_html, "rb") as f:
                    contenido = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(contenido)
                return

        if path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Termofreno - Monitor</title>
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

        elif path == '/panel':
            try:
                with open(PANEL_FILE, "rb") as f:
                    contenido = f.read()
                self.send_response(200)
            except OSError:
                contenido = ("<meta charset='utf-8'><body style='font-family:sans-serif;padding:24px'>"
                             "<h2>No encuentro el panel</h2><p>Pon el archivo <b>sim_panel_button_box.html</b> "
                             "en la misma carpeta que el programa:</p><code>" + script_dir + "</code></body>").encode("utf-8")
                self.send_response(404)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(contenido)

        elif path == '/obs_top':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_top = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Termofreno - Barra superior</title>
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

        elif path == '/obs_bottom':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_bot = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Termofreno - Barra inferior</title>
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

        elif path == '/data':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            _p = terreno_actual.get("pitch")
            pitch_deg = None
            if _p is not None and juego_conectado:
                pitch_deg = float(_p) * 360.0
                if pitch_deg > 180.0: pitch_deg -= 360.0
                pitch_deg = round(pitch_deg, 2)
            data = {
                "temp": temp_frenos, "vel": velocidad_actual, "rpm": rpm_actual, "gear": marcha_actual,
                "aire": presion_aire, "comb": combustible_litros, "cap": combustible_capacidad,
                "marca": camion_marca, "modelo": camion_modelo, "cargo": cargo_nombre, "peso": cargo_peso, "carga_retenida": bool(carga_retenida),
                "ingresos": cargo_ingresos, "origen": origen_ciudad, "destino": destino_ciudad,
                "dist_km": distancia_restante_km, "eta": tiempo_llegada_str, "t_restante": tiempo_restante_contrato_str,
                "sueño": tiempo_sueño_str, "mb_on": motor_brake_on, "retarder": retarder_step, "retarder_max": retarder_max,
                "cc_on": cruise_control_on, "cc_speed": cruise_control_speed, "limit": speed_limit, "beacon": beacon_on,
                "w_eng": wear_engine, "w_tra": wear_trans, "w_cha": wear_chassis, "w_whe": wear_wheels, "w_trl": wear_trailer, "adblue": adblue_litros,
                "conectado": juego_conectado, "pausado": juego_pausado,
                "est": dict(estado_juego),
                "temp_fade": T_INICIO_FADING, "temp_max": T_PERDIDA_TOTAL,
                "efic": round(float(eficacia_global), 3),
                "pitch_deg": pitch_deg, "freno_pct": round(float(freno_vis_global), 1),
                "tmax": T_PERDIDA_TOTAL, "tfade": T_INICIO_FADING
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

# ---- Servidor web (paneles, OBS y QR) con puerto configurable ----
# El puerto sale de "puerto" en config_frenos.json (por defecto 8080). Si está ocupado al arrancar, el programa
# prueba los siguientes (8081, 8082...) y lo avisa en la ventana. Desde la ventana (Inicio > Puerto del panel web)
# se puede cambiar sin reiniciar: el servidor nuevo se abre primero y el viejo se cierra después.
PUERTO_WEB_DEFECTO = 8080
PUERTO_MIN, PUERTO_MAX = 1024, 65535

class _ServidorWeb(ThreadingHTTPServer):
    daemon_threads = True
    # En Windows, SO_REUSEADDR deja que dos programas compartan el mismo puerto sin avisar, asi que ahi va apagado
    # (Windows no bloquea un puerto por conexiones recien cerradas). En otros sistemas solo sirve para reutilizarlo.
    allow_reuse_address = (os.name != "nt")

_WEB = {"servidor": None, "puerto": None, "aviso": "", "error": ""}

def _puerto_valido(p):
    try:
        p = int(p)
    except Exception:
        return None
    return p if PUERTO_MIN <= p <= PUERTO_MAX else None

def puerto_configurado():
    return _puerto_valido(cargar_config_disco().get("puerto", PUERTO_WEB_DEFECTO)) or PUERTO_WEB_DEFECTO

def puerto_web():
    """Puerto en el que escucha el servidor web ahora mismo."""
    return _WEB["puerto"] or puerto_configurado()

def _log_web(msg):
    try:
        with open(os.path.join(script_dir, "termofreno_log.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "  web: " + str(msg) + "\n")
    except Exception:
        pass

def _abrir_servidor(puerto):
    srv = _ServidorWeb(('0.0.0.0', puerto), MobileDashboardHandler)      # OSError si el puerto está ocupado
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def iniciar_servidor_web():
    pedido = puerto_configurado()
    for p in [pedido] + [q for q in range(pedido + 1, pedido + 21) if q <= PUERTO_MAX]:
        try:
            _WEB["servidor"] = _abrir_servidor(p)
            _WEB["puerto"] = p
            if p != pedido:
                _WEB["aviso"] = f"El puerto {pedido} estaba ocupado, así que se usa el {p}."
                _log_web(_WEB["aviso"])
            return
        except OSError:
            continue
        except Exception as e:
            _log_web("no se pudo abrir el puerto %s: %r" % (p, e))
    _WEB["error"] = f"No se pudo abrir ningún puerto desde el {pedido}. Elige otro puerto."
    _log_web(_WEB["error"])

def cambiar_puerto_web(nuevo):
    """Mueve el servidor a otro puerto sin reiniciar el programa. Devuelve {"ok": bool, "puerto"/"error": ...}."""
    p = _puerto_valido(nuevo)
    if p is None:
        return {"ok": False, "error": f"Escribe un número entre {PUERTO_MIN} y {PUERTO_MAX}."}
    if p == _WEB["puerto"]:
        return {"ok": True, "puerto": p}
    try:
        srv = _abrir_servidor(p)
    except OSError:
        return {"ok": False, "error": f"El puerto {p} está ocupado. Prueba con otro número."}
    except Exception as e:
        _log_web("cambiar puerto: %r" % (e,))
        return {"ok": False, "error": "No se pudo abrir ese puerto."}
    viejo = _WEB["servidor"]
    _WEB.update(servidor=srv, puerto=p, aviso="", error="")
    c = cargar_config_disco()
    c["puerto"] = p
    guardar_config_disco(c)
    if viejo is not None:
        threading.Thread(target=lambda: (viejo.shutdown(), viejo.server_close()), daemon=True).start()
    return {"ok": True, "puerto": p}

iniciar_servidor_web()

# ==========================================
# TEMA VISUAL (solo apariencia)
# ==========================================
import math
import tkinter.font as tkfont
T_BG="#131a23"; T_PANEL="#1a2330"; T_ROW="#1f2a39"; T_KEY="#2a3a50"; T_LINE="#33425a"
T_TEXT="#e8edf4"; T_TEXT2="#c3cddb"; T_MUTED="#8d9bb0"
T_AMBER="#ffb347"; T_ON_AMBER="#1b1305"; T_GREEN="#4ade80"; T_RED="#ff6b5e"; T_BLUE="#60a5fa"

def _aclarar(hexc, d=16):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(max(0, min(255, c + d)) for c in (r, g, b))

def _mezcla(c1, c2, t):
    a = [int(c1[i:i+2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(a, b))

def _grad(c1, c2, c3, t):
    return _mezcla(c1, c2, t * 2) if t < .5 else _mezcla(c2, c3, (t - .5) * 2)

def _bg_de(w):
    try:
        return w.cget("bg")
    except Exception:
        return T_BG

def _rr(c, x1, y1, x2, y2, r, **kw):
    """Rectángulo redondeado."""
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    p = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2,
         x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
    return c.create_polygon(p, smooth=True, **kw)

class BotonModerno(tk.Canvas):
    """Botón con relieve: grosor inferior, brillo superior, hover y efecto de hundirse al pulsar."""
    def __init__(self, parent, text="", command=None, bg=T_KEY, fg=T_TEXT, font=("Segoe UI", 9, "bold"), width=None, **kw):
        tk.Canvas.__init__(self, parent, bg=_bg_de(parent), highlightthickness=0, bd=0, cursor="hand2")
        self._t, self._c, self._bg, self._fg, self._wc = text, command, bg, fg, width
        self._f = tkfont.Font(font=font)
        self._h = self._p = False
        self.bind("<Configure>", lambda e: self._dibujar())
        self.bind("<Enter>", lambda e: self._est(h=True))
        self.bind("<Leave>", lambda e: self._est(h=False, p=False))
        self.bind("<ButtonPress-1>", lambda e: self._est(p=True))
        self.bind("<ButtonRelease-1>", self._soltar)
        self._medir()
    def _est(self, h=None, p=None):
        if h is not None: self._h = h
        if p is not None: self._p = p
        self._dibujar()
    def _soltar(self, e):
        dentro = 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height()
        activo = self._p
        self._est(p=False)
        if activo and dentro and self._c:
            self._c()
    def _medir(self):
        tw = self._f.measure(self._t)
        if self._wc:
            tw = max(tw, self._wc * self._f.measure("0"))
        tk.Canvas.configure(self, width=tw + 36, height=self._f.metrics("linespace") + 22)
        self._dibujar()
    def _dibujar(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20: return
        dy = 2 if self._p else 0
        base = _aclarar(self._bg, 14 if self._h else 0)
        _rr(self, 1, 5, w-1, h-1, 12, fill=_aclarar(self._bg, -45), outline="")
        _rr(self, 1, 1+dy, w-1, h-5+dy, 12, fill=base, outline=_aclarar(self._bg, -20))
        _rr(self, 3, 3+dy, w-3, (h-5+dy)//2 + 2, 9, fill=_aclarar(base, 14), outline="")
        self.create_text(w/2, (1 + dy + h - 5 + dy)/2, text=self._t, fill=self._fg, font=self._f)
    def configure(self, cnf=None, **kw):
        kw.update(cnf or {})
        for k, a in (("text", "_t"), ("command", "_c"), ("fg", "_fg"), ("bg", "_bg"), ("width", "_wc")):
            if k in kw: setattr(self, a, kw.pop(k))
        if "font" in kw: self._f = tkfont.Font(font=kw.pop("font"))
        kw.pop("state", None)
        if kw: tk.Canvas.configure(self, **kw)
        self._medir()
    config = configure

def boton(parent, **kw):
    return BotonModerno(parent, **kw)

class SliderTermico(tk.Canvas):
    """Deslizador cuya perilla cambia: llama (más caliente), copo (más frío) o tráiler (zona calibrada)."""
    R = 19
    def __init__(self, parent, from_=0.0, to=1.0, value=0.0, orient=None, caliente_derecha=True, zona=None, command=None, **kw):
        tk.Canvas.__init__(self, parent, height=2*self.R + 12, bg=_bg_de(parent), highlightthickness=0, bd=0, cursor="hand2")
        self._a, self._b, self._v = float(from_), float(to), float(value)
        self._hd, self._z, self._c = caliente_derecha, zona, command
        self.bind("<Configure>", lambda e: self._dibujar())
        self.bind("<Button-1>", self._mover)
        self.bind("<B1-Motion>", self._mover)
    def get(self):
        return self._v
    def set(self, v):
        self._v = max(self._a, min(self._b, float(v)))
        self._dibujar()
        if self._c: self._c(self._v)
    def configure(self, cnf=None, **kw):
        kw.update(cnf or {})
        if "command" in kw: self._c = kw.pop("command")
        if "from_" in kw: self._a = float(kw.pop("from_"))
        if "to" in kw: self._b = float(kw.pop("to"))
        if "value" in kw: self._v = float(kw.pop("value"))
        kw.pop("orient", None)
        if kw: tk.Canvas.configure(self, **kw)
        self._dibujar()
    config = configure
    def _x(self, v):
        m = self.R + 4
        return m + (v - self._a) / (self._b - self._a) * (self.winfo_width() - 2*m)
    def _mover(self, e):
        m = self.R + 4
        f = (e.x - m) / max(1, self.winfo_width() - 2*m)
        self.set(self._a + max(0.0, min(1.0, f)) * (self._b - self._a))
    def _estado(self):
        if self._z and self._z[0] <= self._v <= self._z[1]:
            return "trailer"
        der = self._v > (self._z[1] if self._z else (self._a + self._b) / 2)
        return ("llama" if self._hd else "copo") if der else ("copo" if self._hd else "llama")
    def _dibujar(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 80: return
        R, m, cy = self.R, self.R + 4, h / 2
        izq, der = ("#4cc9f0", "#ff4d2e") if self._hd else ("#ff4d2e", "#4cc9f0")
        _rr(self, m-8, cy-9, w-m+8, cy+9, 9, fill="#0c121a", outline="#2a3a50")
        n = 48
        for i in range(n):
            x1 = m + (w - 2*m) * i / n
            x2 = m + (w - 2*m) * (i + 1) / n + 1
            self.create_rectangle(x1, cy-5, x2, cy+5, fill=_grad(izq, "#ffd166", der, i/(n-1)), outline="")
        self.create_oval(m-5, cy-5, m+5, cy+5, fill=izq, outline="")
        self.create_oval(w-m-5, cy-5, w-m+5, cy+5, fill=der, outline="")
        if self._z:
            _rr(self, self._x(self._z[0]) - 3, cy-12, self._x(self._z[1]) + 3, cy+12, 8, fill="", outline=T_TEXT2, dash=(3, 3))
        kx = self._x(self._v)
        col, icono = {"llama": ("#d9480f", self._llama), "copo": ("#1c7ed6", self._copo),
                      "trailer": ("#2f9e6e", self._trailer)}[self._estado()]
        self.create_oval(kx-R+1, cy-R+4, kx+R+1, cy+R+4, fill="#06090d", outline="")
        self.create_oval(kx-R, cy-R, kx+R, cy+R, fill=_aclarar(col, -35), outline="")
        self.create_oval(kx-R, cy-R, kx+R, cy+R-3, fill=col, outline=_aclarar(col, 45), width=2)
        icono(kx, cy - 1)
    def _llama(self, x, y):
        P = lambda pts: [c for px, py in pts for c in (x + px, y + py)]
        self.create_polygon(P([(0,-14),(5,-7),(9,0),(9,6),(5,11),(0,13),(-5,11),(-9,6),(-8,-1),(-4,-5),(-3,-11)]),
                            smooth=True, fill="#ffb02e", outline="#fff1b8")
        self.create_polygon(P([(0,-3),(4,4),(3,9),(0,10),(-3,9),(-4,4)]), smooth=True, fill="#fff3b0", outline="")
    def _copo(self, x, y):
        for k in range(6):
            a = math.radians(60 * k)
            self.create_line(x, y, x + 12*math.cos(a), y + 12*math.sin(a), fill="#eaf7ff", width=2, capstyle="round")
            bx, by = x + 7*math.cos(a), y + 7*math.sin(a)
            for d in (-45, 45):
                b = a + math.radians(d)
                self.create_line(bx, by, bx + 5*math.cos(b), by + 5*math.sin(b), fill="#eaf7ff", width=2, capstyle="round")
    def _trailer(self, x, y):
        self.create_rectangle(x-15, y-9, x+3, y+3, fill="#f1f5f9", outline="#cbd5e1")
        self.create_polygon(x+5, y-4, x+11, y-4, x+15, y+1, x+15, y+4, x+5, y+4, fill=T_AMBER, outline="#b36b00")
        for cx in (x-10, x-3, x+10):
            self.create_oval(cx-3, y+3, cx+3, y+9, fill="#1b2430", outline="#cbd5e1")

class BarraForma(tk.Canvas):
    """Barra segmentada con una cabeza que cambia según el control (volante, acelerador o freno)."""
    COL = {"volante": ("#4cc9f0", "#8b8cff"), "acelerador": ("#4ade80", "#ffd166"), "freno": ("#ffb347", "#ff4d4d")}
    def __init__(self, parent, tipo="volante"):
        tk.Canvas.__init__(self, parent, height=28, bg=_bg_de(parent), highlightthickness=0, bd=0)
        self._tipo, self._v = tipo, 0.0
        self.bind("<Configure>", lambda e: self._dibujar())
    def __setitem__(self, k, v):
        if k == "value":
            self._v = max(0.0, min(100.0, float(v)))
            self._dibujar()
        else:
            tk.Canvas.__setitem__(self, k, v)
    def configure(self, cnf=None, **kw):
        kw.update(cnf or {})
        if "value" in kw: self._v = max(0.0, min(100.0, float(kw.pop("value"))))
        for k in ("orient", "mode", "length"): kw.pop(k, None)
        if kw: tk.Canvas.configure(self, **kw)
        self._dibujar()
    config = configure
    def _dibujar(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 60: return
        pad, cy, n = 14, h / 2, 26
        c1, c2 = self.COL[self._tipo]
        ancho = (w - 2*pad) / n
        for i in range(n):
            on = (i + .5) / n * 100 <= self._v
            _rr(self, pad + i*ancho + 1, cy-6, pad + (i+1)*ancho - 1, cy+6, 3,
                fill=_mezcla(c1, c2, i/(n-1)) if on else "#243042", outline="")
        x = pad + self._v / 100 * (w - 2*pad)
        col = _mezcla(c1, c2, self._v / 100)
        self.create_oval(x-12, cy-11, x+12, cy+13, fill="#06090d", outline="")
        if self._tipo == "volante":
            self.create_oval(x-10, cy-10, x+10, cy+10, fill=T_BG, outline=col, width=3)
            for a in (90, 210, 330):
                r = math.radians(a)
                self.create_line(x, cy, x + 8*math.cos(r), cy - 8*math.sin(r), fill=col, width=2)
        elif self._tipo == "acelerador":
            self.create_polygon(x-3, cy-11, x+6, cy-11, x+1, cy-2, x+7, cy-2, x-4, cy+11, x-1, cy+2, x-7, cy+2,
                                fill=col, outline="#fff6d6")
        else:
            pts = [(x + 10*math.cos(math.radians(22.5 + 45*k)), cy + 10*math.sin(math.radians(22.5 + 45*k))) for k in range(8)]
            self.create_polygon([c for p in pts for c in p], fill=col, outline="#ffe3e3", width=1)

class TituloFlotante(tk.Canvas):
    """Texto con sombra en capas y una barrita flotante debajo."""
    def __init__(self, parent, text="", font=("Segoe UI", 14, "bold"), fg=T_TEXT, wraplength=420, **kw):
        tk.Canvas.__init__(self, parent, width=wraplength + 20, height=48, bg=_bg_de(parent), highlightthickness=0, bd=0)
        self._t, self._f, self._fg, self._wl = text, font, fg, wraplength
        self._dibujar()
    def _dibujar(self):
        self.delete("all")
        cx = (self._wl + 20) / 2
        for dx, dy, col in ((3, 4, "#0a0f15"), (2, 3, "#18222f"), (1, 1, "#2a3a50")):
            self.create_text(cx+dx, 8+dy, text=self._t, font=self._f, fill=col, width=self._wl, anchor="n", justify="center")
        tid = self.create_text(cx, 8, text=self._t, font=self._f, fill=self._fg, width=self._wl, anchor="n", justify="center")
        bb = self.bbox(tid)
        y2 = bb[3] if bb else 30
        _rr(self, cx-18, y2+5, cx+18, y2+9, 2, fill=T_AMBER, outline="")
        _rr(self, cx-8, y2+11, cx+8, y2+13, 1, fill=_aclarar(T_AMBER, -60), outline="")
        tk.Canvas.configure(self, height=int(y2 + 18))
    def configure(self, cnf=None, **kw):
        kw.update(cnf or {})
        if "text" in kw: self._t = kw.pop("text")
        if "fg" in kw: self._fg = kw.pop("fg")
        if "font" in kw: self._f = kw.pop("font")
        for k in ("bg", "wraplength"): kw.pop(k, None)
        if kw: tk.Canvas.configure(self, **kw)
        self._dibujar()
    config = configure

def barra_oscura(win):
    """Barra de título oscura en Windows 10/11 (si no se puede, se ignora)."""
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        v = ctypes.c_int(1)
        for attr in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v)) == 0:
                break
    except Exception:
        pass

def crear_toplevel(parent):
    w = tk.Toplevel(parent)
    barra_oscura(w)
    return w

def aplicar_tema(raiz):
    st = ttk.Style(raiz)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    st.configure(".", background=T_BG, foreground=T_TEXT, fieldbackground=T_KEY, font=("Segoe UI", 9))
    st.configure("TLabelframe", background=T_BG, bordercolor=T_LINE, lightcolor=T_LINE, darkcolor=T_LINE, borderwidth=1)
    st.configure("TLabelframe.Label", background=T_BG, foreground=T_MUTED, font=("Segoe UI Semibold", 9))
    st.configure("TCombobox", fieldbackground=T_KEY, background=T_KEY, foreground=T_TEXT, arrowcolor=T_AMBER,
                 bordercolor=T_LINE, lightcolor=T_KEY, darkcolor=T_KEY, padding=6)
    st.map("TCombobox", fieldbackground=[("readonly", T_KEY)], foreground=[("readonly", T_TEXT)],
           selectbackground=[("readonly", T_KEY)], selectforeground=[("readonly", T_TEXT)],
           bordercolor=[("focus", T_AMBER)], background=[("active", T_ROW)])
    raiz.option_add("*TCombobox*Listbox.background", T_PANEL)
    raiz.option_add("*TCombobox*Listbox.foreground", T_TEXT)
    raiz.option_add("*TCombobox*Listbox.selectBackground", T_AMBER)
    raiz.option_add("*TCombobox*Listbox.selectForeground", T_ON_AMBER)
    st.configure("Horizontal.TProgressbar", troughcolor=T_KEY, background=T_AMBER, bordercolor=T_LINE,
                 lightcolor=T_AMBER, darkcolor=T_AMBER, thickness=10)
    st.configure("Horizontal.TScale", background=T_AMBER, troughcolor=T_KEY, bordercolor=T_LINE,
                 lightcolor=T_AMBER, darkcolor=T_AMBER)
    raiz.config(bg=T_BG)
    barra_oscura(raiz)

# ==========================================
# 1. VENTANA DE CONFIGURACIÓN INICIAL
# ==========================================
config_final = None

def mostrar_configuracion():
    global config_final
    saved_cfg = cargar_config_disco()
    lang_code = saved_cfg.get("idioma", "es")

    root = tk.Tk()
    aplicar_tema(root)
    root.geometry("460x900")
    root.config(bg=T_BG)
    root.resizable(False, False)

    lbl_title = TituloFlotante(root, wraplength=420)
    lbl_title.pack(pady=(10, 4))
    tk.Frame(root, bg=T_AMBER, height=2).pack(fill="x", padx=25, pady=(0, 4))

    lbl_lang = tk.Label(root, fg=T_TEXT, bg=T_BG, font=("Segoe UI", 9, "bold"))
    lbl_lang.pack(anchor="w", padx=25, pady=2)
    
    combo_lang = ttk.Combobox(root, values=["Español (ES)", "English (EN)"], state="readonly", width=42)
    combo_lang.pack(padx=25, pady=4)
    if lang_code == "en":
        combo_lang.set("English (EN)")
    else:
        combo_lang.set("Español (ES)")

    lbl_tipo = tk.Label(root, fg=T_TEXT, bg=T_BG, font=("Segoe UI", 9, "bold"))
    lbl_tipo.pack(anchor="w", padx=25, pady=2)

    combo_tipo = ttk.Combobox(root, state="readonly", width=42)
    combo_tipo.pack(padx=25, pady=4)

    lbl_disp = tk.Label(root, fg=T_TEXT, bg=T_BG, font=("Segoe UI", 9, "bold"))
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
    chk_invertir = tk.Checkbutton(root, variable=var_invertir, bg=T_BG, fg=T_TEXT, selectcolor=T_KEY, activebackground=T_BG, activeforeground=T_TEXT, font=("Segoe UI", 8, "bold"))
    chk_invertir.pack(anchor="w", padx=25, pady=2)

    frame_test = tk.Frame(root, bg=T_PANEL, highlightbackground=T_LINE, highlightthickness=1)
    frame_test.pack(fill="x", padx=25, pady=6)

    lbl_test_title = tk.Label(frame_test, fg=T_AMBER, bg=T_PANEL, font=("Segoe UI", 8, "bold"))
    lbl_test_title.pack(anchor="w", padx=10, pady=(4, 2))

    frame_v = tk.Frame(frame_test, bg=T_PANEL)
    frame_v.pack(fill="x", padx=10, pady=2)
    lbl_v = tk.Label(frame_v, fg=T_MUTED, bg=T_PANEL, font=("Segoe UI", 8), width=10, anchor="w")
    lbl_v.pack(side="left")
    bar_vol = BarraForma(frame_v, "volante")
    bar_vol.pack(side="left", fill="x", expand=True)

    frame_a = tk.Frame(frame_test, bg=T_PANEL)
    frame_a.pack(fill="x", padx=10, pady=2)
    lbl_a = tk.Label(frame_a, fg=T_MUTED, bg=T_PANEL, font=("Segoe UI", 8), width=10, anchor="w")
    lbl_a.pack(side="left")
    bar_acel = BarraForma(frame_a, "acelerador")
    bar_acel.pack(side="left", fill="x", expand=True)

    frame_f = tk.Frame(frame_test, bg=T_PANEL)
    frame_f.pack(fill="x", padx=10, pady=2)
    lbl_f = tk.Label(frame_f, fg=T_MUTED, bg=T_PANEL, font=("Segoe UI", 8), width=10, anchor="w")
    lbl_f.pack(side="left")
    bar_freno = BarraForma(frame_f, "freno")
    bar_freno.pack(side="left", fill="x", expand=True)

    lbl_status_test = tk.Label(frame_test, fg=T_MUTED, bg=T_PANEL, font=("Segoe UI", 8))
    lbl_status_test.pack(anchor="w", padx=10, pady=(2, 4))

    lbl_calor = tk.Label(root, fg=T_TEXT, bg=T_BG, font=("Segoe UI", 9, "bold"))
    lbl_calor.pack(anchor="w", padx=25, pady=(6, 2))
    
    calor_guardado = saved_cfg.get("calor", 0.078)
    slider_calor = SliderTermico(root, from_=0.001, to=0.800, value=calor_guardado, caliente_derecha=True, zona=(0.05, 0.12))
    slider_calor.pack(fill="x", padx=25, pady=2)
    
    lbl_calor_val = tk.Label(root, fg=T_AMBER, bg=T_BG, font=("Segoe UI", 8))
    lbl_calor_val.pack(anchor="w", padx=25)

    lbl_enf = tk.Label(root, fg=T_TEXT, bg=T_BG, font=("Segoe UI", 9, "bold"))
    lbl_enf.pack(anchor="w", padx=25, pady=(6, 2))
    
    enf_guardado = saved_cfg.get("enf", 0.002)
    slider_enf = SliderTermico(root, from_=0.0001, to=0.0500, value=enf_guardado, caliente_derecha=False, zona=(0.002, 0.02))
    slider_enf.pack(fill="x", padx=25, pady=2)
    
    lbl_enf_val = tk.Label(root, fg=T_AMBER, bg=T_BG, font=("Segoe UI", 8))
    lbl_enf_val.pack(anchor="w", padx=25)

    btn_reset_ini = boton(root, bg=T_KEY, fg=T_TEXT, font=("Segoe UI", 8, "bold"))
    btn_reset_ini.pack(fill="x", padx=25, pady=(8, 2))

    btn_start = boton(root, bg=T_AMBER, fg=T_ON_AMBER, font=("Segoe UI", 10, "bold"))
    btn_start.pack(fill="x", padx=25, pady=10)

    def actualizar_textos_ui(*args):
        curr_lang = "en" if "English" in combo_lang.get() else "es"
        t = TEXTOS[curr_lang]
        
        root.title(t["cfg_title"])
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
    root.update_idletasks()
    root.geometry(f"460x{max(500, root.winfo_reqheight())}")
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
        aplicar_tema(self.root)
        self.root.title(self.t["cfg_title"])
        self.root.geometry("540x575")
        self.root.config(bg=T_BG)
        self.root.resizable(False, False)

        self.construir_menu()

        header_frame = tk.Frame(self.root, bg=T_BG, pady=6)
        header_frame.pack(fill="x")
        
        lbl_flow = TituloFlotante(header_frame, text=self.t["flow_title"], font=("Segoe UI", 15, "bold"), wraplength=480)
        lbl_flow.pack()
        lbl_author = tk.Label(header_frame, text="by El Flacooo", fg=T_AMBER, bg=T_BG, font=("Segoe UI", 9, "italic"))
        lbl_author.pack()
        tk.Frame(self.root, bg=T_AMBER, height=2).pack(fill="x")

        status_frame = ttk.LabelFrame(self.root, text=self.t["server_status"])
        status_frame.pack(fill="x", padx=15, pady=8)

        self.lbl_estado_juego = tk.Label(status_frame, text=self.t["waiting_game"], bg=T_BG, fg=T_RED, font=("Segoe UI", 9, "bold"))
        self.lbl_estado_juego.pack(anchor="w", padx=10, pady=4)

        self.lbl_estado_web = tk.Label(status_frame, text=f"{self.t['web_active']}{obtener_ip_local()}:{puerto_web()}/", bg=T_BG, fg=T_GREEN, font=("Segoe UI", 9))
        self.lbl_estado_web.pack(anchor="w", padx=10, pady=(0, 4))

        links_frame = ttk.LabelFrame(self.root, text=self.t["links_frame"])
        links_frame.pack(fill="both", expand=True, padx=15, pady=5)

        ip_local = obtener_ip_local()
        self.crear_fila_enlace(links_frame, self.t["link_mob"], f"http://{ip_local}:{puerto_web()}/")
        self.crear_fila_enlace(links_frame, self.t["link_top"], f"http://127.0.0.1:{puerto_web()}/obs_top")
        self.crear_fila_enlace(links_frame, self.t["link_bot"], f"http://127.0.0.1:{puerto_web()}/obs_bottom")
        self.crear_fila_enlace(links_frame, self.t["link_panel"], f"http://{ip_local}:{puerto_web()}/panel")

        footer_lbl = tk.Label(self.root, text=self.t["footer_tray"], fg=T_MUTED, bg=T_BG, font=("Segoe UI", 8))
        footer_lbl.pack(pady=4)

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
        frame = tk.Frame(parent, bg=T_ROW, pady=3)
        frame.pack(fill="x", padx=10, pady=2)
        
        lbl_title = tk.Label(frame, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=T_ROW, fg=T_TEXT, width=22, anchor="w")
        lbl_title.pack(side="left")

        link_btn = tk.Label(frame, text=url, fg=T_BLUE, bg=T_ROW, font=("Segoe UI", 9, "underline"), cursor="hand2")
        link_btn.pack(side="left", padx=5)
        link_btn.bind("<Button-1>", lambda e: webbrowser.open(url))

        copy_btn = boton(frame, text="Copiar" if self.lang=="es" else "Copy", font=("Segoe UI", 8), command=lambda: self.copiar_url(url), width=7)
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
                        self.lbl_estado_juego.config(text=f"🟢 Conectado al simulador ({camion_marca} {camion_modelo})" if self.lang=="es" else f"🟢 Connected to simulator ({camion_marca} {camion_modelo})", fg=T_GREEN)
                    else:
                        self.lbl_estado_juego.config(text=self.t["waiting_game"], fg=T_RED)
            except Exception:
                break
            time.sleep(1)

    def abrir_configuracion(self):
        saved_cfg = cargar_config_disco()
        cfg_win = crear_toplevel(self.root)
        cfg_win.title("Configuración de Sensibilidad" if self.lang=="es" else "Sensitivity Configuration")
        cfg_win.geometry("420x490")
        cfg_win.config(bg=T_BG)
        cfg_win.resizable(False, False)

        TituloFlotante(cfg_win, text="⚙️ AJUSTAR SENSIBILIDAD" if self.lang=="es" else "⚙️ ADJUST SENSITIVITY", fg=T_TEXT, wraplength=360).pack(pady=(10, 4))

        lbl_c_txt = "Sensibilidad Calor (Izquierda: Lento | Derecha: Rápido):" if self.lang=="es" else "Heating Sensitivity (Left: Slow | Right: Fast):"
        tk.Label(cfg_win, text=lbl_c_txt, fg=T_TEXT, bg=T_BG, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(5, 2))
        
        calor_val = saved_cfg.get("calor", 0.078)
        s_calor = SliderTermico(cfg_win, from_=0.001, to=0.800, value=calor_val, caliente_derecha=True, zona=(0.05, 0.12))
        s_calor.pack(fill="x", padx=20, pady=2)
        
        lbl_calor_desc = tk.Label(cfg_win, text="", fg=T_AMBER, bg=T_BG, font=("Segoe UI", 8))
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
        tk.Label(cfg_win, text=lbl_e_txt, fg=T_TEXT, bg=T_BG, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 2))
        
        enf_val = saved_cfg.get("enf", 0.002)
        s_enf = SliderTermico(cfg_win, from_=0.0001, to=0.0500, value=enf_val, caliente_derecha=False, zona=(0.002, 0.02))
        s_enf.pack(fill="x", padx=20, pady=2)
        
        lbl_enf_desc = tk.Label(cfg_win, text="", fg=T_AMBER, bg=T_BG, font=("Segoe UI", 8))
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

        btn_reset = boton(cfg_win, text=self.t["reset_cal"], bg=T_KEY, fg=T_TEXT, font=("Segoe UI", 8, "bold"), command=restablecer_predeterminados)
        btn_reset.pack(pady=10)

        def guardar():
            cfg = saved_cfg.copy()
            cfg["calor"] = float(s_calor.get())
            cfg["enf"] = float(s_enf.get())
            guardar_config_disco(cfg)
            messagebox.showinfo("Guardado", "¡Configuración de sensibilidad actualizada correctamente!" if self.lang=="es" else "Sensitivity configuration updated successfully!")
            cfg_win.destroy()

        boton(cfg_win, text="💾 GUARDAR CAMBIOS" if self.lang=="es" else "💾 SAVE CHANGES", bg=T_AMBER, fg=T_ON_AMBER, font=("Segoe UI", 9, "bold"), command=guardar).pack(pady=5)

    def abrir_diagnostico(self):
        diag_win = crear_toplevel(self.root)
        diag_win.title("Diagnóstico de Controles y Frenos" if self.lang=="es" else "Controls and Brakes Diagnostics")
        diag_win.geometry("360x320")
        diag_win.config(bg=T_PANEL)
        diag_win.resizable(False, False)

        TituloFlotante(diag_win, text="🔍 DIAGNÓSTICO EN TIEMPO REAL" if self.lang=="es" else "🔍 REAL-TIME DIAGNOSTICS", fg=T_AMBER, wraplength=360).pack(pady=(10, 4))

        saved_cfg = cargar_config_disco()
        dev_id = saved_cfg.get("device_id", 0)
        tipo = saved_cfg.get("tipo", "volante")
        invertir = saved_cfg.get("invertir_acel", True)

        lbl_v = tk.Label(diag_win, text="Volante: 0%" if self.lang=="es" else "Wheel: 0%", fg=T_TEXT, bg=T_PANEL)
        lbl_v.pack(pady=2)
        lbl_a = tk.Label(diag_win, text="Acelerador: 0%" if self.lang=="es" else "Throttle: 0%", fg=T_TEXT, bg=T_PANEL)
        lbl_a.pack(pady=2)
        lbl_f = tk.Label(diag_win, text="Freno: 0%" if self.lang=="es" else "Brake: 0%", fg=T_TEXT, bg=T_PANEL)
        lbl_f.pack(pady=2)
        lbl_t = tk.Label(diag_win, text="Temp. Frenos: 25.0 °C" if self.lang=="es" else "Brake Temp: 25.0 °C", fg=T_TEXT, bg=T_PANEL, font=("Segoe UI", 11, "bold"))
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
        cred_win = crear_toplevel(self.root)
        cred_win.title("Créditos y Agradecimientos" if self.lang=="es" else "Credits and Acknowledgements")
        cred_win.geometry("420x310")
        cred_win.config(bg=T_BG)
        cred_win.resizable(False, False)

        TituloFlotante(cred_win, text="⭐ CRÉDITOS Y AGRADECIMIENTOS" if self.lang=="es" else "⭐ CREDITS AND ACKNOWLEDGEMENTS", fg=T_TEXT, wraplength=360).pack(pady=(10, 4))
        
        texto = (
            "Este programa de simulación térmica utiliza como base indispensable "
            "el servidor de telemetría de Funbit para American Truck Simulator y Euro Truck Simulator 2.\n\n"
            "¡Un agradecimiento especial a Funbit por su excelente trabajo de código abierto!"
            if self.lang=="es" else
            "This thermal simulation program uses Funbit's telemetry server "
            "for American Truck Simulator and Euro Truck Simulator 2 as an indispensable base.\n\n"
            "Special thanks to Funbit for their excellent open source work!"
        )
        tk.Label(cred_win, text=texto, fg=T_TEXT2, bg=T_BG, wraplength=380, justify="center", font=("Segoe UI", 9)).pack(pady=5)

        url = "https://github.com/funbit/ets2-telemetry-server"
        link_btn = tk.Label(cred_win, text=url, fg=T_BLUE, bg=T_BG, font=("Segoe UI", 9, "underline"), cursor="hand2")
        link_btn.pack(pady=10)
        link_btn.bind("<Button-1>", lambda e: webbrowser.open(url))

        boton(cred_win, text="Cerrar" if self.lang=="es" else "Close", bg=T_KEY, fg=T_TEXT, command=cred_win.destroy).pack(pady=5)

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
            image = _imagen_bandeja()
            menu = pystray.Menu(
                pystray.MenuItem('Restaurar Ventana' if self.lang=="es" else 'Restore Window', self.restaurar_desde_bandeja, default=True),
                pystray.MenuItem('Salir' if self.lang=="es" else 'Exit', self.salir_programa)
            )
            self.tray_icon = pystray.Icon("Termofreno", image, "Termofreno", menu)
            self.tray_icon.run()
        except Exception:
            pass


# ==========================================
# FLUJO DE EJECUCIÓN PRINCIPAL
# ==========================================
# ==========================================
# VENTANA PRINCIPAL EN HTML (pywebview)
# Requiere:  pip install pywebview segno
# Si falta pywebview o el archivo ventana_principal.html, el programa abre las ventanas de Tkinter de siempre.
# ==========================================
VENTANA_HTML = os.path.join(script_dir, "ventana_principal.html")

# ---- Alertas sonoras de temperatura de frenos ----
# Fading: un "bip" suave que se repite cada vez mas seguido conforme sube el calor.
# Sin frenos: rafaga de 4 pitidos cortos "tin tin tin tin" cada 2 segundos.
ALERTAS_ACTIVAS = True
VOLUMEN_ALERTAS = 0.8          # 0.0 a 1.0 (se ajusta desde la ventana: pestaña Frenos)

def _fijar_alertas(valor):
    global ALERTAS_ACTIVAS
    ALERTAS_ACTIVAS = bool(valor)

def _crear_wav(eventos, total):
    """Genera en memoria un WAV mono de 16 bits. eventos = (inicio_s, frecuencia_hz, duracion_s, volumen, armonico)."""
    import io, wave, struct
    sr = 22050
    n = int(total * sr)
    buf = [0.0] * n
    for t0, f, dur, vol, arm in eventos:
        i0 = int(t0 * sr)
        for k in range(int(dur * sr)):
            if i0 + k >= n:
                break
            t = k / sr
            env = min(1.0, k / (0.004 * sr)) * math.exp(-5.0 * t / dur)
            buf[i0 + k] += vol * env * (math.sin(2 * math.pi * f * t) + arm * math.sin(4 * math.pi * f * t)) / (1 + arm)
    datos = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, x)) * 32767 * VOLUMEN_ALERTAS)) for x in buf)
    bio = io.BytesIO()
    w = wave.open(bio, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(datos)
    w.close()
    return bio.getvalue()

_SONIDOS = {}

def _fijar_volumen(porcentaje):
    """Volumen de las alertas, de 0 a 100. Se regeneran los sonidos con el volumen nuevo."""
    global VOLUMEN_ALERTAS
    VOLUMEN_ALERTAS = max(0.0, min(100.0, float(porcentaje))) / 100.0
    _SONIDOS.clear()

def _sonido(n):
    if n not in _SONIDOS:
        if n == 1:      # bip del fading
            _SONIDOS[n] = _crear_wav([(0.0, 880.0, 0.22, 0.9, 0.0)], 0.26)
        else:           # tin tin tin tin
            _SONIDOS[n] = _crear_wav([(i * 0.17, 2300.0, 0.11, 1.0, 0.5) for i in range(4)], 0.66)
    return _SONIDOS[n]

def _reproducir(n):
    try:
        import winsound
        winsound.PlaySound(_sonido(n), winsound.SND_MEMORY)     # sincrono: dentro de su propio hilo
    except Exception:
        pass

def _bucle_alertas():
    estado, proximo = 0, 0.0
    while True:
        time.sleep(0.1)
        try:
            if not (ALERTAS_ACTIVAS and juego_conectado and not juego_pausado):
                estado = 0
                continue
            T = float(temp_frenos)
            if T >= T_PERDIDA_TOTAL:
                nuevo = 2
            elif T > T_INICIO_FADING:
                nuevo = 2 if (estado == 2 and T >= T_PERDIDA_TOTAL - 5.0) else 1
            else:
                nuevo = 1 if (estado == 1 and T > T_INICIO_FADING - 5.0) else 0
            ahora = time.time()
            if nuevo != estado:
                estado, proximo = nuevo, ahora          # al entrar a una zona suena de inmediato
            if estado and ahora >= proximo:
                if estado == 1:
                    _reproducir(1)
                    frac = (T - T_INICIO_FADING) / max(1.0, T_PERDIDA_TOTAL - T_INICIO_FADING)
                    proximo = time.time() + 3.0 - 1.5 * max(0.0, min(1.0, frac))   # de 3 s a 1.5 s
                else:
                    _reproducir(2)
                    proximo = time.time() + 2.0
        except Exception:
            pass

# ---- Mini ventana flotante: solo manometro y estado, siempre encima, se mueve arrastrando ----
MINI_HTML = os.path.join(script_dir, "mini_ventana.html")
MINI_TITULO = "Termofreno mini"
_VENT = {"main": None, "mini": None}
_OPACIDADES = (100, 80, 60)

def _log(msg):
    """Anota problemas en termofreno_log.txt (junto al programa) para poder ver por que algo no aparece."""
    try:
        with open(os.path.join(script_dir, "termofreno_log.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg) + "\n")
    except Exception:
        pass

def _opacidad_ventana(titulo, pct):
    """Transparencia de una ventana de Windows por su titulo (100 = opaca). Si falla, no pasa nada."""
    try:
        u = ctypes.windll.user32
        hwnd = u.FindWindowW(None, titulo)
        if not hwnd:
            return False
        estilo = u.GetWindowLongW(hwnd, -20)                      # GWL_EXSTYLE
        u.SetWindowLongW(hwnd, -20, estilo | 0x80000)             # WS_EX_LAYERED
        u.SetLayeredWindowAttributes(hwnd, 0, int(255 * max(20, min(100, pct)) / 100), 2)   # LWA_ALPHA
        return True
    except Exception:
        return False

def _mantener_encima(titulo):
    """Para que la mini ventana siga visible sobre el juego en pantalla completa:
    - no roba el foco (si lo robara, el juego en pantalla completa se minimiza),
    - no sale en Alt+Tab ni en la barra de tareas,
    - se vuelve a poner 'siempre encima' cada segundo, porque el juego la tapa al cambiar de modo."""
    try:
        u = ctypes.windll.user32
        hwnd = 0
        for _ in range(30):
            hwnd = u.FindWindowW(None, titulo)
            if hwnd:
                break
            time.sleep(0.2)
        if not hwnd:
            return
        estilo = u.GetWindowLongW(hwnd, -20)
        u.SetWindowLongW(hwnd, -20, estilo | 0x08000000 | 0x80)          # WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
        while _VENT["mini"] is not None:
            u.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0040)   # HWND_TOPMOST, sin mover/activar
            time.sleep(1.0)
    except Exception:
        pass

def _guardar_pos_mini():
    """Recuerda posicion y tamano de la mini ventana para la proxima vez."""
    try:
        m = _VENT["mini"]
        if m is None:
            return
        c = cargar_config_disco()
        c.update({"mini_x": int(m.x), "mini_y": int(m.y), "mini_w": int(m.width), "mini_h": int(m.height)})
        guardar_config_disco(c)
    except Exception:
        pass

def _mini_cerrada():
    """Pase lo que pase (boton, Alt+F4), la ventana completa vuelve a mostrarse."""
    _VENT["mini"] = None
    try:
        m = _VENT["main"]
        m.show()
        m.restore()
    except Exception:
        pass

class ApiVentana:
    """Funciones que la ventana HTML puede llamar."""
    def abrir_mini(self):
        """Abre la mini ventana flotante. La completa solo se esconde cuando la mini ya aparecio en pantalla."""
        try:
            import webview
        except Exception as e:
            _log("mini: no se pudo importar webview: %r" % (e,))
            return {"ok": False, "error": "Falta pywebview."}
        if _VENT["mini"] is not None:
            return {"ok": True}
        if _VENT["main"] is None:
            return {"ok": False, "error": "No se encontro la ventana principal."}
        if not os.path.exists(MINI_HTML):
            _log("mini: falta el archivo " + MINI_HTML)
            return {"ok": False, "error": "Falta el archivo mini_ventana.html: copialo en la misma carpeta que el programa."}
        c = cargar_config_disco()
        kw = {}
        if c.get("mini_x") is not None and c.get("mini_y") is not None:
            kw.update(x=int(c["mini_x"]), y=int(c["mini_y"]))
        listo = threading.Event()
        try:
            mini = webview.create_window(MINI_TITULO, MINI_HTML, js_api=ApiVentana(),
                                         width=int(c.get("mini_w", 260)), height=int(c.get("mini_h", 250)), min_size=(170, 170),
                                         frameless=True, easy_drag=True, on_top=True, background_color="#131a23", **kw)
        except Exception as e:
            _log("mini: create_window fallo: %r" % (e,))
            return {"ok": False, "error": "No se pudo crear la mini ventana (mira termofreno_log.txt)."}
        _VENT["mini"] = mini
        try:
            mini.events.closing += _guardar_pos_mini
            mini.events.closed += _mini_cerrada
            mini.events.shown += listo.set
            mini.events.shown += lambda: threading.Thread(target=_mantener_encima, args=(MINI_TITULO,), daemon=True).start()
            mini.events.shown += lambda: threading.Thread(target=_poner_icono_ventana, args=(MINI_TITULO,), daemon=True).start()
            mini.events.shown += lambda: threading.Thread(
                target=lambda: (time.sleep(0.6), _opacidad_ventana(MINI_TITULO, int(cargar_config_disco().get("mini_op", 100)))), daemon=True).start()
        except Exception as e:
            _log("mini: eventos: %r" % (e,))
        if not listo.wait(6.0):                     # la mini no llego a mostrarse: la completa se queda donde esta
            _log("mini: la ventana no aparecio en 6 s")
            _VENT["mini"] = None
            try:
                mini.destroy()
            except Exception:
                pass
            return {"ok": False, "error": "La mini ventana no pudo abrirse (mira termofreno_log.txt)."}
        try:
            _VENT["main"].hide()
        except Exception as e:
            _log("mini: no se pudo esconder la completa: %r" % (e,))
        return {"ok": True}

    def mini_volver(self):
        """Cierra la mini ventana y vuelve a la completa."""
        mini = _VENT["mini"]
        if mini is None:
            return False
        _guardar_pos_mini()
        _mini_cerrada()                      # primero se muestra la completa para que el programa nunca se quede sin ventana
        try:
            mini.destroy()
        except Exception:
            pass
        return True

    def mini_opacidad(self):
        """Cicla 100 % -> 80 % -> 60 % de opacidad."""
        c = cargar_config_disco()
        actual = int(c.get("mini_op", 100))
        sig = _OPACIDADES[(_OPACIDADES.index(actual) + 1) % len(_OPACIDADES)] if actual in _OPACIDADES else 100
        c["mini_op"] = sig
        guardar_config_disco(c)
        _opacidad_ventana(MINI_TITULO, sig)
        return sig

    def estado(self):
        return {"juego": bool(juego_conectado), "pausado": bool(juego_pausado), "vjoy": vj is not None, "web": _WEB["servidor"] is not None,
                "temp": round(float(temp_frenos), 1), "vel": round(float(velocidad_actual), 1),
                "efic": round(float(eficacia_global), 3), "tmax": T_PERDIDA_TOTAL, "tfade": T_INICIO_FADING}

    def config(self):
        c = cargar_config_disco()
        return {"device_id": int(c.get("device_id", 0)), "tipo": c.get("tipo", "volante"),
                "invertir_acel": bool(c.get("invertir_acel", True)),
                "calor": float(c.get("calor", 0.078)), "enf": float(c.get("enf", 0.002)),
                "frenado_programa": bool(c.get("frenado_programa", True)),
                "freno_adaptativo": bool(c.get("freno_adaptativo", True)),
                "alertas_sonoras": bool(c.get("alertas_sonoras", True)),
                "volumen_alertas": int(c.get("volumen_alertas", 80)),
                "reducir_anim": bool(c.get("reducir_anim", False)),
                "tema": "dia" if c.get("tema") == "dia" else "noche",
                # quien ya tenia el programa configurado no ve el asistente de primera vez
                "asistente_visto": bool(c.get("asistente_visto", "device_id" in c))}

    def guardar(self, parcial):
        try:
            c = cargar_config_disco()
            c.update({k: v for k, v in parcial.items() if k in ("device_id", "tipo", "invertir_acel", "alertas_sonoras", "volumen_alertas", "calor", "enf", "frenado_programa", "freno_adaptativo", "reducir_anim", "tema", "asistente_visto")})
            guardar_config_disco(c)
            if "alertas_sonoras" in parcial:
                _fijar_alertas(parcial["alertas_sonoras"])
            if "volumen_alertas" in parcial:
                _fijar_volumen(parcial["volumen_alertas"])
            return True
        except Exception:
            return False

    def probar_alerta(self, n):
        threading.Thread(target=_reproducir, args=(1 if int(n) == 1 else 2,), daemon=True).start()
        return True

    def dispositivos(self):
        return [{"id": i, "nombre": n} for n, i in obtener_dispositivos_activos()]

    def ejes(self, dev_id, tipo, invertir):
        vol, acel, freno, _ = leer_ejes_dispositivo(int(dev_id), tipo, bool(invertir))
        return {"vol": float(vol), "acel": float(acel), "freno": float(freno)}

    def inclinacion(self):
        """Inclinación del terreno bajo el camión en tiempo real (pitch: + = subida, igual que en actualizar_k_freno)."""
        t = terreno_actual
        if not juego_conectado or t["pitch"] is None:
            return {"ok": False}
        grados = float(t["pitch"]) * 360.0
        lateral = None if t["roll"] is None else float(t["roll"]) * 360.0
        if lateral is not None and lateral > 180.0:
            lateral -= 360.0
        if grados > 180.0:
            grados -= 360.0
        return {"ok": True, "grados": round(grados, 2), "pend_pct": round(math.tan(math.radians(grados)) * 100.0, 2),
                "lateral": None if lateral is None else round(lateral, 2),
                "acc_z": None if t["acc_z"] is None else round(float(t["acc_z"]), 2),
                "limite_pct": 4.0, "pausado": bool(juego_pausado)}

    def qr(self, destino):
        url = f"http://{obtener_ip_local()}:{puerto_web()}/" + ("panel" if destino == "panel" else "")
        svg = ""
        try:
            import segno
            svg = segno.make(url, error="m").svg_inline(scale=6, border=1, dark="#101620", light="#ffffff")
        except Exception:
            pass
        return {"url": url, "svg": svg}

    def puerto(self):
        return {"puerto": puerto_web(), "aviso": _WEB["aviso"], "error": _WEB["error"]}

    def cambiar_puerto(self, nuevo):
        return cambiar_puerto_web(nuevo)

    def enlaces_obs(self):
        """Enlaces de OBS de las paginas que existen junto al programa (la carpeta publica solo trae las barras)."""
        base = f"http://127.0.0.1:{puerto_web()}"
        todos = [("Barra superior", "/obs_top", "obs_top.html"),
                 ("Barra inferior", "/obs_bottom", "obs_bottom.html"),
                 ("Overlay de video (horizontal)", "/video?fondo=transparente", "video_overlay.html"),
                 ("Overlay de video (vertical, TikTok)", "/video?modo=tiktok&fondo=transparente", "video_overlay.html"),
                 ("Overlay de video B (1920x1080)", "/video2", "ATS Video Overlay.html")]
        return [[n, base + r] for n, r, arch in todos if os.path.exists(os.path.join(script_dir, arch))]

    def abrir(self, url):
        webbrowser.open(url)
        return True

    def reiniciar_controles(self):
        ok = reiniciar_vjoy()
        return {"ok": ok, "hora": ultimo_reinicio_vjoy["hora"]}

    def calibracion(self):
        return {"activo": _cal["activo"], "estado": _cal["estado"], "detalle": _cal["detalle"],
                "ultima": _cal["ultima"], "n": _cal["n"], "temp": round(float(temp_frenos), 1), "etiqueta": _cal["etiqueta"], "carpeta": PRUEBAS_DIR, "vel": round(float(velocidad_actual), 1), "tope": round(float(freno_tope), 2),
                "temp_juego": (round(float(terreno_actual["temp_juego"]), 1) if (juego_conectado and terreno_actual["temp_juego"] is not None) else None),
                "tmax": T_PERDIDA_TOTAL, "tfade": T_INICIO_FADING,
                "tj_ini": _cal["tj_ini"], "tp_ini": _cal["tp_ini"]}

    def calibracion_activar(self, on):
        calibracion_activar(on)
        return True

    def fijar_temperatura(self, valor):
        return fijar_temperatura_frenos(valor)

    def fijar_tope_freno(self, valor):
        return fijar_tope_freno(valor)

    def calibracion_etiqueta(self, texto):
        return calibracion_etiqueta(texto)

    def registro(self):
        return {"activo": _reg["f"] is not None, "manual": bool(_reg["manual"]), "filas": _reg["n"],
                "archivo": (os.path.basename(_reg["ruta"]) if (_reg["ruta"] and _reg["f"] is not None) else None)}

    def registro_activar(self, on):
        _reg["manual"] = bool(on)      # el archivo se abre y se cierra en el hilo de la telemetría
        return True

    def abrir_carpeta(self):
        os.makedirs(PRUEBAS_DIR, exist_ok=True)
        try:
            os.startfile(PRUEBAS_DIR)
        except Exception:
            webbrowser.open(PRUEBAS_DIR)
        return True

    def diagnostico(self):
        web = _WEB["servidor"] is not None          # antes se comprobaba conectando al 8080, y otro programa en ese puerto daba falso "ok"
        reales = [n for n, _i in obtener_dispositivos_activos() if "Genérico" not in n]
        return [
            {"nombre": "Juego (telemetría)", "ok": bool(juego_conectado),
             "detalle": "Conectado" if juego_conectado else "Abre el juego con el plugin de telemetría (puerto 25555)"},
            {"nombre": "vJoy", "ok": vj is not None,
             "detalle": ("Listo" + (" (último reinicio de controles a las " + ultimo_reinicio_vjoy["hora"] + ")" if ultimo_reinicio_vjoy["hora"] else ""))
             if vj is not None else "No se encontró el dispositivo 1 de vJoy"},
            {"nombre": "Servidor web", "ok": web,
             "detalle": (f"Puerto {puerto_web()} activo" + (" · " + _WEB["aviso"] if _WEB["aviso"] else "")) if web
                        else ((_WEB["error"] or "El servidor web no arrancó") + " Cámbialo en Inicio > Puerto del panel web.")},
            {"nombre": "Volante o mando", "ok": bool(reales),
             "detalle": f"{len(reales)} detectado(s)" if reales else "No se detecta ninguno: conéctalo y vuelve a comprobar"},
            {"nombre": "Memoria térmica", "ok": os.path.exists(MEMORIA_FILE),
             "detalle": f"{len(_mem['snaps'])} recuerdos guardados" if os.path.exists(MEMORIA_FILE) else "Se crea sola tras unos minutos conduciendo"},
        ]

def ocultar_consola_propia():
    """Oculta la ventana negra de Python si la abrió el propio programa (doble clic).
    Si lo ejecutas desde una terminal tuya, no la toca."""
    try:
        k = ctypes.windll.kernel32
        hwnd = k.GetConsoleWindow()
        if not hwnd:
            return
        procesos = (ctypes.c_uint * 8)()
        if k.GetConsoleProcessList(procesos, 8) <= 1:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

# ---- Icono del programa: manómetro de tablero de camión (ver iconos/hacer_icono.py) ----
def dibujar_icono(tam=256, valor=0.74):
    """Manómetro 0-450 °C. Los tamaños chicos (<=48) salen simplificados para que se lean."""
    import math
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
    simple = tam <= 48
    S = max(512, min(2048, tam * 4))          # se dibuja grande y se reduce (bordes suaves)
    K = S / 1024.0
    c = 512
    def q(*v): return [x * K for x in v]
    def disco(r, fill, cx=c, cy=c): ImageDraw.Draw(img).ellipse(q(cx - r, cy - r, cx + r, cy + r), fill=fill)
    def mezcla(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    def fuente(px):
        for n in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            try: return ImageFont.truetype(n, int(px * K))
            except Exception: pass
        return None
    IN, FIN = 135.0, 405.0
    def ang(f): return IN + (FIN - IN) * f
    def pol(r, grados): a = math.radians(grados); return c + r * math.cos(a), c + r * math.sin(a)

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ---- bisel cromado (reflejos cónicos) + biseles oscuros
    for g in range(0, 360, 2):
        t = math.cos(math.radians(g * 2 - 50))
        v = int(128 + 100 * t)
        d.pieslice(q(c - 508, c - 508, c + 508, c + 508), g, g + 3, fill=(v, min(255, v + 6), min(255, v + 18), 255))
    d.ellipse(q(c - 508, c - 508, c + 508, c + 508), outline=(10, 12, 16, 255), width=max(1, int(7 * K)))
    disco(462, (200, 208, 222, 255)); disco(456, (46, 52, 64, 255)); disco(446, (12, 14, 18, 255))

    # ---- esfera con degradado (luz desde arriba a la izquierda)
    N = 70
    for i in range(N):
        t = i / (N - 1)
        r = 426 * (1 - t * 0.92)
        disco(r, mezcla((6, 8, 12), (34, 42, 58), t ** 1.4) + (255,), cx=c - 60 * t, cy=c - 90 * t)
    mask_cara = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask_cara).ellipse(q(c - 426, c - 426, c + 426, c + 426), fill=255)
    # recorte de lo que se salió del círculo
    img.putalpha(ImageChops.lighter(img.getchannel("A"), Image.new("L", (S, S), 0)))
    d = ImageDraw.Draw(img)

    # ---- arco de zonas con resplandor
    R_ARCO, ANCHO = (362, 100) if simple else (356, 44)
    zonas = [(0.0, 0.44, (40, 214, 108)), (0.44, 0.80, (255, 176, 32)), (0.80, 1.0, (255, 61, 46))]
    brillo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(brillo)
    for f0, f1, col in zonas:
        bd.arc(q(c - R_ARCO, c - R_ARCO, c + R_ARCO, c + R_ARCO), ang(f0), ang(f1), fill=col + (230,), width=int((ANCHO + 18) * K))
    if not simple:
        img = Image.alpha_composite(img, brillo.filter(ImageFilter.GaussianBlur(14 * K)))
    d = ImageDraw.Draw(img)
    for f0, f1, col in zonas:
        d.arc(q(c - R_ARCO, c - R_ARCO, c + R_ARCO, c + R_ARCO), ang(f0), ang(f1), fill=col + (255,), width=int(ANCHO * K))
    if not simple:                              # filo claro en el borde exterior del arco
        for f0, f1, col in zonas:
            d.arc(q(c - R_ARCO - 20, c - R_ARCO - 20, c + R_ARCO + 20, c + R_ARCO + 20), ang(f0), ang(f1),
                  fill=mezcla(col, (255, 255, 255), .55) + (255,), width=max(1, int(4 * K)))

    # ---- marcas y números (0-450 °C)
    fn = fuente(52)
    for v in range(0, 451, 25):
        mayor = v % 50 == 0
        if simple and v % 150: continue
        a = ang(v / 450.0)
        r1 = (280 if simple else 306)
        r2 = r1 - (96 if simple else (50 if mayor else 26))
        d.line(q(*pol(r1, a), *pol(r2, a)), fill=(240, 244, 250, 255),
               width=max(1, int((34 if simple else (14 if mayor else 7)) * K)))
        if not simple and tam >= 128 and v % 100 == 0 and fn:
            d.text(q(*pol(206, a)) , str(v), font=fn, fill=(222, 228, 238, 255), anchor="mm")
    if not simple and tam >= 128:
        f2 = fuente(36)
        if f2:
            d.text(q(c, c - 100), "FRENOS", font=f2, fill=(140, 152, 170, 255), anchor="mm")
            d.text(q(c, c + 118), "°C", font=fuente(54), fill=(255, 176, 32, 255), anchor="mm")
    if not simple:                              # disco de freno (con agujeros) en el hueco inferior
        cy = c + 262
        d.ellipse(q(c - 66, cy - 66, c + 66, cy + 66), fill=(150, 158, 172, 255), outline=(60, 66, 78, 255), width=max(1, int(5 * K)))
        d.ellipse(q(c - 44, cy - 44, c + 44, cy + 44), fill=(58, 64, 76, 255))
        d.ellipse(q(c - 20, cy - 20, c + 20, cy + 20), fill=(190, 198, 212, 255))
        for k in range(6):
            x, y = pol(32, k * 60 + 30)
            d.ellipse(q(x - 6, y - 6 + (cy - c), x + 6, y + 6 + (cy - c)), fill=(10, 12, 16, 255))

    # ---- aguja (dos tonos para dar volumen) + sombra
    a = ang(valor)
    def P(r, off=0):
        t = math.radians(a)
        return (c + r * math.cos(t) - off * math.sin(t), c + r * math.sin(t) + off * math.cos(t))
    L = 300 if simple else 336
    W = 36 if simple else 22
    luz = [P(L), P(0, -W), P(-96, -W * .55), P(-96, 0), P(0, 0)]
    osc = [P(L), P(0, W), P(-96, W * .55), P(-96, 0), P(0, 0)]
    sombra = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).polygon([((x + 14) * K, (y + 20) * K) for x, y in luz + osc], fill=(0, 0, 0, 190))
    img = Image.alpha_composite(img, sombra.filter(ImageFilter.GaussianBlur(11 * K)))
    d = ImageDraw.Draw(img)
    d.polygon([(x * K, y * K) for x, y in luz], fill=(255, 128, 96, 255))
    d.polygon([(x * K, y * K) for x, y in osc], fill=(204, 38, 24, 255))

    # ---- eje cromado
    disco(72, (22, 26, 34, 255))
    for i in range(24):
        t = i / 23
        disco(60 * (1 - t * .85), mezcla((112, 120, 136), (238, 242, 250), t) + (255,), cx=c - 8 * t, cy=c - 10 * t)
    if not simple:
        disco(12, (40, 46, 58, 255))

    # ---- reflejo del cristal recortado a la esfera
    cristal = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cristal)
    for i in range(22):
        t = i / 21
        cd.ellipse(q(c - 350 + 60 * t, c - 440 + 40 * t, c + 350 - 60 * t, c - 40 - 150 * t), fill=(255, 255, 255, int(5 + 3 * t)))
    cristal.putalpha(ImageChops.multiply(cristal.getchannel("A"), mask_cara))
    img = Image.alpha_composite(img, cristal)
    return img.resize((tam, tam), Image.LANCZOS)

# Si junto al programa esta icono_frenos.ico, ese es el icono (ventana, barra de tareas y bandeja).
# Si no esta, se dibuja el manometro por codigo, como antes.
ICONO_FRENOS = os.path.join(script_dir, "icono_frenos.ico")

def _imagen_bandeja():
    try:
        if os.path.exists(ICONO_FRENOS):
            from PIL import Image
            im = Image.open(ICONO_FRENOS)
            im.size = (64, 64)                  # el .ico trae varios tamanos; se elige el de 64
            im.load()
            return im.convert("RGBA")
    except Exception as e:
        _log("icono: no se pudo leer icono_frenos.ico: %r" % (e,))
    return dibujar_icono(64)

def _identidad_propia():
    """Le da al programa su propia identidad en Windows, para que la barra de tareas no lo agrupe con Python."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Termofreno.ATS")
    except Exception:
        pass

def _poner_icono_ventana(titulo="Termofreno"):
    """Pone el manómetro como icono de la ventana y de la barra de tareas (solo Windows; si falla, se ignora)."""
    try:
        import ctypes, tempfile, time
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        user32.FindWindowW.restype = wintypes.HWND
        user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.SendMessageW.restype = ctypes.c_ssize_t
        if os.path.exists(ICONO_FRENOS):
            ruta = ICONO_FRENOS
        else:
            tams = [256, 128, 64, 48, 32, 24, 16]
            imgs = [dibujar_icono(t) for t in tams]
            ruta = os.path.join(tempfile.gettempdir(), "frenos_termicos.ico")
            imgs[0].save(ruta, sizes=[(t, t) for t in tams], append_images=imgs[1:])
        grande = user32.LoadImageW(None, ruta, 1, 32, 32, 0x10)
        chico = user32.LoadImageW(None, ruta, 1, 16, 16, 0x10)
        hwnd = None
        for _ in range(40):                      # la ventana tarda un poco en existir: reintenta ~10 s
            hwnd = user32.FindWindowW(None, titulo)
            if hwnd:
                break
            time.sleep(0.25)
        if not hwnd or not grande:
            _log("icono: no se encontro la ventana '%s' o no se pudo cargar el icono" % titulo)
            return
        for _ in range(3):                       # se aplica varias veces por si el navegador embebido lo pisa
            user32.SendMessageW(hwnd, 0x80, 0, chico)    # WM_SETICON, ICON_SMALL
            user32.SendMessageW(hwnd, 0x80, 1, grande)   # WM_SETICON, ICON_BIG
            try:
                user32.SetClassLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
                user32.SetClassLongPtrW(hwnd, -34, chico)   # GCLP_HICONSM
                user32.SetClassLongPtrW(hwnd, -14, grande)  # GCLP_HICON
            except Exception:
                pass
            time.sleep(1.0)
    except Exception as e:
        _log("icono: fallo al poner el icono de '%s': %r" % (titulo, e))

def iniciar_ventana_html():
    """Abre la ventana HTML. Devuelve False si no se pudo, para usar las ventanas de Tkinter."""
    try:
        import webview
    except Exception:
        return False
    if not os.path.exists(VENTANA_HTML):
        return False
    try:
        ventana = webview.create_window("Termofreno", VENTANA_HTML, js_api=ApiVentana(), width=1040, height=700,
                                        min_size=(920, 620), background_color="#131a23")
        _VENT["main"] = ventana
        bandeja = {"icono": None}

        def quitar_icono():
            ic, bandeja["icono"] = bandeja["icono"], None
            if ic is not None:
                try:
                    ic.stop()
                except Exception:
                    pass

        def restaurar(icon=None, item=None):
            quitar_icono()
            try:
                ventana.show()
                ventana.restore()
            except Exception:
                pass

        def salir(icon=None, item=None):
            liberar_todas_las_teclas()
            quitar_icono()
            try:
                ventana.destroy()
            except Exception:
                os._exit(0)

        def al_minimizar():
            """Al minimizar, la ventana se esconde en los iconos ocultos de la barra de tareas."""
            if not PYSTRAY_DISPONIBLE or bandeja["icono"] is not None:
                return
            try:
                menu = pystray.Menu(pystray.MenuItem("Abrir Termofreno", restaurar, default=True),
                                    pystray.MenuItem("Salir", salir))
                icono = pystray.Icon("Termofreno", _imagen_bandeja(), "Termofreno", menu)
                bandeja["icono"] = icono
                threading.Thread(target=icono.run, daemon=True).start()
                ventana.hide()
            except Exception:
                quitar_icono()

        try:
            ventana.events.minimized += al_minimizar
        except Exception:
            pass
        try:
            ventana.events.shown += lambda: threading.Thread(target=_poner_icono_ventana, daemon=True).start()
        except Exception:
            pass
        webview.start()
        quitar_icono()
        return True
    except Exception:
        return False

if __name__ == "__main__":
    _identidad_propia()
    try:
        _fijar_alertas(cargar_config_disco().get("alertas_sonoras", True))
        _fijar_volumen(cargar_config_disco().get("volumen_alertas", 80))
    except Exception:
        pass
    threading.Thread(target=_bucle_alertas, daemon=True).start()
    ocultar_consola_propia()
    if not iniciar_ventana_html():
        mostrar_configuracion()
        AppVentanaPrincipal()