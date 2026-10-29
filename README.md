# 🚛🔥 ATS / ETS2 Thermal Brakes Portable

Herramienta de simulación térmica en tiempo real para **American Truck Simulator (ATS)** y **Euro Truck Simulator 2 (ETS2)**. Diseñada para añadir un nivel de realismo extremo a tus rutas: los frenos se calientan según el peso de la carga, la velocidad y el uso, perdiendo eficacia (*Fading*) e incluso llegando a la cristalización a los **450°C**.

---

## ✨ Características Principales

- **Portable:** carpeta lista para usar (`Termofreno.exe`), sin necesidad de instalar Python.
- **Física Dinámica:** Cálculo de temperatura basado en fricción real, peso del remolque y velocidad.
- **Puente vJoy:** Modifica directamente la respuesta del freno en el juego para que experimentes la pérdida de frenada.
- **Soporte de Dispositivos:** Compatible con mandos (Gamepads) y volantes con pedales independientes.
- **Dashboard Móvil y OBS:** Incluye un servidor web local integrado para ver la telemetría en tu celular o en overlays para OBS Studio.
- **Panel de botones:** panel web para controlar funciones del camión desde el celular o la tablet.
- **Multilenguaje:** Configurable en Español e Inglés.
- **Integración con Windows:** Minimizado inteligente a la bandeja del sistema (*System Tray*) con notificaciones flotantes.

---

## 🆕 Novedades de esta versión

Respecto a la versión anterior (`simulacion termica.py`), esta versión cambia bastante:

- **Ventana principal nueva**, con pestañas: Inicio, Dispositivo, Frenos, Calibración, Diagnóstico y Acerca de.
- **Mini ventana** que se queda encima del juego, con opacidad ajustable (100 / 80 / 60 %).
- **Alertas sonoras** con volumen ajustable.
- **Frenado calibrado por peso:** la fuerza de frenado se calcula con la masa total (tractor + remolque + carga) y apunta a los límites legales de frenado de EE. UU. (60 mph en 250 ft para combinaciones de hasta ~36 t), de modo que un camión pesado tarda en frenar lo que tardaría uno real.
- **Fading más realista:** curva de pérdida de eficacia según la temperatura (empieza hacia los 260 °C y a los 450 °C los frenos ya no frenan), con compensación del fading propio del juego.
- **Aprendizaje por combinación:** mientras frenas, el programa aprende la fuerza de frenado de cada camión + remolque + carga y la guarda para la próxima vez.
- **Memoria térmica:** si cargas una partida anterior, vuelves a la temperatura que tenías en ese punto; si el tiempo del juego salta hacia adelante (grúa, dormir), los frenos se enfrían según los minutos transcurridos.
- **Inclinación del terreno** visible en la pestaña de Calibración.
- **Modo calibración:** prueba de frenado de 100 a 0 km/h y registro continuo en archivos CSV (carpeta `pruebas_frenado`), útil para ajustar camiones o mods.
- **Panel web mejorado:** puerto configurable, código QR para abrirlo desde el celular, enlaces para OBS (fuente de navegador), panel de botones y panel minimalista.
- **Panel de botones:** envía teclas al juego desde el celular o la tablet (solo una lista fija de teclas; si una tecla se queda mantenida más de 20 s, el programa la suelta sola).
- **Cuidado con vJoy:** deja los controles en reposo al abrir y cerrar, los reinicia cuando el juego conecta y tiene un botón "Reiniciar controles".
- **Diagnóstico:** una pestaña que revisa si están conectados el juego (telemetría), vJoy, el servidor web, tu volante o mando y la memoria térmica.

> La versión anterior sigue disponible en [Releases](../../releases) (`v0.1-anterior`).

---

## 🛠️ Requisitos Indispensables
## 🔧 Mod recomendado: Flacooo Physics & FFB Pack

Todas las calibraciones del frenado se hicieron en ATS (1.61+) con el mod **[Flacooo Physics & FFB Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=3821886843)** del Steam Workshop, que ajusta la física del juego, incluido el torque de los frenos (`brake_torque_factor: 0.35`). Para obtener el realismo para el que está calibrado Termofreno, puedes suscríbete al mod antes de usar el programa.

Sin el mod, el programa funciona igual y aprende la fuerza de frenado de cada camión mientras frenas, pero los resultados no están validados y el frenado puede sentirse distinto.

Para que el programa funcione correctamente, necesitas tener instalados dos componentes externos gratuitos:

