import io
import os
import platform
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

SEGMENT_TEMPLATE = {
    'corporativo': 'GrupoNerdResolve.PNG',
    'Operacoes': 'NerdResolveOperacoes.PNG',
    'Servicos': 'NerdResolveServicos.PNG',
    'offshore': 'NerdResolveOffshore.PNG',
    'estaleiro': 'NerdResolveEstaleiro.PNG',
}

POSITIONS = {
    'name': {'x': 28, 'y': 126, 'cover': (24, 122, 285, 160)},
    'sector': {'x': 28, 'y': 162, 'cover': (24, 158, 255, 186)},
    'email': {'x': 28, 'y': 199, 'cover': (24, 195, 325, 223)},
    'phone': {'x': 28, 'y': 234, 'cover': (24, 230, 210, 255)},
}

COLORS = {
    'name': (0, 123, 77),
    'body': (109, 109, 109),
}

FONT_SIZE_NAME = 22
FONT_SIZE_BODY = 16


def get_font_path():
    bundled = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'public',
        'assets',
        'LiberationSans-Regular.ttf',
    )
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

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def normalize_text(value):
    return unicodedata.normalize('NFC', value).strip()


def validate_input(value, max_length=50):
    return isinstance(value, str) and 0 < len(value) <= max_length


def image_to_bytes(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def main():
    if len(sys.argv) < 6:
        sys.stderr.write("Uso: signaturegenerator.py <segment> <name> <sector> <email> <phone>\n")
        sys.exit(1)

    try:
        segment, name, sector, email, phone = sys.argv[1:6]
        segment_key = normalize_text(segment).lower()
        name = normalize_text(name)
        sector = normalize_text(sector)
        email = normalize_text(email)
        phone = normalize_text(phone)

        if segment_key not in SEGMENT_TEMPLATE:
            sys.stderr.write(f"Segmento inválido: {segment}\n")
            sys.exit(1)

        if not validate_input(name) or not validate_input(sector) or not validate_input(email, 100):
            sys.stderr.write("Erro: entrada inválida.\n")
            sys.exit(1)

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public', 'assets')
        template_path = os.path.join(assets_dir, SEGMENT_TEMPLATE[segment_key])

        if not os.path.exists(template_path):
            sys.stderr.write(f"Template não encontrado: {template_path}\n")
            sys.exit(1)

        image = Image.open(template_path).convert('RGB')
        draw = ImageDraw.Draw(image)

        font_path = get_font_path()
        if font_path:
            font_name = ImageFont.truetype(font_path, FONT_SIZE_NAME)
            font_body = ImageFont.truetype(font_path, FONT_SIZE_BODY)
        else:
            font_name = ImageFont.load_default()
            font_body = ImageFont.load_default()

        p = POSITIONS

        draw.rectangle(p['name']['cover'], fill='white')
        draw.rectangle(p['sector']['cover'], fill='white')
        draw.rectangle(p['email']['cover'], fill='white')
        draw.rectangle(p['phone']['cover'], fill='white')

        draw.text((p['name']['x'], p['name']['y']), name.upper(), font=font_name, fill=COLORS['name'])
        draw.text((p['sector']['x'], p['sector']['y']), sector, font=font_body, fill=COLORS['body'])
        draw.text((p['email']['x'], p['email']['y']), email, font=font_body, fill=COLORS['body'])
        if phone:
            draw.text((p['phone']['x'], p['phone']['y']), phone, font=font_body, fill=COLORS['body'])

        sys.stdout.buffer.write(image_to_bytes(image))

    except Exception as exc:
        sys.stderr.write(f"Erro ao gerar imagem: {str(exc)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
