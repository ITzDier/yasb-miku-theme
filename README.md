# Miku Cosmic Theme for YASB

> A Hatsune Miku-inspired YASB setup for Windows, with a launcher, media controls, weather, power menu, and optional local AI through Ollama.

[Español](#español) · [English](#english)

## Español

### Inicio rápido

Necesitas Windows, [YASB](https://github.com/amnweb/yasb) y Python 3.10 o posterior. Instala primero YASB siguiendo sus [instrucciones oficiales](https://github.com/amnweb/yasb/wiki/Installation); este repositorio contiene solamente el tema y sus scripts adicionales.

1. Descarga o clona este tema. La carpeta descargada puede llamarse `yasb-miku-theme` o `yasb-miku-theme-main`.

2. Cambia el nombre de esa carpeta a `yasb` y colócala en:

   ```text
   %USERPROFILE%\.config\
   ```

   El resultado final debe ser `%USERPROFILE%\.config\yasb`. El nombre `yasb` es importante para que YASB encuentre `config.yaml`, `styles.css`, los scripts y los recursos del tema.

3. Abre PowerShell dentro de `%USERPROFILE%\.config\yasb` e instala las dependencias:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Abre `config.yaml` y sustituye:

   - `YOUR_WEATHERAPI_KEY` por tu clave de [WeatherAPI](https://www.weatherapi.com/).
   - `YOUR_CITY` por tu ciudad.

5. Reinicia YASB. El tema básico ya debería funcionar.

6. Para crear tu avatar, guarda tu propia imagen como `assets/profile.jpg`. También puedes configurar `MIKU_PROFILE_IMAGE` con la ruta de otra imagen. Al abrir el menú de energía se generará `assets/miku_avatar.png` automáticamente.

### Personalización opcional

La ventana de clima y el menú de energía leen estos valores desde variables de entorno. Solo configura los que quieras usar:

```powershell
[Environment]::SetEnvironmentVariable('WEATHERAPI_KEY', 'TU_CLAVE', 'User')
[Environment]::SetEnvironmentVariable('WEATHER_LOCATION', 'TU_CIUDAD', 'User')
[Environment]::SetEnvironmentVariable('MIKU_DISPLAY_NAME', 'TU_NOMBRE', 'User')
[Environment]::SetEnvironmentVariable('MIKU_EMAIL', 'TU_CORREO', 'User')
[Environment]::SetEnvironmentVariable('MIKU_USER_ROLE', 'TU_ROL', 'User')
[Environment]::SetEnvironmentVariable('MIKU_LOCATION', 'TU_UBICACION', 'User')
[Environment]::SetEnvironmentVariable('MIKU_CLOCK_LABEL', 'LOCAL', 'User')
[Environment]::SetEnvironmentVariable('MIKU_PROFILE_IMAGE', 'C:\ruta\a\tu\imagen.jpg', 'User')
```

Después, cierra y vuelve a abrir YASB. Si no defines nombre, se usa automáticamente el usuario actual de Windows; si no defines correo, no se muestra ninguno.

La sección de IA requiere [Ollama](https://ollama.com/) ejecutándose localmente. El resto del tema puede utilizarse sin Ollama.

### Solución rápida de problemas

- Si un script no abre, ejecuta otra vez `py -m pip install -r requirements.txt`.
- Si el clima no aparece, revisa la clave y la ciudad tanto en `config.yaml` como en las variables de entorno.
- Si faltan iconos, instala una Nerd Font y configúrala en YASB.
- Las rutas se calculan desde el proyecto o desde `%USERPROFILE%`; no necesitas escribir tu nombre de usuario dentro de los scripts.
- Tu imagen de perfil y el avatar generado están excluidos por `.gitignore` para evitar publicarlos accidentalmente.

## English

### Quick start

You need Windows, [YASB](https://github.com/amnweb/yasb), and Python 3.10 or newer. Install YASB first by following its [official instructions](https://github.com/amnweb/yasb/wiki/Installation); this repository only provides the theme and its additional scripts.

1. Download or clone this theme. The downloaded folder may be named `yasb-miku-theme` or `yasb-miku-theme-main`.

2. Rename that folder to `yasb` and place it inside:

   ```text
   %USERPROFILE%\.config\
   ```

   The final path must be `%USERPROFILE%\.config\yasb`. The `yasb` folder name is important so YASB can find `config.yaml`, `styles.css`, the scripts, and the theme assets.

3. Open PowerShell inside `%USERPROFILE%\.config\yasb` and install the dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Open `config.yaml` and replace:

   - `YOUR_WEATHERAPI_KEY` with your own [WeatherAPI](https://www.weatherapi.com/) key.
   - `YOUR_CITY` with your city.

5. Restart YASB. The basic theme should now work.

6. To create your avatar, save your own image as `assets/profile.jpg`. You may instead set `MIKU_PROFILE_IMAGE` to another image path. Opening the power menu automatically generates `assets/miku_avatar.png`.

### Optional customization

The custom weather window and power menu read the following environment variables. Configure only the ones you want:

```powershell
[Environment]::SetEnvironmentVariable('WEATHERAPI_KEY', 'YOUR_KEY', 'User')
[Environment]::SetEnvironmentVariable('WEATHER_LOCATION', 'YOUR_CITY', 'User')
[Environment]::SetEnvironmentVariable('MIKU_DISPLAY_NAME', 'YOUR_NAME', 'User')
[Environment]::SetEnvironmentVariable('MIKU_EMAIL', 'YOUR_EMAIL', 'User')
[Environment]::SetEnvironmentVariable('MIKU_USER_ROLE', 'YOUR_ROLE', 'User')
[Environment]::SetEnvironmentVariable('MIKU_LOCATION', 'YOUR_LOCATION', 'User')
[Environment]::SetEnvironmentVariable('MIKU_CLOCK_LABEL', 'LOCAL', 'User')
[Environment]::SetEnvironmentVariable('MIKU_PROFILE_IMAGE', 'C:\path\to\your\image.jpg', 'User')
```

Close and reopen YASB afterward. If no display name is configured, the current Windows username is used automatically; if no email is configured, no email is shown.

The AI section requires [Ollama](https://ollama.com/) running locally. The rest of the theme works without Ollama.

### Quick troubleshooting

- If a script does not open, run `py -m pip install -r requirements.txt` again.
- If weather is missing, check the key and city in both `config.yaml` and the environment variables.
- If icons are missing, install a Nerd Font and select it in YASB.
- Paths are resolved from the project or `%USERPROFILE%`; you do not need to place your username inside any script.
- Your profile image and generated avatar are excluded through `.gitignore` to prevent accidental publication.

## Project notes

Local logs, caches, notification counters, and launcher history are excluded through `.gitignore` so they are not accidentally published.

Hatsune Miku and third-party artwork remain the property of their respective owners. Before redistributing any included image, verify that its original license or permission allows it.

## License

Original code and configuration are available under the [MIT License](LICENSE), copyright © 2026 Jesus Blanco (ITzDier).

Third-party images and other resources are not automatically covered by the MIT License. See [ASSET_NOTICE.md](ASSET_NOTICE.md) before redistributing files from `assets`.

## Independent project disclaimer

This is an unofficial community theme for YASB. It is not affiliated with, maintained by, sponsored by, or endorsed by the YASB authors. YASB is a separate third-party project distributed under its own license and documentation. Installation, updates, compatibility, and use of YASB itself are outside the scope of this repository.

This theme is provided as-is, without warranty, under the terms of the MIT License. References and links to YASB are included only to explain compatibility and installation.

---

Este es un tema comunitario no oficial para YASB. No está afiliado, mantenido, patrocinado ni respaldado por los autores de YASB. YASB es un proyecto independiente de terceros, distribuido bajo su propia licencia y documentación. La instalación, las actualizaciones, la compatibilidad y el uso de YASB quedan fuera del alcance de este repositorio.

Este tema se proporciona tal cual, sin garantías, conforme a la licencia MIT. Las referencias y enlaces a YASB se incluyen únicamente para explicar la compatibilidad y la instalación.
