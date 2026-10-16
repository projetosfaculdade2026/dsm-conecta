# Passo a passo: do zero até a entrega

## 0. O que instalar (leve)
| Ferramenta | Para quê | Download |
|---|---|---|
| Git | versionamento | git-scm.com |
| Docker Desktop | broker + banco + serviços (um comando) | docker.com |
| Python 3.12 | só se quiser rodar testes fora do Docker | python.org |
| Flutter SDK | app (web/desktop/Android) | flutter.dev |
| VS Code | editor | code.visualstudio.com |

> Para **navegador e desktop** você não precisa de Android Studio. Só instale se quiser emulador Android.

## 1. Preparar o repositório (Iteração 0 e 1)
```bash
cd dsm-conecta
git init && git add . && git commit -m "chore: estrutura inicial do projeto"
git branch -M main
# crie o repositório no GitHub e:
git remote add origin https://github.com/SEU_USUARIO/dsm-conecta.git
git push -u origin main
```
No GitHub: **Settings → Branches → Add rule** em `main`: *Require a pull request before merging*,
*Require approvals (1)* e *Require status checks to pass* (marque `backend` e `client`). Isso cumpre
"ramo principal protegido" e "CI bloqueando incorporação".

## 2. Subir o ambiente e verificar (Iteração 0)
```bash
cp .env.example .env        # edite as senhas
docker compose up --build
```
Verificações:
1. http://localhost:8000/docs abre o Swagger.
2. `docker compose logs -f ingest` mostra `mqtt_conectado`.
3. `docker compose logs -f totem` mostra `totem online`.
4. Em 10 s o log do `ingest` mostra `stats` com `gravadas` crescendo (mensagens do totem).

## 3. Evidência de TDD (Iteração 1) — o histórico do Git precisa mostrar teste ANTES do código
Faça o ciclo **de verdade** a cada tarefa nova: escreva o teste, rode e veja **falhar** (vermelho), só então implemente. O histórico do Git
é a evidência; não monte commits depois só para parecer TDD. Exemplo com a presença por localização (`rules.py`):
```bash
git checkout -b feat/T01-regras-presenca
# 1) commit só do teste (ele falha porque app/rules.py não existe/está vazio)
git add backend/tests/test_rules.py && git commit -m "test: presença por localização dentro e fora do raio (red)"
# 2) commit da implementação
git add backend/app/rules.py && git commit -m "feat: presença por localização com raio de 150 m (green)"
# 3) refatorações
git commit -am "refactor: extrai haversine"
git push -u origin feat/T01-regras-presenca   # abra o Pull Request; peça revisão a colega de outra equipe
```
Repita para cada item novo, um branch e um PR por tarefa: presença única (`test_api.py` + `api.py` + `db/01_schema.sql`), janela configurável
(`test_analytics.py` + `analytics.py`), dados abertos (`test_opendata.py` + `opendata.py`). O código destes itens já está no projeto: para
registrar o ciclo, **tire a implementação do commit** (por exemplo `git stash` ou `git rm --cached` do arquivo), commite só o teste, confirme que falha e
depois commite a implementação. Para módulos que você não vai mexer mais, deixe como está e explique isso na avaliação. Commits pequenos e descritivos, um PR por tarefa,
revisão cruzada — isso é o que a rubrica (4.3 e 4.4) avalia.

## 4. Demonstração de cada iteração
| Iteração | O que mostrar | Comando / evidência |
|---|---|---|
| 0 | Visão, contratos, ambiente por comando único | `docs/DOCUMENTACAO.md`, `docker compose up` |
| 1 | PR bloqueado com CI vermelho, TDD no histórico | aba *Actions*, `git log --oneline` |
| 2 | Broker com login, 2 origens, LWT/retenção, consentimento | abaixo |
| 3 | Ingestão, 1M de registros, comparação de desempenho | `bench` abaixo |
| 4 | API documentada, WebSocket, alerta de anomalia | `/docs`, painel admin |
| 5 | App em 3 plataformas, offline, painel admin | `flutter run -d chrome/windows/...` |
| 6 | Ensaio de carga, painel público, dados abertos | `carga` abaixo |

### Iteração 2: assinar o broker ao vivo e mostrar LWT
```bash
docker compose exec mosquitto mosquitto_sub -u dsm -P dsm_pass -t "dsm/#" -v
```
Para demonstrar a **mensagem de última vontade**: `docker compose kill totem` → aparece
`dsm/prod/totem/status/sensor-01 offline` (retida). `docker compose up -d totem` → volta `online`.
Sem senha a conexão é recusada (mostra autenticação).

**ACL (permissões por usuário).** Com o usuário `leitor` (somente leitura) a assinatura funciona e a publicação é negada:
```bash
docker compose exec mosquitto mosquitto_sub -u leitor -P leitor_pass -t "dsm/#" -v           # funciona
docker compose exec mosquitto mosquitto_pub -u leitor -P leitor_pass -t dsm/prod/app/interacao/tela -m x   # negado pela ACL
docker compose exec mosquitto mosquitto_pub -u totem -P totem_pass -t dsm/prod/app/interacao/tela -m x      # negado: totem só escreve em totem/
```
O broker aceita a conexão e descarta a mensagem; o log do `mosquitto` (`docker compose logs mosquitto`) mostra a negação.

