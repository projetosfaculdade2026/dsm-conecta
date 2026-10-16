# Dicionário de dados abertos — DSM Conecta (RNF03)

Conjunto: **telemetria agregada por hora** · Licença: CC BY 4.0 · Formatos não proprietários: CSV e JSON.

Onde obter, sem login:

| Conteúdo | Endereço |
|---|---|
| Dados em CSV | `GET /open-data/telemetria?format=csv` |
| Dados em JSON | `GET /open-data/telemetria?format=json` |
| Este dicionário em JSON | `GET /open-data/dicionario` |
| Cópia publicada no repositório | pasta `dados-abertos/` (gerada por `dados_abertos.bat`) |

## Campos

| Campo | Tipo | Descrição | Exemplo |
|---|---|---|---|
| `hora` | texto, ISO-8601 em UTC | Início da hora a que a contagem se refere. | `2026-10-01T14:00:00+00:00` |
| `categoria` | texto | Tipo de evento: `interacao` (abertura de telas), `quiz` (respostas do questionário) ou `sensor` (leituras). | `interacao` |
| `total` | inteiro, no mínimo 10 | Quantidade de eventos da categoria naquela hora. | `42` |

## Regras de publicação

1. Só aparecem grupos (hora + categoria) com **no mínimo 10 registros** (RN08). Os demais são omitidos, não zerados.
2. Não há identificador de sessão, de dispositivo, localização nem qualquer dado pessoal (RNF15, RNF16).
3. A categoria `presenca` não é publicada neste conjunto, pois grupos pequenos poderiam identificar pessoas.
4. Os dados vêm da agregação contínua `telemetria_hora`, mantida por 5 anos (RNF20).
5. Implementação: `backend/app/opendata.py` (`preparar_publicacao`, `DICIONARIO`); testes em `backend/tests/test_opendata.py`.

## Observação sobre o painel público

O painel público do app (`GET /metrics/public`) usa as mesmas regras de agregação mínima e anonimização.
