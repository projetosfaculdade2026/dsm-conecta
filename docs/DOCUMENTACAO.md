# DSM Conecta — Documentação técnica

Versão 1.1 · Disciplina: Laboratório de Desenvolvimento de Software Multiplataforma · 2026/2
> Preencha nomes da equipe, datas, prints e links de PR onde indicado por **[PREENCHER]**.

## 1. Visão geral
Aplicativo de divulgação do curso DSM para Android, navegador e desktop (Flutter, base única), integrado a uma
arquitetura orientada a eventos que coleta telemetria de uso e a analisa em tempo real. Escopo e exclusões seguem o
Documento de Visão (sem iOS, sem lojas, sem hardware, sem cadastro pessoal).

## 2. Arquitetura
| Camada | Componente | Tecnologia | Código |
|---|---|---|---|
| Borda | Aplicativo cliente | Flutter | `app/lib` |
| Borda | Nó sensor simulado (totem) | Python + MQTT, e página no **navegador** (MQTT sobre WebSocket) | `backend/app/simulator.py`, `simulador-web/index.html` |
| Transporte | Broker | Eclipse Mosquitto (senha + **ACL por usuário**, WebSocket 9001) | `mosquitto/`, `docker-compose.yml` |
| Processamento | Ingestão assíncrona | Python `asyncio` + `aiomqtt` + `asyncpg` | `backend/app/ingest.py` |
| Processamento | API + motor de análise | FastAPI, WebSocket | `backend/app/api.py`, `analytics.py` |
| Persistência | Série temporal + conteúdo + presenças | PostgreSQL + TimescaleDB | `db/01_schema.sql`, `02_policies.sql`, `03_seed.sql` |
| Borda de segurança (opcional) | Proxy TLS | Caddy (`docker compose --profile tls up -d`) | `proxy/Caddyfile` |

Fluxo: o app envia o evento por HTTP `POST /events`; a API valida, aplica regras de negócio e **publica no broker (QoS 1)**;
a ingestão e o motor de análise assinam o broker de forma independente (publicação/assinatura → desacoplamento).
O nó sensor (Python ou navegador) publica direto no broker, com usuário próprio restrito por ACL.

**Decisão D2 (ACL no broker).** O usuário `dsm` (serviços internos) tem acesso total; `totem` só escreve em
`dsm/+/totem/sensor/+` e no seu status; `leitor` só lê. Assim, um nó comprometido não consegue forjar eventos do app.

**Decisão D1 (gateway HTTP→MQTT).** O Flutter web não abre TCP MQTT e o cliente MQTT por WebSocket varia entre
plataformas; com o gateway, as 3 plataformas usam o mesmo código e o transporte entre componentes continua MQTT.
Trade-off: o app depende da API para publicar (mitigado pela fila local, RNF11). **Desvio assumido em relação ao RF13**, que fala em
publicar direto no broker: o contrato (tópicos, JSON, QoS 1) é o mesmo, e a API é o ponto onde as regras RN03/RN04/RN05 são aplicadas
antes de a mensagem entrar no broker. Justifique assim na apresentação.

## 3. Contrato de mensagens (congelado ao fim da Iteração 0)
Tópico: `dsm/<ambiente>/<origem>/<categoria>/<identificador>`

| Tópico | Origem | Payload obrigatório |
|---|---|---|
| `dsm/prod/app/interacao/tela` | app | `tela` |
| `dsm/prod/app/quiz/resposta` | app | `questao`, `perfil` |
| `dsm/prod/app/presenca/evento` | app | `evento_id` |
| `dsm/prod/app/sensor/dispositivo` | app | `tipo`, `valor` |
| `dsm/prod/totem/sensor/contagem` | totem | `contagem` (inteiro ≥ 0) |
| `dsm/prod/totem/status/sensor-01` | totem | `online` / `offline` (retida; LWT) |

Envelope JSON: `event_id` (UUID), `session_id` (aleatório, 8–64), `categoria`, `origem`, `ts` (ISO-8601 com fuso),
`schema_version` (obrigatória; hoje `1`), `payload`. Implementação: `backend/app/schema.py`.
Evolução: nova versão entra em `SCHEMA_VERSIONS` sem quebrar produtores antigos (*openness*).

Uso do protocolo: **QoS 1** em todas as publicações e na assinatura da ingestão; **retenção** e **última vontade** no
status do totem; **curinga** `dsm/+/+/+/+` na assinatura; autenticação por usuário/senha no broker.

## 4. Modelo de dados (`db/01_schema.sql`, `02_policies.sql`, `03_seed.sql`)
- Relacional: `content` (conteúdo e eventos; `approved` implementa RN07), `mensagens` (dúvidas à coordenação), `presencas`
  (**RN05**: chave primária `(evento_id, session_id)`, portanto no máximo uma presença por sessão e evento, mesmo com requisições simultâneas).
- Série temporal: `telemetria`, *hypertable* por dia, PK `(event_id, ts)` (deduplicação), índices `(categoria, ts DESC)` e `session_id`.
- Agregação contínua: `telemetria_hora` (atualizada incrementalmente; é a fonte dos dados abertos).
- Ciclo de vida: compressão após 30 dias, remoção dos brutos após 90 dias (RNF20).

