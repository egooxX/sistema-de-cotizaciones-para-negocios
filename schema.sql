-- Esquema SQLite del Sistema de Cotizaciones (misma estructura que la v1 web).
CREATE TABLE IF NOT EXISTS business_profile (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL DEFAULT 'Mi Negocio',
  tagline TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL DEFAULT '',
  phone TEXT NOT NULL DEFAULT '',
  email TEXT NOT NULL DEFAULT '',
  address TEXT NOT NULL DEFAULT '',
  rfc TEXT NOT NULL DEFAULT '',
  default_tax_percent REAL NOT NULL DEFAULT 16,
  default_validity_days INTEGER NOT NULL DEFAULT 15,
  notes TEXT NOT NULL DEFAULT 'Precios en MXN. Cotización sujeta a disponibilidad.',
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  price REAL NOT NULL DEFAULT 0,
  unit TEXT NOT NULL DEFAULT 'pieza',
  category TEXT NOT NULL DEFAULT 'General',
  active INTEGER NOT NULL DEFAULT 1,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  company TEXT NOT NULL DEFAULT '',
  phone TEXT NOT NULL DEFAULT '',
  email TEXT NOT NULL DEFAULT '',
  address TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS quotes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  folio TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL DEFAULT 'Cotización de servicios',
  client_id INTEGER,
  client_name TEXT NOT NULL,
  client_company TEXT NOT NULL DEFAULT '',
  client_phone TEXT NOT NULL DEFAULT '',
  client_email TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pendiente',
  valid_until TEXT NOT NULL DEFAULT '',
  discount_percent REAL NOT NULL DEFAULT 0,
  tax_percent REAL NOT NULL DEFAULT 16,
  notes TEXT NOT NULL DEFAULT '',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS quote_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quote_id INTEGER NOT NULL,
  catalog_id INTEGER,
  description TEXT NOT NULL,
  detail TEXT NOT NULL DEFAULT '',
  quantity REAL NOT NULL DEFAULT 1,
  unit_price REAL NOT NULL DEFAULT 0,
  unit TEXT NOT NULL DEFAULT 'pieza',
  sort_order INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO business_profile
  (id, name, tagline, owner, phone, email, address, rfc,
   default_tax_percent, default_validity_days, notes, updated_at)
VALUES
  (1, 'Mi Negocio', 'Servicios profesionales', '', '', '', '', '',
   16, 15, 'Precios en MXN. Forma de pago: 50% anticipo, 50% al entregar. Cotización sujeta a disponibilidad.',
   1735689600000);
