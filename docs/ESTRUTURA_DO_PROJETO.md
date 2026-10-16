# O que existe no projeto

## Visão em uma frase
O app (Flutter) envia eventos de uso para a API; a API publica no broker MQTT; a ingestão grava no banco de série temporal;
a API analisa o fluxo em tempo real e mostra no painel. Um totem simulado também publica no broker.

## Árvore de arquivos
```
dsm-conecta/
├── iniciar.bat / parar.bat / app.bat / app_desktop.bat / testes.bat / benchmark.bat / carga.bat / dados_abertos.bat / build_artefatos.bat   (atalhos Windows; build_artefatos.sh no Linux/Mac)
├── docker-compose.yml        sobe tudo com 1 comando (broker, banco, ingestão, API, totem; proxy TLS opcional)
├── .env.example              modelo de variáveis/segredos (copiar para .env se quiser trocar senhas)
├── .github/workflows/ci.yml  pipeline de integração contínua (lint + testes + cobertura)
├── mosquitto/                mosquitto.conf (1883 MQTT, 9001 WebSocket, senha obrigatória) e acl (permissões por usuário)
├── proxy/Caddyfile           TLS opcional para a API (https://localhost:8443)
├── simulador-web/index.html  totem simulado que roda no navegador (http://localhost:8000/simulador/)
├── db/                       01_schema.sql (tabelas, presencas, hypertable, agregação), 02_policies.sql (retenção), 03_seed.sql (conteúdo)
├── backend/                  Python
│   ├── Dockerfile, requirements*.txt, pytest.ini, ruff.toml, .coveragerc
│   ├── app/
│   │   ├── config.py         lê variáveis de ambiente
│   │   ├── schema.py         contrato das mensagens (validação, tópicos, versão do esquema)
│   │   ├── dedup.py          deduplicação em memória (cache LRU)
│   │   ├── rules.py          regras de negócio puras: janela de presença (RN03), raio 150 m (RN04), mínimo 10 (RN08)
│   │   ├── opendata.py       dados abertos, dicionário e relatório para a escola (funções puras)
│   │   ├── analytics.py      janela deslizante, média móvel, detecção de anomalia (z-score), motor em tempo real
│   │   ├── auth.py           login e token JWT
│   │   ├── db.py             conexão e gravação em lote (ON CONFLICT DO NOTHING)
│   │   ├── ingest.py         serviço de ingestão assíncrona (assina broker > valida > deduplica > grava)
│   │   ├── api.py            API REST + WebSocket + painel público + dados abertos + exportação + configuração
│   │   ├── simulator.py      totem simulado (com última vontade) e gerador de carga (inclui 1000 conexões reais)
│   │   └── bench.py          1 milhão de registros e comparativo de desempenho
│   └── tests/                cerca de 100 casos de teste automatizados
├── app/                      Flutter (Android, web, desktop)
│   ├── pubspec.yaml          dependências
│   ├── lib/main.dart         navegação, tema e escala de fonte
│   ├── lib/a11y.dart         contraste (WCAG) e preferência de tamanho de fonte
│   ├── lib/consent_text.dart texto do termo de consentimento
│   ├── lib/localizacao.dart  posição do aparelho (presença por localização)
│   ├── tool/                 preparar_plataformas.dart (permissões do Android)
│   ├── lib/pages.dart        Início, Curso (matriz/projetos/depoimentos/dúvidas), Eventos, Quiz, Painel público
│   ├── lib/privacy.dart      consentimento, histórico, exclusão de dados, leitura de sensor
│   ├── lib/admin.dart        login, painel em tempo real, gestão de conteúdo, exportação
│   ├── lib/telemetry.dart    envio de eventos, sessão aleatória, fila offline
│   ├── lib/api.dart          cliente HTTP, cache local, URL da API
│   ├── lib/quiz_logic.dart   cálculo do perfil do quiz
│   └── test/                 quiz_test, a11y_test, consent_test
└── docs/                     GUIA_WINDOWS, PASSO_A_PASSO, DOCUMENTACAO, CHECKLIST_RUBRICA, TERMO_DE_CONSENTIMENTO,
                              DICIONARIO_DE_DADOS, ESTRUTURA_DO_PROJETO, modelos/ (backlog, ata, relatório da ação)
```

