# Checklist da rubrica por iteração

Legenda: ✔ pronto · ● feito, falta juntar a evidência (print, link ou saída do comando) · ○ ainda falta fazer (depende da equipe, não é código).

## Critérios transversais (todas as iterações)
| Critério (peso) | O que o projeto já tem | O que ainda falta |
|---|---|---|
| Escopo (25%) | ✔ Todos os RF/RNF estão na seção 9 do `DOCUMENTACAO.md` | ○ Demonstrar ao vivo e anotar por escrito o que ficou de fora |
| Qualidade técnica (25%) | ✔ Camadas separadas (regras, API, ingestão), contratos validados, tratamento de erro e de falta de rede | — |
| Testes (15%) | ✔ Mais de 100 testes no back-end (104 no início, 111 depois dos PRs #1 e #2), CI exigindo cobertura mínima de 70% (hoje 83%) e testes do app. O teste veio antes do código nos PRs #1 e #2 | — |
| Controle de versão (15%) | ✔ CI com lint e testes, branch `main` protegida e dois PRs aprovados pela Diulianne | ○ PR revisado por outra equipe (dúvida enviada ao professor) e tags |
| Documentação (10%) | ✔ `DOCUMENTACAO.md`, termo, dicionário e guias | ○ Outra equipe executar o roteiro e anotar o resultado |
| Colaboração (10%) | ● Backlog com responsáveis, ata de planejamento (25/08) e ata de revisão dos PRs | ○ Novas atas, só de reuniões que tiverem registro |

## Iteração 0: iniciação e arquitetura
| Entregável / critério | Situação | Evidência |
|---|---|---|
| Documento de visão e backlog priorizado | ✔ Backlog com responsáveis em `docs/modelos/BACKLOG.md` | Print do BACKLOG.md no repositório |
| Esquema de mensagens e especificação da API | ✔ seções 3 e 5 do `DOCUMENTACAO.md`, OpenAPI em `/docs` | — |
| Ambiente por comando único | ✔ `docker compose up --build` | Mostrar funcionando também no computador da Diulianne |
| Ata das reuniões com a coordenação | ○ Ainda não temos ata de reunião com a coordenação. A ata 1 é de planejamento entre a dupla | Modelo pronto em `docs/modelos/ATA_MODELO.md`. Falta registrar a reunião quando acontecer |

## Iteração 1: fundação de qualidade
| Entregável | Situação | Evidência |
|---|---|---|
| Fluxo de versionamento, `main` protegida | ✔ Exige PR, 1 aprovação e os checks `backend` e `client` | Print das regras do GitHub |
| CI com análise estática e testes | ✔ `.github/workflows/ci.yml` | Prints da aba *Actions* |
| Testes escritos **antes** do código | ✔ PRs #1 e #2, cada um com o commit `test:` (CI vermelho) antes do `feat:` (CI verde) | `git log --oneline` e prints do Actions |

## Iteração 2: mensageria e captura
| Entregável / critério | Situação | Evidência |
|---|---|---|
| Broker com autenticação | ✔ Senha e **ACL por usuário** (`mosquitto/acl`) | Prints do teste com os usuários `leitor` e `totem` |
| QoS 1, retenção e última vontade | ✔ | Print do totem derrubado e do status `offline` |
| Duas origens de dados | ✔ App (via API e MQTT) e totem (Python e **navegador**) | `/simulador/` |
| Leitura de sensores com consentimento | ✔ Acelerômetro e localização aproximada | Demonstração no app |
| Consentimento antes de qualquer coleta | ✔ | `consent_test.dart` e prints com o consentimento ligado e desligado |

## Iteração 3: ingestão e armazenamento
| Entregável | Situação | Evidência |
|---|---|---|
| Ingestão assíncrona, validação, deduplicação | ✔ | `docker compose logs ingest` |
| Série temporal particionada, retenção | ✔ `db/01_schema.sql`, `db/02_policies.sql` | — |
| Carga de 1 milhão e comparativo | ✔ Inserção em 137,5 s. As últimas 24 h levam 9,2 ms na hypertable contra 53,2 ms na tabela plana | seção 9.1 do `DOCUMENTACAO.md` e print do `benchmark.bat` |

## Iteração 4: API e análise em tempo real
| Entregável | Situação | Evidência |
|---|---|---|
| API documentada e autenticada | ✔ `/docs`, JWT | Print do Swagger |
| WebSocket | ✔ `/ws/live` | Painel admin |
| Janela, média móvel, anomalia | ✔ Com **janela configurável (RF20)** | `test_analytics.py` |
| Latência de até 3 s | ✔ 5 medições manuais entre 0,59 s e 2,63 s, média de 1,59 s | seção 9.1 do `DOCUMENTACAO.md` e prints do simulador |

## Iteração 5: aplicações multiplataforma
| Entregável | Situação | Evidência |
|---|---|---|
| App nas 3 plataformas, base única | ✔ Código único, com build pelo CI | Jobs de CI |
| Artefatos de instalação | ✔ O CI gera web, APK e Windows | Lista de *Artifacts* no Actions |
| Painel admin com gestão de conteúdo | ✔ | Demonstração |
| Offline e erro de rede | ✔ Cache e fila local | Demonstração em modo avião |
| Acessibilidade | ✔ Contraste ≥ 4,5:1 (testado), fonte ajustável até 200% e rótulos | `a11y_test.dart` |
| Testes do app | ✔ `app/test` | `flutter test` |

## Iteração 6: escala, entrega e ação social
| Entregável | Situação | Evidência |
|---|---|---|
| Ensaio de carga sem perda | ✔ 1000 conexões: 3000 enviadas, 3000 gravadas, `perdidas=0` | seção 9.1 do `DOCUMENTACAO.md` e print do `RESULTADO` |
| Painel público e dados abertos com dicionário | ✔ `/metrics/public`, `/open-data/*`, `DICIONARIO_DE_DADOS.md` | `dados_abertos.bat` e commit da pasta |
| Termo de consentimento publicado | ● `TERMO_DE_CONSENTIMENTO.md` pronto. Falta o e-mail da coordenação | Resposta do professor |
| Ação de divulgação e devolutiva | ○ O relatório agregado já sai do app (Exportar) | `docs/modelos/RELATORIO_ACAO_DIVULGACAO.md` e fotos |
| Documentação final e apresentação | ○ Faltam o relatório da ação de divulgação e a apresentação | `docs/modelos/` |
