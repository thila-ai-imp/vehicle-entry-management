-- CMDA Steel Yard Vehicle Entry Management
-- Engine: SQLite 3 (file: cmda_yard.db)
-- One file database on the server PC. Gate terminals talk to this over LAN.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

-- Lookup tables so gates, vehicle classes, and fees can be changed without code edits.

CREATE TABLE IF NOT EXISTS gates (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS vehicle_types (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  single_rate REAL NOT NULL,
  multiple_rate REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicles (
  id TEXT PRIMARY KEY,
  number TEXT NOT NULL,
  entryGate TEXT NOT NULL,
  exitGate TEXT,
  type TEXT NOT NULL,
  entryType TEXT NOT NULL CHECK (entryType IN ('single', 'multiple')),
  entry TEXT NOT NULL,
  exit TEXT,
  amount REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  FOREIGN KEY (entryGate) REFERENCES gates(code),
  FOREIGN KEY (exitGate) REFERENCES gates(code),
  FOREIGN KEY (type) REFERENCES vehicle_types(code)
);

CREATE INDEX IF NOT EXISTS idx_vehicles_number ON vehicles(number);
CREATE INDEX IF NOT EXISTS idx_vehicles_entry ON vehicles(entry);
CREATE INDEX IF NOT EXISTS idx_vehicles_exit ON vehicles(exit);
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(exit, number);

-- A vehicle number may appear only once while still inside the yard.
CREATE UNIQUE INDEX IF NOT EXISTS idx_vehicles_inside_number
  ON vehicles(number)
  WHERE exit IS NULL;

INSERT OR IGNORE INTO gates (code, name) VALUES
  ('GATE 1', 'Gate 1'),
  ('GATE 2', 'Gate 2'),
  ('GATE 3', 'Gate 3');

INSERT OR IGNORE INTO vehicle_types (code, name, single_rate, multiple_rate) VALUES
  ('lorry', 'Lorry / Trailers / Multiaxle', 165, 240),
  ('lmv', 'Light Motor Vehicle', 65, 120),
  ('association', 'Steel Yard Trailers Association', 65, 120);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  display_name TEXT NOT NULL DEFAULT 'Administrator',
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
