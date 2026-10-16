# DSM Conecta

Aplicativo multiplataforma (Flutter) de divulgação do curso DSM + arquitetura distribuída de telemetria
(MQTT → ingestão assíncrona → TimescaleDB → API FastAPI/WebSocket → painéis).

```
app (Flutter) --HTTP--> API --MQTT QoS1--> Mosquitto <--MQTT-- nó sensor simulado (totem)
                                              |
                                  ingestão (asyncio, lote, dedup) --> TimescaleDB (hypertable + agregações)
                                              |
                                  API: motor de análise (janela, média móvel, z-score) --WebSocket--> painel admin
```

## Subir tudo (back-end)
Requisito: Docker Desktop (ou Docker Engine + Compose).

```bash
docker compose up --build
```
- API + Swagger: http://localhost:8000/docs  (login de teste: `admin` / `admin123`)
- Broker MQTT: `localhost:1883` (usuário `dsm`, senha `dsm_pass`; `totem` e `leitor` têm permissões restritas pela ACL)
- Totem simulado no navegador: http://localhost:8000/simulador/
- Dados abertos (sem login): http://localhost:8000/open-data/telemetria · dicionário em `/open-data/dicionario`
- HTTPS opcional: `docker compose --profile tls up -d` → https://localhost:8443

## Rodar o app (Flutter)
```bash
cd app
flutter create . --project-name dsm_conecta --platforms=web,android,windows   # gera as pastas de plataforma (uma vez)
rm test/widget_test.dart                            # (Windows: del test\widget_test.dart)
dart tool/preparar_plataformas.dart                 # permissões do Android (internet e localização)
flutter pub get
flutter run -d chrome          # navegador
flutter run -d windows         # desktop (ou linux/macos)
flutter run                    # Android (emulador usa 10.0.2.2 automaticamente)
```
Celular físico: `flutter run --dart-define=API_URL=http://IP_DO_SEU_PC:8000`.

## Testes
```bash
cd backend && pip install -r requirements-dev.txt && ruff check . && pytest --cov --cov-fail-under=70
cd app && flutter test
```
Artefatos das 3 plataformas: `build_artefatos.bat` (ou `./build_artefatos.sh`).

Guia completo: `docs/PASSO_A_PASSO.md` · Documentação: `docs/DOCUMENTACAO.md` · Rubrica: `docs/CHECKLIST_RUBRICA.md` ·
Termo de consentimento: `docs/TERMO_DE_CONSENTIMENTO.md` · Dicionário de dados: `docs/DICIONARIO_DE_DADOS.md`
