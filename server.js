const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const session = require('express-session');
const cors = require('cors');
const crypto = require('crypto');
const os = require('os');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = Number(process.env.PORT) || 3001;
const HOST = '0.0.0.0';
const dbPath = path.join(__dirname, 'cmda_yard.db');
const schemaPath = path.join(__dirname, 'db', 'schema.sql');
const publicDir = path.join(__dirname, 'public');
const SESSION_SECRET = process.env.SESSION_SECRET || 'cmda-steel-yard-intranet-session';

app.use(cors({ origin: true, credentials: true }));
app.use(express.json({ limit: '100kb' }));
app.use(session({
  name: 'cmda.sid',
  secret: SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    sameSite: 'lax',
    maxAge: 12 * 60 * 60 * 1000
  }
}));

const db = new sqlite3.Database(dbPath);

function runAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) reject(err);
      else resolve(this);
    });
  });
}

function getAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

function allAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

function initDatabase() {
  return new Promise((resolve, reject) => {
    const schema = fs.readFileSync(schemaPath, 'utf8');
    db.exec(schema, (err) => {
      if (err) reject(err);
      else resolve();
    });
  });
}

function hashPassword(password, salt) {
  return crypto.scryptSync(password, salt, 64).toString('hex');
}

function passwordsMatch(password, salt, expectedHash) {
  const actual = hashPassword(password, salt);
  const a = Buffer.from(actual, 'hex');
  const b = Buffer.from(expectedHash, 'hex');
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

async function seedAdmin() {
  const existing = await getAsync('SELECT id FROM users WHERE username = ?', ['admin']);
  if (existing) return;
  const salt = crypto.randomBytes(16).toString('hex');
  await runAsync(
    'INSERT INTO users (username, password_hash, salt, display_name) VALUES (?, ?, ?, ?)',
    ['admin', hashPassword('admin', salt), salt, 'Administrator']
  );
  console.log('Default operator created: username admin / password admin');
}

function lanAddresses() {
  const nets = os.networkInterfaces();
  const ips = [];
  for (const name of Object.keys(nets)) {
    for (const net of nets[name] || []) {
      if (net.family === 'IPv4' && !net.internal) ips.push(net.address);
    }
  }
  return ips;
}

function normalizePlate(value) {
  return String(value || '')
    .trim()
    .toUpperCase()
    .replace(/\s+/g, ' ');
}

function newId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function calcAmount(rate, entry, exit) {
  const start = new Date(entry);
  const end = new Date(exit);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) {
    throw new Error('Invalid entry or exit time');
  }
  const hours = Math.max(0, (end - start) / 3600000);
  const slabs = Math.max(1, Math.ceil(hours / 24));
  return { hours, slabs, amount: slabs * Number(rate) };
}

function requireAuth(req, res, next) {
  if (req.session && req.session.user) return next();
  return res.status(401).json({ error: 'Please sign in.' });
}

app.get('/api/health', async (_req, res) => {
  try {
    await getAsync('SELECT 1 AS ok');
    res.json({ ok: true, time: new Date().toISOString() });
  } catch (err) {
    res.status(500).json({ ok: false, error: err.message });
  }
});

app.get('/api/session', (req, res) => {
  if (!req.session.user) return res.status(401).json({ error: 'Not signed in.' });
  res.json(req.session.user);
});

