# Miku Cosmic Theme for YASB

> Tema comunitario de YASB inspirado en Hatsune Miku, con launcher, controles multimedia, clima, menú de energía y una IA local opcional mediante Ollama.

[Español](#español) · [English](#english)

## Español

### Requisitos

- Windows 10 u 11.
- [YASB](https://github.com/amnweb/yasb) estable y actualizado.
- Python 3.10 o posterior instalado con los comandos `py` y `pyw`.
- Una Nerd Font, preferentemente JetBrainsMono Nerd Font.
- Una cuenta gratuita de [WeatherAPI](https://www.weatherapi.com/).

### Instalación

1. Descarga o clona el repositorio. Cambia el nombre de la carpeta descargada a `yasb` y colócala en:

   ~~~text
   %USERPROFILE%\.config\yasb
   ~~~

   Comprueba la carpeta que YASB está usando con:

   ~~~powershell
   yasbc --config
   ~~~

2. Abre PowerShell dentro de `%USERPROFILE%\.config\yasb` e instala los requisitos en el Python global que utilizarán los widgets:

   ~~~powershell
   py -3 -m pip install --upgrade -r requirements.txt
   ~~~

   No uses un entorno virtual para este flujo. Tanto la instalación como los comandos de YASB usan `py -3`, por lo que apuntan al mismo intérprete.

3. Copia tu fotografía a:

   ~~~text
   assets\Avatar.png
   ~~~

   El nombre debe ser exactamente `Avatar.png`. Al abrir el menú de energía, `scripts\mikugen.py` combina automáticamente tu foto con `Miku_Headsets.png` y genera:

   ~~~text
   assets\Miku_Avatar.png
   ~~~

   También puedes generarla manualmente:

   ~~~powershell
   py -3 .\scripts\mikugen.py
   ~~~

4. Crea la configuración privada del clima:

   ~~~powershell
   Copy-Item .env.example .env
   notepad .env
   ~~~

   Reemplaza los valores de `.env` con tu clave y ubicación:

   ~~~dotenv
   YASB_WEATHER_API_KEY=TU_CLAVE_DE_WEATHERAPI
   YASB_WEATHER_LOCATION=TU_CIUDAD
   ~~~

   El archivo `.env` está ignorado por Git. No publiques ni compartas tu clave.

5. Verifica los componentes personalizados:

   ~~~powershell
   py -3 .\scripts\miku_media.py
   py -3 .\scripts\launcher.py --bar-icon
   ~~~

   El primer comando debe mostrar `Miku System Ready` si no hay contenido reproduciéndose. El segundo debe devolver una etiqueta `<img>` con una ruta absoluta a `Miku_Tie.png`.

6. Reinicia YASB y habilita el inicio automático si todavía no lo hiciste:

   ~~~powershell
   yasbc stop
   yasbc start
   yasbc enable-autostart
   ~~~

### Qué se inicia con YASB

- El botón Miku Tie calcula una ruta absoluta para que el icono funcione sin depender del directorio de inicio.
- `miku_media.py` consulta la sesión multimedia de Windows cada segundo y muestra los datos o `Miku System Ready`.
- El menú de energía ejecuta `mikugen.py` y actualiza `Miku_Avatar.png` cuando cambia `Avatar.png`.
- El widget nativo y el popup de clima comparten `YASB_WEATHER_API_KEY` y `YASB_WEATHER_LOCATION`.

### Brillo y monitores

El botón de brillo permanece visible aunque YASB no detecte control compatible. Algunos monitores externos no permiten cambiar el brillo desde Windows o requieren activar DDC/CI en el menú físico del monitor. Para revisar la detección:

~~~powershell
yasbc monitor-information
~~~

Si el botón aparece pero no cambia el brillo, actualiza YASB y comprueba DDC/CI; no es un fallo de `requirements.txt`.

### Diagnóstico

~~~powershell
where.exe py
where.exe pyw
py -3 -c "import PIL, PyQt6, psutil, requests, winsdk; print('Dependencias OK')"
yasbc log
~~~

Si modificas `.env`, detén y vuelve a iniciar YASB para que el proceso reciba los valores nuevos.

### Personalización opcional

El menú de energía admite estas variables de entorno del usuario:

~~~powershell
[Environment]::SetEnvironmentVariable('MIKU_DISPLAY_NAME', 'TU_NOMBRE', 'User')
[Environment]::SetEnvironmentVariable('MIKU_EMAIL', 'TU_CORREO', 'User')
[Environment]::SetEnvironmentVariable('MIKU_USER_ROLE', 'TU_ROL', 'User')
[Environment]::SetEnvironmentVariable('MIKU_LOCATION', 'TU_UBICACION', 'User')
[Environment]::SetEnvironmentVariable('MIKU_CLOCK_LABEL', 'LOCAL', 'User')
~~~

La ventana de IA requiere [Ollama](https://ollama.com/) ejecutándose localmente. El resto del tema funciona sin Ollama.

## English

### Requirements

- Windows 10 or 11.
- An up-to-date stable installation of [YASB](https://github.com/amnweb/yasb).
- Python 3.10 or newer with both `py` and `pyw` available.
- A Nerd Font, preferably JetBrainsMono Nerd Font.
- A free [WeatherAPI](https://www.weatherapi.com/) account.

### Installation

1. Download or clone the repository. Rename the downloaded folder to `yasb` and place it at:

   ~~~text
   %USERPROFILE%\.config\yasb
   ~~~

   Confirm the directory used by YASB with `yasbc --config`.

2. Open PowerShell in that directory and install the requirements into the global Python used by the widgets:

   ~~~powershell
   py -3 -m pip install --upgrade -r requirements.txt
   ~~~

   Do not use a virtual environment for this installation flow. Both installation and YASB callbacks use `py -3`.

3. Save your picture as `assets\Avatar.png`. Opening the power menu runs `scripts\mikugen.py` and creates `assets\Miku_Avatar.png` automatically.

4. Copy `.env.example` to `.env` and set your WeatherAPI key and location:

   ~~~dotenv
   YASB_WEATHER_API_KEY=YOUR_WEATHERAPI_KEY
   YASB_WEATHER_LOCATION=YOUR_CITY
   ~~~

5. Validate and restart:

   ~~~powershell
   py -3 .\scripts\miku_media.py
   py -3 .\scripts\launcher.py --bar-icon
   yasbc stop
   yasbc start
   ~~~

The Miku Tie icon uses an absolute URI generated at startup. The media script always returns a visible status, and the weather widget and popup share the same private environment values.

The brightness button remains visible on unsupported displays, but software control still requires compatible Windows brightness or DDC/CI support. Use `yasbc monitor-information` for diagnostics.

## Project notes

Local logs, caches, notification counters, `.env`, `Avatar.png`, and `Miku_Avatar.png` are ignored so they cannot be committed accidentally.

Hatsune Miku and third-party artwork remain the property of their respective owners. Before redistributing an included image, verify that its original license or permission permits redistribution.

## License

Original code and configuration are available under the [MIT License](LICENSE), copyright © 2026 Jesus Blanco (ITzDier).

Third-party images and other resources are not automatically covered by the MIT License. See [ASSET_NOTICE.md](ASSET_NOTICE.md).

## Independent project disclaimer

This is an unofficial community theme for YASB. It is not affiliated with, maintained by, sponsored by, or endorsed by the YASB authors. YASB is a separate third-party project distributed under its own license and documentation. Installation, updates, compatibility, and use of YASB itself are outside the scope of this repository.

This theme is provided as-is, without warranty, under the terms of the MIT License.
