import io
import os
import platform
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

SEGMENT_TEMPLATES: dict[str, str] = {
    'corporativo': 'Corporativo.PNG',
    'Operacoes':  'Operacoes.PNG',
    'Servicos':  'Servicos.PNG',
    'offshore':    'Offshore.PNG',
    'estaleiro':   'Estaleiro.PNG',
}

TEXT_POSITIONS: dict[str, dict] = {
    'name':   {'x': 28, 'y': 138, 'clear_area': (24, 139, 285, 162)},
    'sector': {'x': 28, 'y': 170, 'clear_area': (24, 169, 255, 188)},
    'email':  {'x': 28, 'y': 208, 'clear_area': (24, 207, 325, 230)},
    'phone':  {'x': 28, 'y': 235, 'clear_area': (24, 234, 230, 256)},
}

COLOR_NAME = (0, 123, 77)
COLOR_BODY = (109, 109, 109)

FONT_SIZE_NAME = 22
FONT_SIZE_BODY = 16

MAX_NAME_LENGTH  = 50
MAX_EMAIL_LENGTH = 100


def resolve_font_path() -> str | None:
    bundled_font = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'public', 'assets', 'LiberationSans-Regular.ttf',
    )
    if os.path.exists(bundled_font):
        return bundled_font

    system_fonts: dict[str, list[str]] = {
        'Windows': [
            r'C:\Windows\Fonts\l_10646.ttf',
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\calibri.ttf',
        ],
        'Darwin': [
            '/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
        ],
        'Linux': [
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ],
    }

    candidates = system_fonts.get(platform.system(), system_fonts['Linux'])
    return next((path for path in candidates if os.path.exists(path)), None)


def normalize(value: str) -> str:
    return unicodedata.normalize('NFC', value).strip()


def is_valid_field(value: str, max_length: int = MAX_NAME_LENGTH) -> bool:
    return isinstance(value, str) and 0 < len(value) <= max_length


def encode_image_as_png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def load_fonts(font_path: str | None) -> tuple:
    if font_path:
        return (
            ImageFont.truetype(font_path, FONT_SIZE_NAME),
            ImageFont.truetype(font_path, FONT_SIZE_BODY),
        )
    fallback = ImageFont.load_default()
    return fallback, fallback


def render_signature(template_path: str, name: str, sector: str, email: str, phone: str) -> bytes:
    image = Image.open(template_path).convert('RGB')
    draw  = ImageDraw.Draw(image)

    font_name, font_body = load_fonts(resolve_font_path())

    for field in TEXT_POSITIONS.values():
        draw.rectangle(field['clear_area'], fill='white')

    pos = TEXT_POSITIONS
    draw.text((pos['name']['x'],   pos['name']['y']),   name.upper(), font=font_name, fill=COLOR_NAME)
    draw.text((pos['sector']['x'], pos['sector']['y']), sector,       font=font_body, fill=COLOR_BODY)
    draw.text((pos['email']['x'],  pos['email']['y']),  email,        font=font_body, fill=COLOR_BODY)

    if phone:
        draw.text((pos['phone']['x'], pos['phone']['y']), phone, font=font_body, fill=COLOR_BODY)

    return encode_image_as_png(image)


def parse_args() -> tuple[str, str, str, str, str]:
    if len(sys.argv) < 6:
        sys.stderr.write('Uso: signaturegenerator.py <segmento> <nome> <setor> <email> <telefone>\n')
        sys.exit(1)

    segment, name, sector, email, phone = (normalize(arg) for arg in sys.argv[1:6])
    return segment.lower(), name, sector, email, phone


def main() -> None:
    segment_key, name, sector, email, phone = parse_args()

    if segment_key not in SEGMENT_TEMPLATES:
        sys.stderr.write(f'Segmento inválido: {segment_key}\n')
        sys.exit(1)

    if not is_valid_field(name) or not is_valid_field(sector) or not is_valid_field(email, MAX_EMAIL_LENGTH):
        sys.stderr.write('Entrada inválida.\n')
        sys.exit(1)

    assets_dir    = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public', 'assets')
    template_path = os.path.join(assets_dir, SEGMENT_TEMPLATES[segment_key])

    if not os.path.exists(template_path):
        sys.stderr.write(f'Template não encontrado: {template_path}\n')
        sys.exit(1)

    try:
        png_bytes = render_signature(template_path, name, sector, email, phone)
        sys.stdout.buffer.write(png_bytes)
    except Exception as error:
        sys.stderr.write(f'Erro ao gerar imagem: {error}\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