## 5. Interface de programação (OpenAPI em `/docs`)
Pública: `GET /content`, `GET /quiz`, `POST /events`, `POST /messages`, `GET /sessions/{id}/history`,
`DELETE /sessions/{id}`, `GET /metrics/public`, `GET /health`, `POST /auth/login`, e os **dados abertos** (RNF03):
`GET /open-data/telemetria?format=csv|json` e `GET /open-data/dicionario`.
Autenticada (JWT Bearer): `GET /admin/content`, `POST|PUT|DELETE /content`, `GET /metrics/realtime`,
`GET /metrics/summary`, `GET /export?format=csv|json`, `GET /admin/messages`, `GET|PUT /admin/config` (janela do ranking, RF20),
`GET /admin/report` (devolutiva para a escola), `WS /ws/live?token=…`.
Erros: 401 (auth), 404, 409 (presença inválida: fora da janela, fora do raio de 150 m, código errado ou **já registrada**), 422 (contrato violado), 503 (broker indisponível).

**Presença (RF10, RF11, RN03–RN05).** `POST /events` com categoria `presenca` aceita `codigo` (equivalente ao QR) **ou** `lat`/`lon`
(proximidade). A API confere a janela de horário, o código ou o raio de 150 m e grava em `presencas`; só então publica. A posição exata
e o código **não** vão para o broker (o payload publicado leva só `metodo`). Se o broker falhar, a linha de `presencas` é desfeita para
permitir nova tentativa.

## 6. Motor de análise (`analytics.py`)
Janela deslizante **configurável de 10 s a 1 h, padrão 60 s** (RF20: `PUT /admin/config` ou seletor no painel) para visitantes ativos e ranking, buckets de 5 s, média móvel (n=3) e detecção de
desvio: z-score do último bucket concluído contra os 12 anteriores (limiar 3; piso de desvio 1; mínimo de 5 amostras).
Presença única por sessão/evento (RN05) no painel e, agora, também no servidor (`presencas`). Testado com dados controlados (`tests/test_analytics.py`).

## 7. Concorrência, escalabilidade e transparência (Seção 7 do Documento de Visão)
- **Concorrência/contrapressão:** fila `asyncio.Queue(5000)`; quando o banco atrasa, a fila enche e a leitura do broker é freada. Gravação em lotes de até 500.
- **Múltiplas instâncias (RNF07):** `docker compose up -d --scale ingest=3`; `ON CONFLICT DO NOTHING` impede duplicata entre instâncias.
- **Escalabilidade:** particionamento temporal, agregações contínuas, ingestão replicável; comprovada por `bench` e `carga`.
- **Transparência:** o app conhece apenas `API_URL`; fila local e cache offline absorvem falhas.
- **Descarte:** mensagens malformadas/duplicadas são registradas em log JSON (`mensagem_descartada`).

## 8. Privacidade (LGPD)
Consentimento explícito antes de qualquer coleta (RN01, dialog inicial, revogável); `session_id` aleatório local, sem dado
pessoal (RN02, RNF15); histórico e exclusão da sessão no app (RF12); painel público só com grupos ≥ 10 registros (RN08, RNF16);
credenciais em variáveis de ambiente (RNF13); código secreto do evento não é exposto na API pública; posição exata não é armazenada.
O texto completo está em `docs/TERMO_DE_CONSENTIMENTO.md` e é o mesmo exibido no app (teste automatizado confere).

## 9. Rastreabilidade de requisitos
✔ implementado · ◐ implementado, falta você medir/registrar · ✘ não implementado (explicado)

