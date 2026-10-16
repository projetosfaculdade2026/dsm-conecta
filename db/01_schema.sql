-- DSM Conecta: esquema do banco (executado automaticamente na primeira subida do contêiner)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Dados relacionais convencionais
CREATE TABLE content (
    id       SERIAL PRIMARY KEY,
    kind     TEXT NOT NULL CHECK (kind IN ('apresentacao','disciplina','projeto','depoimento','evento','faq')),
    title    TEXT NOT NULL,
    body     TEXT NOT NULL DEFAULT '',
    extra    JSONB NOT NULL DEFAULT '{}',
    approved BOOLEAN NOT NULL DEFAULT FALSE       -- RN07: só aparece ao público após aprovação
);

CREATE TABLE mensagens (
    id        SERIAL PRIMARY KEY,
    nome      TEXT NOT NULL DEFAULT '',
    texto     TEXT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RN05: no máximo uma presença por sessão e por evento (garantido pelo banco, mesmo com requisições simultâneas)
CREATE TABLE presencas (
    evento_id INT         NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    session_id TEXT       NOT NULL,
    metodo     TEXT       NOT NULL CHECK (metodo IN ('codigo','localizacao')),
    criado_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (evento_id, session_id)
);

-- Série temporal: tabela particionada por tempo (chunks de 1 dia)
CREATE TABLE telemetria (
    event_id       UUID        NOT NULL,
    ts             TIMESTAMPTZ NOT NULL,
    session_id     TEXT        NOT NULL,
    categoria      TEXT        NOT NULL,
    origem         TEXT        NOT NULL,
    schema_version INT         NOT NULL,
    payload        JSONB       NOT NULL
);
SELECT create_hypertable('telemetria', 'ts', chunk_time_interval => INTERVAL '1 day');

-- Deduplicação entre instâncias da ingestão (RNF07): o banco é a última barreira
CREATE UNIQUE INDEX telemetria_event_uq ON telemetria (event_id, ts);
-- Índice composto categoria + instante (modelo de dados da seção 6.4)
CREATE INDEX telemetria_categoria_ts ON telemetria (categoria, ts DESC);
CREATE INDEX telemetria_sessao ON telemetria (session_id);
