/**
 * Servidor HTTP.
 *
 * Serve a interface e expõe duas rotas: uma que descreve a marca configurada e
 * outra que gera a assinatura. Nada de marca ou de layout vive aqui — o
 * servidor lê `brands/<id>/brand.json` e repassa. Trocar de cliente é editar
 * aquele arquivo, nunca este.
 *
 * O desenho é feito pelo Python, chamado como subprocesso. A alternativa seria
 * reimplementar o layout em JavaScript e manter as duas versões em acordo.
 */

const express = require('express');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const RAIZ = path.resolve(__dirname, '..');
const DIR_MARCAS = path.join(RAIZ, 'brands');

const PORTA = Number(process.env.PORT) || 3000;
const HOST = process.env.HOST || '0.0.0.0';
const MARCA_PADRAO = process.env.BRAND || 'nerdresolve';
const PYTHON = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');

const LIMITES = { nome: 60, cargo: 60, email: 120, telefone: 24 };

/** Só letras, espaço, hífen e apóstrofo: nome de pessoa, não campo livre. */
const PADROES = {
  nome: /^[\p{L}\p{M}\s'’-]+$/u,
  cargo: /^[\p{L}\p{M}\p{N}\s&()./'’-]+$/u,
  email: /^[^\s@]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  telefone: /^[\d\s()+-]+$/,
};

const app = express();
app.use(express.json({ limit: '16kb' }));
app.use(express.urlencoded({ extended: false, limit: '16kb' }));
app.use(express.static(path.join(__dirname, 'public')));

/** Lê o brand.json da marca, ou null se ela não existir. */
function lerMarca(id) {
  if (!/^[a-z0-9][a-z0-9_-]*$/i.test(id)) return null; // barra travessia de caminho
  const arquivo = path.join(DIR_MARCAS, id, 'brand.json');
  if (!fs.existsSync(arquivo)) return null;
  try {
    return JSON.parse(fs.readFileSync(arquivo, 'utf8'));
  } catch (erro) {
    console.error(`[marca] ${id}/brand.json inválido:`, erro.message);
    return null;
  }
}

function validar({ nome, cargo, email, telefone }, marca) {
  const campos = { nome, cargo, email };

  for (const [campo, valor] of Object.entries(campos)) {
    if (!valor) return `Preencha o campo ${campo}.`;
    if (valor.length > LIMITES[campo]) return `O campo ${campo} é longo demais.`;
    if (!PADROES[campo].test(valor)) return `O campo ${campo} tem caracteres inválidos.`;
  }

  if (telefone) {
    if (telefone.length > LIMITES.telefone) return 'Telefone longo demais.';
    if (!PADROES.telefone.test(telefone)) return 'Telefone inválido.';
  } else if (marca.telefone?.obrigatorio) {
    return 'Telefone é obrigatório nesta marca.';
  }

  return null;
}

/** Chama o gerador e devolve o PNG. */
function gerar({ marca, perfil, nome, cargo, email, telefone }) {
  const argumentos = [
    '-m', 'app.cli',
    '--marca', marca,
    '--nome', nome,
    '--cargo', cargo,
    '--email', email,
  ];
  if (perfil) argumentos.push('--perfil', perfil);
  if (telefone) argumentos.push('--telefone', telefone);

  return new Promise((resolve, reject) => {
    const processo = spawn(PYTHON, argumentos, { cwd: RAIZ });

    const pedacos = [];
    let erros = '';

    processo.stdout.on('data', (pedaco) => pedacos.push(pedaco));
    processo.stderr.on('data', (pedaco) => { erros += pedaco.toString(); });
    processo.on('error', reject);

    processo.on('close', (codigo) => {
      const png = Buffer.concat(pedacos);
      if (codigo === 0 && png.length > 0) return resolve(png);
      reject(new Error(erros.trim() || `o gerador saiu com código ${codigo}`));
    });
  });
}

/** O que a interface precisa saber para se desenhar. */
app.get('/api/marca', (req, res) => {
  const id = req.query.id || MARCA_PADRAO;
  const marca = lerMarca(id);

  if (!marca) return res.status(404).json({ erro: `marca '${id}' não encontrada` });

  res.json({
    id,
    nome: marca.nome,
    cores: marca.cores ?? {},
    slogan: marca.slogan ?? '',
    perfis: marca.perfis ?? [],
    cargos: marca.cargos ?? [],
    dominioEmail: marca.dominioEmail ?? '',
    telefoneObrigatorio: Boolean(marca.telefone?.obrigatorio),
  });
});

/** As marcas instaladas, para uma instalação que atenda mais de um cliente. */
app.get('/api/marcas', (_req, res) => {
  if (!fs.existsSync(DIR_MARCAS)) return res.json([]);

  const marcas = fs.readdirSync(DIR_MARCAS)
    .filter((id) => fs.existsSync(path.join(DIR_MARCAS, id, 'brand.json')))
    .map((id) => ({ id, nome: lerMarca(id)?.nome ?? id }));

  res.json(marcas);
});

app.get('/brands/:id/:arquivo', (req, res) => {
  const { id, arquivo } = req.params;
  if (!/^[a-z0-9][a-z0-9_-]*$/i.test(id) || !/^[\w-]+\.(png|jpg|jpeg|svg|webp)$/i.test(arquivo)) {
    return res.sendStatus(400);
  }
  res.sendFile(path.join(DIR_MARCAS, id, arquivo));
});

app.post('/api/assinatura', async (req, res) => {
  const id = (req.body.marca || MARCA_PADRAO).trim();
  const marca = lerMarca(id);
  if (!marca) return res.status(404).send(`Marca '${id}' não encontrada.`);

  const dados = {
    marca: id,
    perfil: (req.body.perfil || '').trim(),
    nome: (req.body.nome || '').normalize('NFC').trim(),
    cargo: (req.body.cargo || '').normalize('NFC').trim(),
    email: (req.body.email || '').trim(),
    telefone: (req.body.telefone || '').trim(),
  };

  const problema = validar(dados, marca);
  if (problema) return res.status(400).send(problema);

  try {
    const png = await gerar(dados);
    const arquivo = `assinatura-${dados.nome.toLowerCase().replace(/\s+/g, '-')}.png`;

    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Content-Disposition', `attachment; filename="${arquivo}"`);
    res.send(png);
  } catch (erro) {
    console.error('[gerador]', erro.message);
    res.status(500).send('Não foi possível gerar a assinatura.');
  }
});

app.listen(PORTA, HOST, () => {
  console.log(`Gerador de assinaturas em http://localhost:${PORTA}  (marca: ${MARCA_PADRAO})`);
});
