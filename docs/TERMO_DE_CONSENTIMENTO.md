# Termo de Consentimento para Coleta de Dados de Uso — DSM Conecta

Versão 1.0 · Curso Superior de Tecnologia em Desenvolvimento de Software Multiplataforma · Fatec Zona Sul · 2026/2

> Este é o texto exibido no aplicativo antes de qualquer coleta (RN01, RNF14) e publicado no repositório conforme a
> seção 11 do Documento de Visão. O mesmo texto está em `app/lib/consent_text.dart`; um teste automatizado
> (`backend/tests/test_projeto.py`) confere que os dois são idênticos.

## Texto do termo

Quem somos: o DSM Conecta é um aplicativo de divulgação do curso superior de tecnologia em Desenvolvimento de Software Multiplataforma da Fatec Zona Sul, desenvolvido pelos estudantes da disciplina de Laboratório de Desenvolvimento de Software Multiplataforma.

Para que usamos os dados: medir o alcance das ações de divulgação do curso e entender quais conteúdos despertam interesse. Os dados não são usados em qualquer decisão sobre você, e o questionário de afinidade é apenas orientativo, sem efeito sobre processo seletivo.

O que podemos registrar: as telas que você abre, as respostas do questionário de afinidade, a presença em eventos de divulgação e, somente se você pedir, leituras de sensores do aparelho e a sua localização para confirmar presença em um evento.

Como identificamos você: por um código aleatório gerado no seu aparelho. Não pedimos nome, e-mail, telefone, CPF nem qualquer outro dado pessoal, e a sua localização exata não é armazenada.

Base legal: o seu consentimento, conforme a Lei nº 13.709/2018 (LGPD). Nenhum dado é coletado antes do seu aceite.

Por quanto tempo guardamos: os dados brutos ficam por 90 dias e depois são removidos; somente contagens agregadas e anonimizadas ficam por até 5 anos.

Com quem compartilhamos: apenas resultados agregados, em grupos de no mínimo 10 registros, no painel público, nos dados abertos e no relatório entregue à escola parceira. Não é possível identificar uma pessoa por esses resultados.

Seus direitos: você pode consultar o histórico das suas interações, revogar o consentimento a qualquer momento e excluir os dados da sua sessão na tela Privacidade e meus dados. Ao excluir, o código aleatório é descartado.

Dúvidas: fale com a coordenação do curso pelo canal Falar com a coordenação, na aba Curso, em Dúvidas.

## Como o aplicativo aplica este termo

| Compromisso do termo | Onde está implementado |
|---|---|
| Nenhuma coleta antes do aceite (RN01) | `Telemetry.track` descarta o evento sem consentimento; teste `consent_test.dart` |
| Código aleatório, sem dado pessoal (RN02, RNF15) | `Telemetry.setConsent` gera um UUID v4 local |
| Consentimento revogável | Chave em *Privacidade e meus dados* (`privacy.dart`) |
| Consultar o histórico (RF12) | `GET /sessions/{id}/history` |
| Excluir os dados e descartar o código (RF12, RN02) | `DELETE /sessions/{id}`; também apaga as presenças da sessão |
| Posição exata não é armazenada | A API remove `lat` e `lon` antes de publicar a presença (`api.py`) |
| Retenção de 90 dias (brutos) e 5 anos (agregados) | `db/02_policies.sql` (RNF20) |
| Só agregados com no mínimo 10 registros (RN08) | `rules.mascarar_grupo`, painel público, dados abertos e relatório |

## Contato

Coordenação do curso DSM — **[PREENCHER: e-mail institucional da coordenação]**.
