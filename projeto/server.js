const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 3000;
const HOST = '0.0.0.0';

const VALID_SEGMENTS = [
  'corporativo',
  'Operacoes',
  'Servicos',
  'offshore',
  'estaleiro'
];

const VALIDATION_RULES = {
  name: { maxLength: 50, pattern: /^[\p{L}\p{M}\s'-]+$/u },
  sector: { pattern: /^[\p{L}\p{M}\p{N}@._\s&()/-]+$/u },
  email: { pattern: /^[^\s@]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/ },
  phone: { pattern: /^\+55\s\(\d{2}\)\s\d{4,5}-\d{4}$/ }
};

const normalizeTextInput = (value) => value.normalize('NFC').trim();

const validateInputs = (segment, name, sector, email, phone) => {
  const normalizedName = normalizeTextInput(name);
  const normalizedSector = normalizeTextInput(sector);
  const normalizedEmail = email.trim();

  if (!segment || !VALID_SEGMENTS.includes(segment.toLowerCase())) {
    return { valid: false, error: 'Segmento invalido' };
  }

  if (!normalizedName || !normalizedSector || !normalizedEmail) {
    return { valid: false, error: 'Campos obrigatorios vazios' };
  }

  if (normalizedName.length > VALIDATION_RULES.name.maxLength || !VALIDATION_RULES.name.pattern.test(normalizedName)) {
    return { valid: false, error: 'Nome invalido' };
  }

  if (!VALIDATION_RULES.sector.pattern.test(normalizedSector)) {
    return { valid: false, error: 'Setor invalido' };
  }

  if (!VALIDATION_RULES.email.pattern.test(normalizedEmail)) {
    return { valid: false, error: 'Email invalido' };
  }

  if (phone && !VALIDATION_RULES.phone.pattern.test(phone)) {
    return { valid: false, error: 'Telefone invalido' };
  }

  return { valid: true };
};

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/signaturegenerator', (req, res) => {
  const { signSegment, signName, signSector, signEmail, signPhone } = req.body;
  const normalizedName = normalizeTextInput(signName);
  const normalizedSector = normalizeTextInput(signSector);
  const normalizedEmail = signEmail.trim();

  const validation = validateInputs(signSegment, normalizedName, normalizedSector, normalizedEmail, signPhone || '');
  if (!validation.valid) {
    return res.status(400).send(validation.error);
  }

  const pythonPath = path.resolve(__dirname, 'signaturegenerator.py');
  if (!pythonPath.startsWith(path.resolve(__dirname))) {
    return res.status(400).send('Caminho invalido');
  }

  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  const pythonProcess = spawn(pythonCmd, [
    pythonPath,
    signSegment.toLowerCase(),
    normalizedName,
    normalizedSector,
    normalizedEmail,
    signPhone || ''
  ]);

  let imageBuffer = Buffer.alloc(0);
  let hasError = false;

  pythonProcess.stdout.on('data', (data) => {
    imageBuffer = Buffer.concat([imageBuffer, data]);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error('Python stderr:', data.toString());
    hasError = true;
  });

  pythonProcess.on('error', () => res.status(500).send('Erro interno ao gerar assinatura.'));

  pythonProcess.on('close', (code) => {
    if (code === 0 && !hasError) {
      res.setHeader('Content-Disposition', 'attachment; filename="assinatura_NerdResolve.png"');
      res.setHeader('Content-Type', 'image/png');
      res.send(imageBuffer);
      return;
    }

    res.status(500).send('Erro ao gerar imagem da assinatura.');
  });
});

app.listen(PORT, HOST, () => {
  console.log(`Servidor rodando em http://${HOST}:${PORT}`);
});
