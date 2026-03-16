import sys
import os
import io
import platform
from PIL import Image, ImageDraw, ImageFont

SEGMENT_TEMPLATE = {
    'Operacoes': 'template_seg1.png',
    'Servicos': 'template_seg2.png',
    'offshore': 'template_seg3.png',
    'estaleiro': 'template_seg4.png',
}

POSITIONS = {
    'name':      {'x': 87,   'y': 444, 'cover': (79,  430, 1000, 502)},
    'sector':    {'x': 89,   'y': 538, 'cover': (81,  525, 1000, 602)},
    'email':     {'x': 90,   'y': 658, 'cover': (82,  645, 1060, 800)},
    'phone':     {'x': 91,   'y': 743},
    # moved closer to the social handles on the template
    'instagram': {'x': 1450, 'y': 672},
    'linkedin':  {'x': 1450, 'y': 725},
}

COLORS = {
    'name': (0,   123, 77),
    'body': (109, 109, 109),
}

FONT_SIZE_NAME = 48
FONT_SIZE_BODY = 50


def get_font_path():
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'public', 'assets', 'LiberationSans-Regular.ttf')
    if os.path.exists(bundled):
        return bundled

    system = platform.system()
    if system == 'Windows':
        candidates = [
            r'C:\Windows\Fonts\l_10646.ttf',
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\calibri.ttf',
        ]
    elif system == 'Darwin':
        candidates = [
            '/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ]

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def validate_input(value, max_length=50):
    return isinstance(value, str) and len(value) > 0 and len(value) <= max_length


def image_to_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()


def main():
    if len(sys.argv) < 6:
        sys.stderr.write("Uso: signaturegenerator.py <segment> <name> <sector> <email> <phone>\n")
        sys.exit(1)

    try:
        segment, name, sector, email, phone = sys.argv[1:6]
        segment_key = segment.lower().strip()

        if segment_key not in SEGMENT_TEMPLATE:
            sys.stderr.write(f"Segmento inválido: {segment}\n")
            sys.exit(1)

        if not validate_input(name) or not validate_input(sector) or not validate_input(email, 100):
            sys.stderr.write("Erro: entrada inválida.\n")
            sys.exit(1)

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'public', 'assets')
        template_path = os.path.join(assets_dir, SEGMENT_TEMPLATE[segment_key])

        if not os.path.exists(template_path):
            sys.stderr.write(f"Template não encontrado: {template_path}\n")
            sys.exit(1)

        image = Image.open(template_path).convert('RGB')
        draw  = ImageDraw.Draw(image)

        font_path = get_font_path()
        if font_path:
            font_name = ImageFont.truetype(font_path, FONT_SIZE_NAME)
            font_body = ImageFont.truetype(font_path, FONT_SIZE_BODY)
        else:
            font_name = ImageFont.load_default()
            font_body = ImageFont.load_default()

        p = POSITIONS

        # Cover placeholder text with white
        draw.rectangle(p['name']['cover'],   fill='white')
        draw.rectangle(p['sector']['cover'], fill='white')
        draw.rectangle(p['email']['cover'],  fill='white')

        # Draw user data
        draw.text((p['name']['x'],   p['name']['y']),   name.upper(), font=font_name, fill=COLORS['name'])
        draw.text((p['sector']['x'], p['sector']['y']), sector,        font=font_body, fill=COLORS['body'])
        draw.text((p['email']['x'],  p['email']['y']),  email,         font=font_body, fill=COLORS['body'])
        if phone and phone.strip():
            draw.text((p['phone']['x'], p['phone']['y']), phone.strip(), font=font_body, fill=COLORS['body'])

        # Paste social media icons (small, aligned to right side)
        def paste_icon(name, pos):
            try:
                icon_path = os.path.join(assets_dir, name)
                if not os.path.exists(icon_path):
                    return
                icon = Image.open(icon_path).convert('RGBA')
                icon = icon.resize((32, 32), Image.LANCZOS)
                image.paste(icon, pos, icon)
            except Exception:
                pass

        paste_icon('3.png', (p['instagram']['x'], p['instagram']['y']))
        paste_icon('4.png', (p['linkedin']['x'],  p['linkedin']['y']))

        sys.stdout.buffer.write(image_to_bytes(image))

    except Exception as e:
        sys.stderr.write(f"Erro ao gerar imagem: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
