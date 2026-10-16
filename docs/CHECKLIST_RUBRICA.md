# Checklist da rubrica por iteração

Legenda: ✔ pronto no código · ◐ pronto, falta você registrar a evidência · ✋ depende da equipe (não é código).
Onde estiver **[PREENCHER]**, cole o print, o link do PR ou a saída do comando.

## Critérios transversais (todas as iterações)
| Critério (peso) | O que o projeto já oferece | O que falta de você |
|---|---|---|
| Escopo (25%) | Todos os RF/RNF rastreados em `DOCUMENTACAO.md` §9 | Demonstrar ao vivo; replanejar por escrito o que ficar pendente ✋ |
| Qualidade técnica (25%) | Camadas separadas (regras puras, API, ingestão), contratos validados, tratamento de erro e de falta de rede ✔ | — |
| Testes (15%) | cerca de 100 casos de teste no back-end, CI exigindo cobertura ≥ 70%, testes do cliente ✔ (rode `testes.bat` e registre o número e a cobertura **[PREENCHER]**) | **Histórico Git com teste antes do código** ✋ (`PASSO_A_PASSO.md` §3) |
| Controle de versão (15%) | CI com lint e testes; jobs de artefatos ✔ | Branch protegida, PRs revisados por outra equipe, tags ✋ |
| Documentação (10%) | `DOCUMENTACAO.md`, termo, dicionário, guias ✔ | Outra equipe executar o roteiro e registrar ✋ |
| Colaboração (10%) | Modelos de backlog e ata em `docs/modelos/` | Atas, backlog atualizado, presença nos ritos ✋ |

## Iteração 0 — iniciação e arquitetura
| Entregável / critério | Situação | Evidência |
|---|---|---|
| Documento de visão e backlog priorizado | ◐ backlog inicial em `docs/modelos/BACKLOG.md` | Ajustar prioridades com a equipe |
| Esquema de mensagens e especificação da API | ✔ `DOCUMENTACAO.md` §3 e §5, OpenAPI em `/docs` | — |
| Ambiente por comando único | ✔ `docker compose up --build` | Demonstrar em todas as máquinas |
| Ata das reuniões com a coordenação | ✋ | Usar `docs/modelos/ATA_MODELO.md` |

## Iteração 1 — fundação de qualidade
| Entregável | Situação | Evidência |
|---|---|---|
| Fluxo de versionamento, main protegida | ✋ | Print das regras do GitHub |
| CI com análise estática e testes | ✔ `.github/workflows/ci.yml` | Prints da aba *Actions* |
| Testes do módulo de validação **escritos antes** | ✋ | `git log --oneline` mostrando `test:` antes de `feat:` |

## Iteração 2 — mensageria e captura
| Entregável / critério | Situação | Evidência |
|---|---|---|
| Broker com autenticação | ✔ senha + **ACL por usuário** (`mosquitto/acl`) | `PASSO_A_PASSO.md` §4 (negação ao publicar com `leitor`) |
| QoS 1, retenção e última vontade | ✔ | Demonstração `docker compose kill totem` |
| Duas origens de dados | ✔ app (via API→MQTT) e totem (Python e **navegador**) | `/simulador/` |
| Leitura de sensores com consentimento | ✔ acelerômetro e localização aproximada | Demonstração no app |
| Consentimento antes de qualquer coleta | ✔ | `consent_test.dart` |

## Iteração 3 — ingestão e armazenamento
| Entregável | Situação | Evidência |
|---|---|---|
| Ingestão assíncrona, validação, deduplicação | ✔ | `docker compose logs ingest` |
| Série temporal particionada, retenção | ✔ `db/01_schema.sql`, `db/02_policies.sql` | — |
| Carga de 1 milhão e comparativo | ◐ `benchmark.bat` | Colar a saída no relatório **[PREENCHER]** |

## Iteração 4 — API e análise em tempo real
| Entregável | Situação | Evidência |
|---|---|---|
| API documentada e autenticada | ✔ `/docs`, JWT | Print do Swagger |
| WebSocket | ✔ `/ws/live` | Painel admin |
| Janela, média móvel, anomalia | ✔ + **janela configurável (RF20)** | `test_analytics.py` |
| Latência ≤ 3 s | ◐ | Medir e registrar **[PREENCHER]** |

## Iteração 5 — aplicações multiplataforma
| Entregável | Situação | Evidência |
|---|---|---|
| App nas 3 plataformas, base única | ✔ código · ◐ build | `build_artefatos.bat` / jobs de CI |
| Artefatos de instalação | ✔ script e CI geram web, APK e Windows | Pasta `dist/` ou artefatos do Actions |
| Painel admin com gestão de conteúdo | ✔ | Demonstração |
| Offline e erro de rede | ✔ cache + fila local | Demonstração em modo avião |
| Acessibilidade | ✔ contraste ≥ 4,5:1 (testado), fonte ajustável até 200%, rótulos | `a11y_test.dart` |
| Testes do cliente | ✔ `app/test` | `flutter test` |

## Iteração 6 — escala, entrega e ação social
| Entregável | Situação | Evidência |
|---|---|---|
| Ensaio de carga sem perda | ◐ `carga.bat` (inclui **1000 conexões reais**) | Saída `RESULTADO … perdidas=0` **[PREENCHER]** |
| Painel público e dados abertos com dicionário | ✔ `/metrics/public`, `/open-data/*`, `DICIONARIO_DE_DADOS.md` | `dados_abertos.bat` e commit da pasta |
| Termo de consentimento publicado | ✔ `TERMO_DE_CONSENTIMENTO.md` | — |
| Ação de divulgação e devolutiva | ✋ relatório agregado pronto no app (Exportar) | `docs/modelos/RELATORIO_ACAO_DIVULGACAO.md`, fotos |
| Documentação final e apresentação | ◐ | Completar os **[PREENCHER]** |
