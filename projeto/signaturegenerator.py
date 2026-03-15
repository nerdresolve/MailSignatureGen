import sys
import os
import subprocess
import glob
import tempfile
import shutil

# Segment key -> slide index (0-based) inside blankmodels.pptx
SEGMENT_SLIDE_MAP = {
    'corporativo': 0,
    'Servicos':  1,
    'offshore':    2,
    'bunker':      3,
}


def validate_input(value, max_length=50):
    return isinstance(value, str) and len(value) > 0 and len(value) <= max_length


def replace_text_preserving_format(shape, first_line, second_line=None):
    """Replace text in a shape while preserving run formatting."""
    tf = shape.text_frame
    if not tf.paragraphs:
        return
    para0 = tf.paragraphs[0]
    if para0.runs:
        para0.runs[0].text = first_line
        for run in para0.runs[1:]:
            run.text = ''
    if len(tf.paragraphs) > 1:
        para1 = tf.paragraphs[1]
        if para1.runs:
            para1.runs[0].text = second_line if second_line else ''
            for run in para1.runs[1:]:
                run.text = ''


def main():
    if len(sys.argv) < 6:
        sys.stderr.write("Uso: signaturegenerator.py <segment> <name> <sector> <email> <phone>\n")
        sys.exit(1)

    try:
        segment, name, sector, email, phone = sys.argv[1:6]
        segment_key = segment.lower().strip()

        if segment_key not in SEGMENT_SLIDE_MAP:
            sys.stderr.write(f"Segmento inválido: {segment}\n")
            sys.exit(1)

        if not validate_input(name) or not validate_input(sector) or not validate_input(email, 100):
            sys.stderr.write("Erro: entrada inválida.\n")
            sys.exit(1)

        slide_idx = SEGMENT_SLIDE_MAP[segment_key]
        base_pptx = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'public', 'assets', 'blankmodels.pptx')

        if not os.path.exists(base_pptx):
            sys.stderr.write("Arquivo base não encontrado.\n")
            sys.exit(1)

        from pptx import Presentation
        prs = Presentation(base_pptx)
        slide = prs.slides[slide_idx]

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            sname = shape.name
            if sname == 'CaixaDeTexto 5':
                replace_text_preserving_format(shape, name.upper())
            elif sname == 'CaixaDeTexto 6':
                replace_text_preserving_format(shape, sector)
            elif sname == 'CaixaDeTexto 7':
                replace_text_preserving_format(shape, email, phone if phone else '')

        tmpdir = tempfile.mkdtemp()
        try:
            tmp_pptx = os.path.join(tmpdir, 'signature.pptx')
            prs.save(tmp_pptx)

            # Convert PPTX to PDF via LibreOffice
            conv = subprocess.run(
                ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', tmpdir, tmp_pptx],
                capture_output=True
            )
            if conv.returncode != 0:
                sys.stderr.write(f"Erro LibreOffice: {conv.stderr.decode()}\n")
                sys.exit(1)

            pdf_files = glob.glob(os.path.join(tmpdir, '*.pdf'))
            if not pdf_files:
                sys.stderr.write("PDF não gerado.\n")
                sys.exit(1)

            # Convert the correct PDF page to PNG
            png_prefix = os.path.join(tmpdir, 'sig')
            page_num = slide_idx + 1
            ppm = subprocess.run(
                ['pdftoppm', '-png', '-r', '150',
                 '-f', str(page_num), '-l', str(page_num),
                 pdf_files[0], png_prefix],
                capture_output=True
            )
            if ppm.returncode != 0:
                sys.stderr.write(f"Erro pdftoppm: {ppm.stderr.decode()}\n")
                sys.exit(1)

            png_files = sorted(glob.glob(os.path.join(tmpdir, 'sig*.png')))
            if not png_files:
                sys.stderr.write("PNG não gerado.\n")
                sys.exit(1)

            with open(png_files[0], 'rb') as f:
                sys.stdout.buffer.write(f.read())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as e:
        sys.stderr.write(f"Erro ao gerar imagem: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
