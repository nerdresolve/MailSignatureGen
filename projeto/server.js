const express  = require('express');
const multer   = require('multer');
const { spawn } = require('child_process');
const path     = require('path');

const app    = express();
const upload = multer();
const PORT   = 3000;
const HOST   = 'localhost';

const VALID_SEGMENTS = [
  'corporativo',
  'Servicos',
  'offshore',
  'bunker',
  'Operacoes',
  'estaleiro'
];

const VALIDATION_RULES = {
  name:   { maxLength: 50, pattern: /^[a-zA-ZÀ-ÿ\s]+$/ },
  sector: { pattern: /^[a-zA-ZÀ-ÿ0-9@._\s&()-]+$/ },
  email:  { pattern: /^[^\s@]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/ },
  phone:  { pattern: /^\+55\s\(\d{2}\)\s\d{4,5}-\d{4}$/ }
};

const validateInputs = (segment, name, sector, email, phone) => {
  if (!segment || !VALID_SEGMENTS.includes(segment.toLowerCase()))
    return { valid: false, error: 'Segmento inválido' };
  if (!name || !sector || !email)
    return { valid: false, error: 'Campos obrigatórios vazios' };
  if (name.length > VALIDATION_RULES.name.maxLength || !VALIDATION_RULES.name.pattern.test(name))
    return { valid: false, error: 'Nome inválido' };
  if (!VALIDATION_RULES.sector.pattern.test(sector))
    return { valid: false, error: 'Setor inválido' };
  if (!VALIDATION_RULES.email.pattern.test(email))
    return { valid: false, error: 'Email inválido' };
  if (phone && !VALIDATION_RULES.phone.pattern.test(phone))
    return { valid: false, error: 'Telefone inválido' };
  return { valid: true };
};

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/signaturegenerator', upload.none(), (req, res) => {
  const { signSegment, signName, signSector, signEmail, signPhone } = req.body;

  const validation = validateInputs(signSegment, signName, signSector, signEmail, signPhone || '');
  if (!validation.valid) return res.status(400).send(validation.error);

  const pythonPath = path.resolve(__dirname, 'signaturegenerator.py');
  if (!pythonPath.startsWith(path.resolve(__dirname)))
    return res.status(400).send('Caminho inválido');

  // Try python3 first, fall back to python (Windows)
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

  const pythonProcess = spawn(pythonCmd, [
    pythonPath,
    signSegment.toLowerCase(),
    signName,
    signSector,
    signEmail,
    signPhone || ''
  ]);

  let imageBuffer = Buffer.alloc(0);
  let hasError    = false;

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
    } else {
      res.status(500).send('Erro ao gerar imagem da assinatura.');
    }
  });
});

app.listen(PORT, HOST, () => {
  console.log(`Servidor rodando em http://${HOST}:${PORT}`);
});

