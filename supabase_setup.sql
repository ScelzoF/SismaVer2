-- Script SQL per configurare le tabelle di chat e segnalazioni su Supabase

-- Tabella per i messaggi della chat
CREATE TABLE public.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    nickname TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    regione TEXT NOT NULL,
    lat FLOAT,
    lon FLOAT,
    user_id TEXT,
    is_emergency BOOLEAN DEFAULT false,
    message_type TEXT DEFAULT 'standard'
);

-- Indici per migliorare le performance
CREATE INDEX idx_chat_messages_timestamp ON public.chat_messages(timestamp);
CREATE INDEX idx_chat_messages_regione ON public.chat_messages(regione);
CREATE INDEX idx_chat_messages_emergency ON public.chat_messages(is_emergency);

-- Tabella per le segnalazioni
CREATE TABLE public.segnalazioni (
    id BIGSERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,
    descrizione TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    latitudine FLOAT,
    longitudine FLOAT,
    regione TEXT
);

-- Politiche di sicurezza Row Level Security (RLS)
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.segnalazioni ENABLE ROW LEVEL SECURITY;

-- Politiche per chat_messages
CREATE POLICY "Tutti possono leggere i messaggi" 
ON public.chat_messages FOR SELECT USING (true);

CREATE POLICY "Gli utenti possono modificare i propri messaggi" 
ON public.chat_messages FOR UPDATE 
USING (auth.uid()::text = user_id);

CREATE POLICY "Gli utenti possono eliminare i propri messaggi" 
ON public.chat_messages FOR DELETE 
USING (auth.uid()::text = user_id);

CREATE POLICY "Tutti possono inserire messaggi" 
ON public.chat_messages FOR INSERT 
WITH CHECK (true);

-- Politiche per segnalazioni
CREATE POLICY "Tutti possono leggere le segnalazioni" 
ON public.segnalazioni FOR SELECT USING (true);

CREATE POLICY "Tutti possono inserire segnalazioni" 
ON public.segnalazioni FOR INSERT 
WITH CHECK (true);

-- Tabella per il log della pulizia chat
CREATE TABLE public.chat_cleanup_log (
    id SERIAL PRIMARY KEY,
    last_run TIMESTAMPTZ DEFAULT NOW()
);

-- Funzione per pulire messaggi vecchi
CREATE OR REPLACE FUNCTION cleanup_old_messages()
RETURNS void AS $$
BEGIN
    DELETE FROM public.chat_messages
    WHERE id IN (
        SELECT id FROM public.chat_messages
        ORDER BY timestamp DESC
        OFFSET 1000
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger per la pulizia automatica
CREATE OR REPLACE FUNCTION trigger_cleanup_check()
RETURNS TRIGGER AS $$
DECLARE
    last_cleanup TIMESTAMPTZ;
BEGIN
    SELECT MAX(last_run) INTO last_cleanup FROM public.chat_cleanup_log;
    IF last_cleanup IS NULL OR (NOW() - last_cleanup) > INTERVAL '24 hours' THEN
        PERFORM cleanup_old_messages();
        INSERT INTO public.chat_cleanup_log (last_run) VALUES (NOW());
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER chat_cleanup_trigger
AFTER INSERT ON public.chat_messages
FOR EACH ROW
EXECUTE FUNCTION trigger_cleanup_check();

-- Inserimento dati iniziali di esempio
INSERT INTO public.chat_messages (nickname, message, regione, is_emergency) VALUES
('Sistema', 'Benvenuti nella chat pubblica di SismaVer2! Utilizzate questo spazio per condividere informazioni e supportarvi a vicenda.', 'Lazio', false),
('InfoMeteo', 'Previsioni per oggi: sereno su tutta la penisola con temperature in aumento.', 'Lombardia', false),
('Protezione_Civile', 'Ricordiamo a tutti gli utenti di verificare i punti di raccolta nella propria area di residenza.', 'Campania', false);