app.post('/api/login', async (req, res) => {
  try {
    const username = String(req.body.username || '').trim();
    const password = String(req.body.password || '');
    if (!username || !password) {
      return res.status(400).json({ error: 'Enter username and password.' });
    }
    const user = await getAsync('SELECT * FROM users WHERE username = ?', [username]);
    if (!user || !passwordsMatch(password, user.salt, user.password_hash)) {
      return res.status(401).json({ error: 'Invalid username or password.' });
    }
    req.session.user = {
      id: user.id,
      username: user.username,
      displayName: user.display_name
    };
    res.json({ ok: true, user: req.session.user });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/logout', (req, res) => {
  req.session.destroy(() => {
    res.clearCookie('cmda.sid');
    res.json({ ok: true });
  });
});

app.get('/api/lookups', requireAuth, async (_req, res) => {
  try {
    const [gates, types] = await Promise.all([
      allAsync('SELECT code, name FROM gates WHERE active = 1 ORDER BY code'),
      allAsync(`SELECT code, name, single_rate, multiple_rate FROM vehicle_types
         ORDER BY CASE code WHEN 'lorry' THEN 1 WHEN 'lmv' THEN 2 ELSE 3 END`)
    ]);
    res.json({ gates, types });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/vehicles', requireAuth, async (_req, res) => {
  try {
    const rows = await allAsync('SELECT * FROM vehicles ORDER BY rowid DESC');
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/vehicles', requireAuth, async (req, res) => {
  try {
    const number = normalizePlate(req.body.number);
    const entryGate = String(req.body.entryGate || '').trim();
    const type = String(req.body.type || '').trim();
    const entryType = String(req.body.entryType || '').trim();
    const entry = String(req.body.entry || '').trim();
    const id = String(req.body.id || newId());

    if (!number || !entryGate || !type || !entryType || !entry) {
      return res.status(400).json({ error: 'Vehicle number, gate, type, entry type, and entry time are required.' });
    }
    if (!['single', 'multiple'].includes(entryType)) {
      return res.status(400).json({ error: 'Entry type must be single or multiple.' });
    }

    const gate = await getAsync('SELECT code FROM gates WHERE code = ? AND active = 1', [entryGate]);
    if (!gate) return res.status(400).json({ error: 'Unknown entry gate.' });

    const vehicleType = await getAsync('SELECT code FROM vehicle_types WHERE code = ?', [type]);
    if (!vehicleType) return res.status(400).json({ error: 'Unknown vehicle type.' });

    const inside = await getAsync(
      'SELECT id FROM vehicles WHERE number = ? AND exit IS NULL',
      [number]
    );
    if (inside) {
      return res.status(409).json({ error: `Vehicle ${number} is already inside the yard.` });
    }

    await runAsync(
      `INSERT INTO vehicles (id, number, entryGate, exitGate, type, entryType, entry, exit, amount)
       VALUES (?, ?, ?, NULL, ?, ?, ?, NULL, 0)`,
      [id, number, entryGate, type, entryType, entry]
    );

    const row = await getAsync('SELECT * FROM vehicles WHERE id = ?', [id]);
    res.status(201).json(row);
  } catch (err) {
    if (String(err.message).includes('UNIQUE')) {
      return res.status(409).json({ error: 'Vehicle is already inside the yard.' });
    }
    res.status(500).json({ error: err.message });
  }
});

app.put('/api/vehicles/:id/exit', requireAuth, async (req, res) => {
  try {
    const vehicle = await getAsync('SELECT * FROM vehicles WHERE id = ?', [req.params.id]);
    if (!vehicle) return res.status(404).json({ error: 'Vehicle record not found.' });
    if (vehicle.exit) return res.status(409).json({ error: 'This vehicle has already exited.' });

    const exit = String(req.body.exit || '').trim();
    const exitGate = String(req.body.exitGate || '').trim();
    if (!exit || !exitGate) {
      return res.status(400).json({ error: 'Exit time and exit gate are required.' });
    }

    const gate = await getAsync('SELECT code FROM gates WHERE code = ? AND active = 1', [exitGate]);
    if (!gate) return res.status(400).json({ error: 'Unknown exit gate.' });

    const rates = await getAsync(
      'SELECT single_rate, multiple_rate FROM vehicle_types WHERE code = ?',
      [vehicle.type]
    );
    if (!rates) return res.status(400).json({ error: 'Unknown vehicle type on this record.' });

    const rate = vehicle.entryType === 'multiple' ? rates.multiple_rate : rates.single_rate;
    const billed = calcAmount(rate, vehicle.entry, exit);

    await runAsync(
      `UPDATE vehicles
       SET exit = ?, exitGate = ?, amount = ?, updated_at = datetime('now','localtime')
       WHERE id = ? AND exit IS NULL`,
      [exit, exitGate, billed.amount, req.params.id]
    );

    const row = await getAsync('SELECT * FROM vehicles WHERE id = ?', [req.params.id]);
    res.json({ ...row, hours: billed.hours, slabs: billed.slabs });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.get('/', (req, res) => {
  if (req.session && req.session.user) {
    return res.sendFile(path.join(publicDir, 'index.html'));
  }
  return res.sendFile(path.join(publicDir, 'login.html'));
});

app.use(express.static(publicDir, { index: false }));

async function start() {
  await initDatabase();
  await seedAdmin();
  app.listen(PORT, HOST, () => {
    const ips = lanAddresses();
    console.log('CMDA Vehicle Entry server is running.');
    console.log(`Database file: ${dbPath}`);
    console.log(`On this PC:    http://localhost:${PORT}`);
    if (ips.length) {
      ips.forEach((ip) => console.log(`On LAN client: http://${ip}:${PORT}`));
    } else {
      console.log('No LAN IPv4 address found. Connect Ethernet/Wi-Fi and restart.');
    }
  });
}

start().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
