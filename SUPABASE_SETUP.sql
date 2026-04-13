-- ============================================================
-- SismaVer2 — Setup tabelle Supabase
-- Progetto: ycdwgehifbyxarrsofmz.supabase.co
-- Eseguire nel SQL Editor di Supabase
-- ============================================================

-- Tabella messaggi chat pubblica
CREATE TABLE IF NOT EXISTS chat_messages (
    id         BIGSERIAL PRIMARY KEY,
    username   TEXT,
    contenuto  TEXT NOT NULL,
    regione    TEXT DEFAULT 'Campania',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella segnalazioni eventi
CREATE TABLE IF NOT EXISTS event_reports (
    id          BIGSERIAL PRIMARY KEY,
    username    TEXT,
    contenuto   TEXT,
    localita    TEXT,
    tipo_evento TEXT,
    intensita   INTEGER,
    data_ora    TIMESTAMPTZ DEFAULT NOW(),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Abilita accesso pubblico (RLS)
ALTER TABLE chat_messages  ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_reports  ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "allow_all" ON chat_messages  FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "allow_all" ON event_reports  FOR ALL USING (true) WITH CHECK (true);
