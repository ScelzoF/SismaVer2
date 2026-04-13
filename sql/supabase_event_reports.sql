-- Tabella per le segnalazioni eventi
CREATE TABLE public.event_reports (
    id BIGSERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,
    descrizione TEXT NOT NULL,
    data_ora TIMESTAMPTZ DEFAULT NOW(),
    regione TEXT NOT NULL,
    comune TEXT NOT NULL,
    gravita TEXT DEFAULT 'Medio',
    lat FLOAT,
    lon FLOAT,
    user_id TEXT,
    contatto TEXT,
    is_moderated BOOLEAN DEFAULT false,
    moderation_level TEXT,
    moderation_score FLOAT,
    original_description TEXT
);

-- Indici per migliorare le performance
CREATE INDEX idx_event_reports_data_ora ON public.event_reports(data_ora);
CREATE INDEX idx_event_reports_regione ON public.event_reports(regione);
CREATE INDEX idx_event_reports_tipo ON public.event_reports(tipo);
CREATE INDEX idx_event_reports_gravita ON public.event_reports(gravita);

-- Politiche di sicurezza RLS
ALTER TABLE public.event_reports ENABLE ROW LEVEL SECURITY;

-- Politica: chiunque può leggere le segnalazioni
CREATE POLICY "Tutti possono leggere le segnalazioni" 
ON public.event_reports FOR SELECT 
USING (true);

-- Politica: solo l'utente che ha creato la segnalazione può modificarla o eliminarla
CREATE POLICY "Gli utenti possono modificare le proprie segnalazioni" 
ON public.event_reports FOR UPDATE 
USING (auth.uid()::text = user_id);

CREATE POLICY "Gli utenti possono eliminare le proprie segnalazioni" 
ON public.event_reports FOR DELETE 
USING (auth.uid()::text = user_id);

-- Politica: chiunque può inserire nuove segnalazioni
CREATE POLICY "Tutti possono inserire segnalazioni" 
ON public.event_reports FOR INSERT 
WITH CHECK (true);

-- Modifica alla tabella chat_messages per supportare moderazione
ALTER TABLE IF EXISTS public.chat_messages 
ADD COLUMN IF NOT EXISTS is_moderated BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS moderation_level TEXT,
ADD COLUMN IF NOT EXISTS moderation_score FLOAT,
ADD COLUMN IF NOT EXISTS original_message TEXT;

-- Tabella per la moderazione della chat
CREATE TABLE IF NOT EXISTS public.chat_moderation (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    infraction_score FLOAT DEFAULT 0,
    infractions_count INTEGER DEFAULT 0,
    last_infraction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    restriction_level TEXT DEFAULT 'none',
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_chat_moderation_user_id ON public.chat_moderation(user_id);

-- Politiche per la tabella di moderazione
CREATE POLICY IF NOT EXISTS "Solo gli amministratori possono leggere moderazioni"
ON public.chat_moderation FOR SELECT
USING (auth.uid() IN (
  SELECT id FROM auth.users WHERE email LIKE '%@admin.sismaver.it'
));

CREATE POLICY IF NOT EXISTS "Solo gli amministratori possono inserire moderazioni"
ON public.chat_moderation FOR INSERT
WITH CHECK (auth.uid() IN (
  SELECT id FROM auth.users WHERE email LIKE '%@admin.sismaver.it'
));

CREATE POLICY IF NOT EXISTS "Solo gli amministratori possono aggiornare moderazioni"
ON public.chat_moderation FOR UPDATE
USING (auth.uid() IN (
  SELECT id FROM auth.users WHERE email LIKE '%@admin.sismaver.it'
));