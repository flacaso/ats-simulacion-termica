# 🚛🔥 ATS / ETS2 Thermal Brakes Portable

Herramienta de simulación térmica en tiempo real para **American Truck Simulator (ATS)** y **Euro Truck Simulator 2 (ETS2)**. Diseñada para añadir un nivel de realismo extremo a tus rutas: los frenos se calientan según el peso de la carga, la velocidad y el uso, perdiendo eficacia (*Fading*) e incluso llegando a la cristalización a los **450°C**.

---

## ✨ Características Principales
* **100% Portable:** Compilado en un único archivo ejecutable (`.exe`), sin necesidad de instalar Python.
* **Física Dinámica:** Cálculo de temperatura basado en fricción real, peso del remolque y velocidad.
* **Puente vJoy:** Modifica directamente la respuesta del freno en el juego para que experimentes la pérdida de frenada.
* **Soporte de Dispositivos:** Compatible con mandos (Gamepads) y volantes con pedales independientes.
* **Dashboard Móvil y OBS:** Incluye un servidor web local integrado para ver la telemetría en tu celular o en overlays para OBS Studio
* **Multilenguaje:** Configurable en Español e Inglés.
* **Integración con Windows:** Minimizado inteligente a la bandeja del sistema (*System Tray*) con notificaciones flotantes.

---

## 🛠️ Requisitos Indispensables

Para que el programa funcione correctamente, necesitas tener instalados dos componentes externos gratuitos:

1. **vJoy (Controlador de Joystick Virtual):**
   * Descarga e instala la versión oficial desde [SourceForge](https://sourceforge.net/projects/vjoystick/) o [GitHub](https://github.com/shauleiz/vJoy). Asegúrate de habilitar al menos el *Device ID 1*.
2. **Servidor de Telemetría de Funbit (ETS2/ATS Telemetry Server):**
   * Es la base para extraer los datos del juego. Descárgalo desde su repositorio oficial en [GitHub de Funbit](https://github.com/funbit/ets2-telemetry-server).

---

## 🚀 Guía de Instalación y Uso

1. Descarga el archivo ejecutable (`.exe`) más reciente desde la sección de **Releases** de este repositorio.
2. Asegúrate de tener corriendo el servidor de telemetría de Funbit y vjoy.
3. Ejecuta la aplicación. Se abrirá una ventana de configuración inicial donde podrás:
   * Seleccionar tu idioma (Español / Inglés).
   * Elegir tu dispositivo de entrada (Mando o Volante) y comprobar los ejes en tiempo real.
   * Ajustar la sensibilidad de calentamiento y enfriamiento.
4. Entra a tu juego (`ATS` / `ETS2`), ve a **Opciones > Controles**, selecciona `Teclado + vJoy Device` como entrada principal y mapea tus ejes.
5. ¡Listo! Puedes minimizar el programa a la bandeja de sistema y usar los enlaces web que te proporciona para tu celular u OBS.

---

⭐ **Créditos y Agradecimientos:**
Este proyecto utiliza como base fundamental el servidor de telemetría de código abierto de **Funbit**. ¡Un reconocimiento especial a su gran trabajo para la comunidad de simulación! también utiliza la app de vJoy para poder simular la perdida de frenos sin sus proyectos esto no seria posible
