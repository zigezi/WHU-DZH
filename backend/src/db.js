import pg from 'pg';

const { Pool } = pg;

export const pool = new Pool({
  host: process.env.PGHOST || '127.0.0.1',
  port: Number(process.env.PGPORT || 5432),
  user: process.env.PGUSER || 'appuser',
  password: process.env.PGPASSWORD || 'apppass',
  database: process.env.PGDATABASE || 'authdb',
});

export async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id          SERIAL PRIMARY KEY,
      username    VARCHAR(50)  UNIQUE NOT NULL,
      email       VARCHAR(120) UNIQUE NOT NULL,
      password    VARCHAR(255) NOT NULL,
      created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS sessions (
      id          SERIAL PRIMARY KEY,
      user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      name        TEXT NOT NULL DEFAULT '',
      folder      TEXT NOT NULL,
      status      TEXT NOT NULL DEFAULT 'active',
      created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, created_at);

    CREATE TABLE IF NOT EXISTS messages (
      id          SERIAL PRIMARY KEY,
      user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      session_id  INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
      role        TEXT NOT NULL DEFAULT 'user',
      content     TEXT NOT NULL,
      created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, created_at);
  `);

  await pool.query(`ALTER TABLE messages ADD COLUMN IF NOT EXISTS session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE;`);
  await pool.query(`ALTER TABLE messages ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';`);
  await pool.query(`CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);`);

  await pool.query(`
    CREATE TABLE IF NOT EXISTS builds (
      id SERIAL PRIMARY KEY,
      session_id INTEGER REFERENCES sessions(id),
      user_id INTEGER REFERENCES users(id),
      status VARCHAR(32) NOT NULL DEFAULT 'queued',
      iterations INTEGER NOT NULL DEFAULT 0,
      error_summary TEXT,
      created_at TIMESTAMP DEFAULT NOW(),
      finished_at TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS build_events (
      id SERIAL PRIMARY KEY,
      build_id INTEGER REFERENCES builds(id),
      agent VARCHAR(32),
      event_type VARCHAR(32),
      content TEXT,
      created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_builds_session ON builds(session_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_build_events_build ON build_events(build_id, id);

    CREATE TABLE IF NOT EXISTS test_containers (
      id SERIAL PRIMARY KEY,
      session_id INTEGER REFERENCES sessions(id),
      user_id INTEGER REFERENCES users(id),
      container_id VARCHAR(64),
      host_port INTEGER,
      url TEXT,
      status VARCHAR(16) DEFAULT 'running',
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);

  console.log('Database tables "users", "sessions", "messages", "builds", "build_events", "test_containers" ready');
}