## Serviços que rodam no Docker
| Serviço | Porta | Função |
|---|---|---|
| `mosquitto` | 1883 (MQTT), 9001 (WebSocket) | broker de mensagens com senha e ACL |
| `db` | 5432 | PostgreSQL + TimescaleDB |
| `ingest` | – | consome do broker e grava no banco |
| `api` | 8000 | REST, WebSocket, Swagger em `/docs` |
| `totem` | – | nó sensor simulado: contagem de visitantes a cada 3 s |
| `proxy` (perfil `tls`) | 8443 | HTTPS para a API: `docker compose --profile tls up -d` |

## Como cada requisito da rubrica é atendido
| Critério da rubrica | Onde está |
|---|---|
| Ambiente por comando único (It. 0) | `docker-compose.yml`, `iniciar.bat` |
| Contratos de interface (It. 0) | `schema.py`, `/docs` (OpenAPI), `DOCUMENTACAO.md` seção 3 |
| Fluxo de versionamento e CI (It. 1) | `ci.yml`, `PASSO_A_PASSO.md` seções 1 e 3 |
| Testes antes do código (It. 1) | roteiro de commits em `PASSO_A_PASSO.md` seção 3 |
| Broker autenticado com ACL, QoS, retenção, última vontade (It. 2) | `mosquitto/`, `simulator.py` (`totem`), `simulador-web/` |
| Duas origens de dados + consentimento (It. 2) | app + totem; `telemetry.dart` |
| Ingestão com validação, deduplicação, concorrência (It. 3) | `ingest.py`, `schema.py`, `dedup.py` |
| Modelo de série temporal, partição, retenção (It. 3) | `db/01_schema.sql`, `db/02_policies.sql` |
| Carga de 1M e comparativo (It. 3) | `benchmark.bat` / `bench.py` |
| Motor de análise e anomalia (It. 4) | `analytics.py` + testes |
| API documentada e autenticada, tempo real (It. 4) | `api.py`, `auth.py`, `/docs`, `/ws/live` |
| App multiplataforma, offline, painel admin (It. 5) | `app/lib/*` |
| Ensaio de carga sem perda (It. 6) | `carga.bat` / `simulator.py carga` |
| Painel público e dados abertos (It. 6) | `/metrics/public`, `PainelPage`, `/open-data/*`, `DICIONARIO_DE_DADOS.md`, `dados_abertos.bat` |
| Termo de consentimento publicado (seção 11) | `docs/TERMO_DE_CONSENTIMENTO.md`, `consent_text.dart` |
| Artefatos das 3 plataformas (It. 5) | `build_artefatos.bat`, jobs do `ci.yml` |
| Privacidade e anonimização (It. 6) | `privacy.dart`, `rules.py`, `DOCUMENTACAO.md` seção 8 |

## Fluxo de um evento (para explicar na apresentação)
1. Usuário abre uma tela no app. Se aceitou o consentimento, `telemetry.dart` cria o evento (UUID + sessão aleatória) e coloca na fila local.
2. A fila envia `POST /events`. A API valida o contrato, aplica regras (janela, raio de 150 m, presença única) e **publica no tópico** `dsm/prod/app/interacao/tela` (QoS 1).
3. O **broker** entrega a todos os assinantes.
4. A **ingestão** valida de novo, descarta duplicadas/malformadas (log JSON) e grava em lotes no TimescaleDB.
5. O **motor de análise** (dentro da API) atualiza janelas, ranking e z-score e envia por **WebSocket** ao painel admin a cada 0,5 s.
6. Sem rede, o app guarda o evento localmente e reenvia depois.

## Limitações conhecidas (diga na apresentação)
Leitura de QR pela câmera (RF10: a presença usa o código que o QR contém, digitado) e sensor de luminosidade (RF14) não foram incluídos;
o app publica via API e não direto no broker (decisão D1); TLS só no acesso à API (proxy opcional), não no MQTT; docker-compose e Flutter
foram escritos e revisados, mas não executados no ambiente de desenvolvimento deste pacote, então podem exigir pequenos ajustes.