**Segunda origem no navegador.** Abra http://localhost:8000/simulador/ , **Conectar** (usuário `totem`, senha `totem_pass`) e use *+1 visitante*
ou *Modo automático*. Feche a aba e veja o status `offline` (última vontade). Consentimento: no app, recuse o aceite e mostre que
nada chega no `mosquitto_sub`.

### Iteração 3: carga de 1 milhão e comparativo
```bash
docker compose run --rm api python -m app.bench --n 1000000
```
Saída: tempos medianos em tabela plana × hypertable e bruto × agregação contínua. **Copie essa saída para o relatório.**

### Iteração 4: latência (< 3 s)
Abra o painel admin (login → aba *Tempo real*): o totem já gera eventos a cada 3 s e a contagem de eventos sobe na tela.
Para medir, publique um evento e cronometre até aparecer no painel (meta RNF05: ≤ 3 s):
```bash
docker compose exec mosquitto mosquitto_pub -u dsm -P dsm_pass -q 1 -t dsm/prod/app/interacao/tela \
  -m '{"event_id":"'$(cat /proc/sys/kernel/random/uuid)'","session_id":"teste-latencia-01","categoria":"interacao","origem":"app","ts":"'$(date -u +%FT%TZ)'","schema_version":1,"payload":{"tela":"latencia"}}'
```
Mensagem inválida (aparece como `mensagem_descartada` no log da ingestão): publique `-m 'lixo'`.

### Iteração 6: ensaio de carga (RNF06: 1000 clientes, 50 msg/s)
```bash
docker compose run --rm api python -m app.simulator carga --taxa 50 --total 3000 --sessoes 1000                # 1 conexão, 1000 sessões
docker compose run --rm api python -m app.simulator carga --taxa 50 --total 3000 --conexoes 1000               # 1000 conexões MQTT reais
```
(`carga.bat` roda os dois.) O segundo mostra também quantos clientes o próprio broker reportou conectados (`broker_reportou_conectados`).
Ao final imprime `enviadas=… gravadas=… perdidas=…` (meta: 0 perdidas em QoS 1). Registre o resultado.
Duplicatas/concorrência: `docker compose up -d --scale ingest=3` e repita; `perdidas` deve continuar 0 e
não deve haver registros duplicados (chave primária + `ON CONFLICT`).

### Iteração 6: dados abertos e dicionário
Sem login: http://localhost:8000/open-data/telemetria?format=csv e http://localhost:8000/open-data/dicionario . Para publicar no repositório,
rode `dados_abertos.bat` e faça commit da pasta `dados-abertos/`. Só aparecem grupos com 10 ou mais registros: com pouco uso o arquivo
sai só com o cabeçalho (isso é a regra RN08 funcionando). Para a demonstração, rode antes o `carga.bat` para gerar volume.

### Iteração 5: artefatos das 3 plataformas
```bash
build_artefatos.bat http://localhost:8000     # Windows;  ./build_artefatos.sh no Linux/Mac
```
Gera `dist/web`, `dist/windows` e `dist/dsm-conecta.apk` (Windows exige Visual Studio com C++; APK exige Android SDK; o que faltar é avisado
e os demais continuam). O build web também vai para `web/`, e a API o serve em http://localhost:8000 . Para celular físico passe o IP do PC no lugar de `localhost`.
No GitHub, os jobs do `ci.yml` geram os mesmos artefatos e os anexam na aba *Actions* (evidência "artefatos disponibilizados").

### Segurança: HTTPS na API (RNF12)
```bash
docker compose --profile tls up -d
flutter run -d chrome --dart-define=API_URL=https://localhost:8443
```
O navegador avisa sobre o certificado local na primeira vez (aceite). Em produção use um domínio real. O MQTT continua sem TLS.

## 5. Ação de divulgação e devolutiva
Leve o app em tablets/celulares ao campus/escola. Use o código da "Feira de Profissões" (seed: `DSM2026`) e a presença por localização na
"Visita à escola parceira". Depois: painel admin → Exportar → **Relatório para a escola parceira** (Markdown agregado, mín. 10 registros por
grupo; copie e entregue). Registre a ação em `docs/modelos/RELATORIO_ACAO_DIVULGACAO.md` e acompanhe tudo em `docs/CHECKLIST_RUBRICA.md`.

## 6. Problemas comuns
| Sintoma | Causa | Solução |
|---|---|---|
| `db` não sobe / tabelas ausentes / `presencas` não existe | volume antigo (de uma versão anterior) | `docker compose down -v` e suba de novo |
| Presença por localização "fora do raio" | o local do evento no `03_seed.sql` é o da Fatec Zona Sul | edite `lat`/`lon` do evento (painel admin → Conteúdo → campo extra) para o local real |
| Android: localização/internet não funcionam | permissões não aplicadas | rode `dart tool/preparar_plataformas.dart` dentro de `app/` e gere o APK de novo |
| App Android não conecta | `localhost` do emulador | já usa `10.0.2.2`; em celular real use `--dart-define=API_URL=…` |
| Web: erro de CORS | origem | API já libera `*` (restrinja em produção) |
| `flutter: command not found` | PATH | reinicie o terminal após instalar |
| Porta 1883/5432/8000 ocupada | outro serviço | altere o mapeamento em `docker-compose.yml` |
