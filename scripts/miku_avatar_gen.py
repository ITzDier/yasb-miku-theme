from PIL import Image, ImageDraw, ImageOps
import os
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

def obtener_imagen_de_perfil():
    configured_path = os.getenv("MIKU_PROFILE_IMAGE", "").strip()
    if configured_path:
        profile_path = Path(os.path.expandvars(configured_path)).expanduser()
        if profile_path.is_file():
            return profile_path

    for filename in ("profile.png", "profile.jpg", "profile.jpeg", "profile.webp"):
        profile_path = ASSETS_DIR / filename
        if profile_path.is_file():
            return profile_path

    raise FileNotFoundError(
        "Agrega assets/profile.jpg o configura la variable MIKU_PROFILE_IMAGE."
    )

def generar_avatar():
    try:
        # 1. Cargar imágenes
        base = Image.open(obtener_imagen_de_perfil()).convert("RGBA")
        headsets = Image.open(ASSETS_DIR / "Miku_Headsets.png").convert("RGBA")

        # 2. Preparar el círculo (Perfil)
        # Recortamos la cara en un círculo de 300x300
        base = base.resize((300, 300))
        mask = Image.new("L", (300, 300), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 300, 300), fill=255)
        
        perfil_circular = ImageOps.fit(base, (300, 300), centering=(0.5, 0.5))
        perfil_circular.putalpha(mask)

        # 3. Preparar la foto de perfil (Aumentamos el tamaño a 400x400 dentro del lienzo de 500x500)
        base = base.resize((400, 400)) 
        mask = Image.new("L", (400, 400), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 400, 400), fill=255)
        
        perfil_circular = ImageOps.fit(base, (400, 400), centering=(0.5, 0.5))
        perfil_circular.putalpha(mask)

        # Centrar el perfil en el lienzo de 500x500
        # (500-400)/2 = 50 px de margen
        final = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
        final.paste(perfil_circular, (50, 50), perfil_circular)

        # 4. Ajustar audífonos (Aumentamos a 500x500 para que cubran bien el perfil)
        headsets = headsets.resize((500, 500))
        
        # Pegamos centrados (coordenadas 0,0 porque el lienzo ya es de 500x500)
        final.paste(headsets, (0, 0), headsets)
        
        # Guardar (yasb escalará esto automáticamente, pero ahora mantendrá la forma)
        final.save(ASSETS_DIR / "miku_avatar.png", "PNG")
        return True
    except Exception as e:
        print(f"Error componiendo avatar: {e}")
        return False
