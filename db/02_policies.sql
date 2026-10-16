-- Agregação contínua por hora (visão materializada incremental)
CREATE MATERIALIZED VIEW telemetria_hora
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT time_bucket('1 hour', ts) AS bucket, categoria, count(*) AS total
FROM telemetria
GROUP BY 1, 2
WITH NO DATA;

SELECT add_continuous_aggregate_policy('telemetria_hora',
    start_offset => INTERVAL '3 days', end_offset => INTERVAL '1 hour', schedule_interval => INTERVAL '5 minutes');

-- Ciclo de vida (RNF20): compressão após 30 dias, remoção do bruto após 90 dias.
-- O agregado horário é mantido por 5 anos (última política).
ALTER TABLE telemetria SET (timescaledb.compress, timescaledb.compress_segmentby = 'categoria', timescaledb.compress_orderby = 'ts DESC');
SELECT add_compression_policy('telemetria', INTERVAL '30 days');
SELECT add_retention_policy('telemetria', INTERVAL '90 days');
SELECT add_retention_policy('telemetria_hora', INTERVAL '5 years');