1. **vJoy (Controlador de Joystick Virtual):**
   - Descarga e instala la versión oficial desde [SourceForge](https://sourceforge.net/projects/vjoystick/) o [GitHub](https://github.com/shauleiz/vJoy). Asegúrate de habilitar al menos el *Device ID 1*.
2. **Servidor de Telemetría de Funbit (ETS2/ATS Telemetry Server):**
   - Es la base para extraer los datos del juego. Descárgalo desde su repositorio oficial en [GitHub de Funbit](https://github.com/funbit/ets2-telemetry-server).

---

## 🚀 Guía de Instalación y Uso

1. Descarga el archivo `.zip` más reciente desde la sección de **[Releases](../../releases)** de este repositorio.
2. **Extrae todo el contenido** en una carpeta donde tu usuario pueda escribir (por ejemplo `Documentos\Termofreno`). No lo ejecutes desde dentro del zip ni lo pongas en `Program Files`: el programa guarda su configuración, registros y pruebas junto al `.exe`.
3. Mantén todos los archivos juntos (el `.exe`, la carpeta `_internal` y los `.html`).
4. Asegúrate de tener corriendo el servidor de telemetría de Funbit y vJoy.
5. Ejecuta `Termofreno.exe`. Se abrirá una ventana de configuración inicial donde podrás:
   - Seleccionar tu idioma (Español / Inglés).
   - Elegir tu dispositivo de entrada (Mando o Volante) y comprobar los ejes en tiempo real.
   - Ajustar la sensibilidad de calentamiento y enfriamiento.
6. Entra a tu juego (`ATS` / `ETS2`), ve a **Opciones > Controles**, selecciona `Teclado + vJoy Device` como entrada principal y mapea tus ejes.
7. ¡Listo! Puedes minimizar el programa a la bandeja de sistema y usar los enlaces web que te proporciona para tu celular u OBS.

---

## 🔍 Transparencia y avisos de antivirus

El `.exe` está hecho con Python y **PyInstaller**, y **no está firmado digitalmente**. Por eso Windows SmartScreen puede mostrar un aviso ("Más información → Ejecutar de todos modos") y algunos antivirus pueden marcarlo por error (falso positivo, algo común en programas de Python empaquetados). Todo el código fuente está en este repositorio para que lo puedas revisar.

Qué hace el programa:

- Lee la telemetría del juego desde el servidor de Funbit en `http://localhost:25555`.
- Envía valores de ejes a un joystick virtual (vJoy).
- Abre un **servidor web local** para mostrar los paneles en tu celular, tablet u OBS. Escucha en tu red local, así que otros dispositivos de tu misma red pueden abrir esas páginas. Si no lo quieres, bloquea el puerto en el firewall de Windows.
- Desde el panel de botones envía al juego una **lista fija de teclas** (simulación de teclado). Cualquier otra tecla se rechaza.
- Guarda su configuración, registros y pruebas de frenado en archivos junto al `.exe`.

Qué **no** hace: no contacta ningún servidor en internet, no se agrega al inicio de Windows ni al registro, no modifica archivos del sistema y no descarga ni ejecuta otro código.

Para verificar tu descarga, compara el hash **SHA-256** con el que aparece en la descripción de cada release:

```
certutil -hashfile Termofreno.exe SHA256
```

---

## 🧪 Estado de la calibración

El modelo de frenado está calibrado y validado (±5 % en tiempo y distancia) con el **Kenworth W900**: tractor solo, remolque vacío y cargas de 20, 27, 35 y 56 t, en frío y en caliente.

Pendiente (no calibrado): freno de motor, retarder, freno de remolque (botón) y otros camiones.

---

## 🧱 Compilar desde el código fuente

Requisitos: Python para Windows (la misma versión con la que pruebes el programa) y los paquetes de `requirements.txt`.

Para ejecutarlo sin compilar:

```
pip install -r requirements.txt
python termofreno.pyw
```

Para generar la carpeta portable, ejecuta `build_termofreno.bat` junto a `termofreno.pyw`. Crea un entorno limpio, compila con PyInstaller y deja el resultado en `dist\Termofreno\` junto con un `.zip` y sus hashes SHA-256.

---

⭐ **Créditos y Agradecimientos:** Este proyecto utiliza como base fundamental el servidor de telemetría de código abierto de **Funbit**. ¡Un reconocimiento especial a su gran trabajo para la comunidad de simulación! También utiliza la app de vJoy para poder simular la pérdida de frenos; sin sus proyectos esto no sería posible.
