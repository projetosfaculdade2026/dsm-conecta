# Backlog priorizado (modelo inicial)

Prioridade pela regra do Documento de Visão (seção 10): se faltar tempo, corta-se de baixo para cima, preservando
broker, ingestão, persistência, API e app em pelo menos duas plataformas. 

|#|Item|Requisitos|Iteração|Prioridade|Responsável|Situação|
|-|-|-|-|-|-|-|
|1|Contratos de mensagem e API|RF16, RNF02|0|Alta|Nayara Eufrasio dos Santos|Feito|
|2|Ambiente por `docker compose up`|RNF13|0|Alta|Nayara Eufrasio dos Santos|Feito|
|3|CI com lint e testes, branch protegida|RNF17, RNF18|1|Alta|Nayara Eufrasio dos Santos|Feito|
|4|Validação de mensagens (TDD)|RF16, RF17|1|Alta|Nayara Eufrasio dos Santos|Feito|
|5|Broker com autenticação e ACL|RNF12|2|Alta|Nayara Eufrasio dos Santos|Feito|
|6|Nó sensor simulado (Python e navegador)|RF15|2|Alta|Nayara Eufrasio dos Santos|Feito|
|7|Consentimento antes da coleta|RN01, RNF14|2|Alta|Nayara Eufrasio dos Santos|Feito|
|8|Ingestão concorrente e deduplicação|RF17, RNF07, RNF09|3|Alta|Nayara Eufrasio dos Santos|Feito|
|9|Série temporal, retenção e agregação|RF18, RNF08, RNF20|3|Alta|Nayara Eufrasio dos Santos|Feito|
|10|API de conteúdo e métricas, JWT|RF23, RF24|4|Alta|Nayara Eufrasio dos Santos|Feito|
|11|WebSocket e motor de análise|RF19–RF22|4|Alta|Nayara Eufrasio dos Santos|Feito|
|12|Telas públicas do app (quiz e design visual: Diulianne; demais telas e integração: Nayara)|RF01–RF09|5|Alta|Diulianne Carine Alves de Oliveira e Nayara Eufrasio dos Santos|Feito|
|13|Presença por código e por localização|RF10, RF11, RN03–RN05|5|Média|Nayara Eufrasio dos Santos|Feito|
|14|Painel administrativo|RF19, RF23|5|Média|Nayara Eufrasio dos Santos|Feito|
|15|Artefatos web, Android e Windows|RNF01|5|Média|Nayara Eufrasio dos Santos|Feito|
|16|Acessibilidade e design visual|RNF19|5|Média|Diulianne Carine Alves de Oliveira e Nayara Eufrasio dos Santos|Feito|
|17|Painel público e dados abertos|RF25, RNF03, RN08|6|Média|Nayara Eufrasio dos Santos|Feito|
|18|Ensaio de carga e relatório|RNF04–RNF06|6|Alta|Nayara Eufrasio dos Santos|Executar e registrar|
|19|Ação de divulgação e devolutiva|Seção 9|6|Alta|Diulianne Carine Alves de Oliveira|Planejar|
|20|Leitor de QR pela câmera|RF10|—|Baixa|—|Fora desta entrega|



