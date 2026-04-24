const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 3000;
const HOST = '0.0.0.0';

const VALID_SEGMENTS = ['corporativo', 'Operacoes', 'Servicos', 'offshore', 'estaleiro'];

const FIELD_RULES = {
  name:   { maxLength: 50, pattern: /^[\p{L}\p{M}\s'-]+$/u },
  sector: { pattern: /^[\p{L}\p{M}\p{N}@._\s&()/-]+$/u },
  email:  { pattern: /^[^\s@]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/ },
  phone:  { pattern: /^\+55\s\(\d{2}\)\s\d{4,5}-\d{4}$/ },
};

const PYTHON_SCRIPT_PATH = path.resolve(__dirname, 'signaturegenerator.py');
const PYTHON_CMD = process.platform === 'win32' ? 'python' : 'python3';

const normalize = (value) => value.normalize('NFC').trim();

const validateFields = ({ segment, name, sector, email, phone }) => {
  if (!segment || !VALID_SEGMENTS.includes(segment.toLowerCase()))
    return 'Segmento inválido.';

  if (!name || !sector || !email)
    return 'Campos obrigatórios não preenchidos.';

  if (name.length > FIELD_RULES.name.maxLength || !FIELD_RULES.name.pattern.test(name))
    return 'Nome inválido.';

  if (!FIELD_RULES.sector.pattern.test(sector))
    return 'Setor inválido.';

  if (!FIELD_RULES.email.pattern.test(email))
    return 'E-mail inválido.';

  if (phone && !FIELD_RULES.phone.pattern.test(phone))
    return 'Telefone inválido.';

  return null;
};

const generateSignatureImage = ({ segment, name, sector, email, phone }, onSuccess, onError) => {
  const process = spawn(PYTHON_CMD, [
    PYTHON_SCRIPT_PATH,
    segment.toLowerCase(),
    name,
    sector,
    email,
    phone || '',
  ]);

  let imageChunks = [];
  let stderrOutput = '';

  process.stdout.on('data', (chunk) => imageChunks.push(chunk));
  process.stderr.on('data', (chunk) => { stderrOutput += chunk.toString(); });
  process.on('error', onError);

  process.on('close', (exitCode) => {
    if (stderrOutput) console.error('[python]', stderrOutput.trim());

    const imageBuffer = Buffer.concat(imageChunks);

    if (exitCode === 0 && imageBuffer.length > 0) {
      onSuccess(imageBuffer);
    } else {
      onError(new Error(`Python encerrou com código ${exitCode}`));
    }
  });
};

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/signaturegenerator', (req, res) => {
  const fields = {
    segment: req.body.signSegment,
    name:    normalize(req.body.signName    ?? ''),
    sector:  normalize(req.body.signSector  ?? ''),
    email:   (req.body.signEmail ?? '').trim(),
    phone:   (req.body.signPhone ?? '').trim(),
  };

  const validationError = validateFields(fields);
  if (validationError) return res.status(400).send(validationError);

  generateSignatureImage(
    fields,
    (imageBuffer) => {
      res.setHeader('Content-Disposition', 'attachment; filename="assinatura_NerdResolve.png"');
      res.setHeader('Content-Type', 'image/png');
      res.send(imageBuffer);
    },
    () => res.status(500).send('Erro ao gerar assinatura.'),
  );
});

app.listen(PORT, HOST, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});