| Requisito | Situação | Onde |
|---|---|---|
| RF01–RF05 | ✔ | seed em `db/03_seed.sql`; telas `pages.dart` |
| RF06 | ✔ | FAQ + `POST /messages` |
| RF07 | ✔ compartilhamento nativo (`share_plus`); onde a plataforma não oferece, copia o texto | `pages.dart` (`compartilhar`) |
| RF08 | ✔ cache local | `api.dart` |
| RF09 | ✔ | `QuizPage`, `GET /quiz` |
| RF10 | ◐ presença por **código** do evento (o QR contém esse código); **leitura pela câmera não foi incluída** | `EventosPage`, `rules.py` |
| RF11 | ✔ presença por localização, raio de 150 m | `localizacao.dart`, `telemetry.dart`, `rules.py` |
| RF12 | ✔ | `privacy.dart`, `/sessions` |
| RF13 | ◐ desvio D1: app → API → broker | seção 2 |
| RF14 | ◐ acelerômetro e localização aproximada; **luminosidade não** (sem suporte no pacote de sensores) | `telemetry.dart` |
| RF15 | ✔ totem Python e totem no navegador | `simulator.py`, `simulador-web/` |
| RF16–RF18 | ✔ | `schema.py`, `ingest.py`, `db.py` |
| RF19, RF21, RF22 | ✔ | `analytics.py`, `admin.dart` |
| RF20 | ✔ janela configurável | `analytics.py`, `PUT /admin/config`, seletor no painel |
| RF23 | ✔ | `/content`, `ContentAdminTab` |
| RF24 | ✔ (admin) | `/export`, `ExportTab` |
| RF25 | ✔ | `/metrics/public`, `PainelPage` |
| RNF01 | ✔ base única; artefatos por `build_artefatos.bat` e CI | `.github/workflows/ci.yml` |
| RNF02 | ✔ OpenAPI 3, MQTT 3.1.1 | `/docs` |
| RNF03 | ✔ dados abertos em CSV/JSON + dicionário | `/open-data/*`, `DICIONARIO_DE_DADOS.md`, `dados_abertos.bat` |
| RNF04, RNF05, RNF08 | ◐ medir e registrar | **[PREENCHER]** |
| RNF06 | ◐ `carga.bat` abre **1000 conexões MQTT reais** a 50 msg/s; registrar `perdidas=0` | **[PREENCHER]** |
| RNF07, 09, 11 | ✔ | seção 7 |
| RNF12 | ◐ JWT ✔; TLS no acesso administrativo via proxy opcional (`--profile tls`, https://localhost:8443). TLS no próprio MQTT **não** configurado | `proxy/Caddyfile` |
| RNF13–16 | ✔ | seção 8 |
| RNF17–18 | ✔ CI com `--cov-fail-under=70` e bloqueio por teste falhando (configure a branch protegida) | `ci.yml` |
| RNF19 | ✔ contraste ≥ 4,5:1 verificado por teste, fonte ajustável (85% a 200%) somada à do sistema, rótulos e dicas para leitores de tela | `a11y.dart`, `a11y_test.dart` |
| RNF20 | ✔ | `db/02_policies.sql` |
| RN01–RN08 | ✔ RN05 agora também no servidor | `rules.py`, `api.py`, `db/01_schema.sql` |

**O que continua fora (diga na apresentação):** leitura de QR pela câmera, sensor de luminosidade, TLS no MQTT, versão para iOS e lojas
(estas duas já são exclusões do Documento de Visão).

## 10. Testes
`backend/tests` (cerca de 100 casos): esquema, deduplicação, janelas e anomalia (inclui janela configurável), regras RN03/RN04/RN08
(código e localização), autenticação, API com dublês (presença única, raio, desfazer presença, configuração, dados abertos,
relatório), módulo de dados abertos e **coerência do repositório** (`test_projeto.py`: termo igual no app e no documento, ACL do
broker, apenas scripts SQL numerados, chave única de presenças). Rode `testes.bat` e registre o número exato e a cobertura (meta ≥ 70%).
Cliente (`app/test`): lógica do quiz, contraste e escala de fonte (`a11y_test.dart`), termo e RN01 (`consent_test.dart`).
**Limitação:** não há testes de widget com tela renderizada.

## 11. Registro do que foi feito em cada iteração  **[PREENCHER com datas, autores, links de PR]**
| It. | Entregas | Evidências |
|---|---|---|
| 0 | Documento de visão, contratos (seção 3), repositório, `docker compose up` | ata, demonstração |
| 1 | Fluxo de branches/PR, CI (`ci.yml`), testes de validação antes do código | histórico Git, Actions |
| 2 | Broker autenticado, publicação do app e do totem, LWT/retenção, consentimento | `mosquitto_sub`, demo |
| 3 | Ingestão assíncrona, hypertable, 1M de registros, comparativo | saída de `bench` |
| 4 | API documentada, WebSocket, motor de análise, alerta | `/docs`, painel |
| 5 | App Android/web/desktop, painel admin, tratamento offline | demo nos 3 ambientes |
| 6 | Ensaio de carga, painel público, dados abertos, ação de divulgação | saída de `carga`, fotos |

## 12. Dados abertos e dicionário (RNF03)
Conjunto público e sem login em `/open-data/telemetria` (CSV ou JSON), com dicionário em `/open-data/dicionario` e em
`docs/DICIONARIO_DE_DADOS.md`. Só agregados por hora e categoria, com no mínimo 10 registros por grupo (RN08). Para publicar uma cópia no
repositório, rode `dados_abertos.bat` e faça commit da pasta `dados-abertos/`.

## 12.1 Devolutiva para a escola parceira (seção 9 do Documento de Visão)
Área da coordenação → **Exportar** → *Relatório para a escola parceira* (Markdown agregado, também em `GET /admin/report`).
Modelos de ata, backlog e relatório da ação em `docs/modelos/`.

## 13. Riscos residuais
Senhas padrão do `.env.example` devem ser trocadas; CORS `*` e ausência de TLS só servem para desenvolvimento;
o compose e o app Flutter não foram executados no ambiente em que este pacote foi preparado — se algo falhar, veja `docker compose logs <serviço>` e envie a mensagem completa.
Se você já tinha subido uma versão anterior, rode `docker compose down -v` para recriar o banco com a tabela `presencas` e a ACL do broker.
