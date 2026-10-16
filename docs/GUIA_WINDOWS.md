# Guia para Windows: do zero até o app aberto

## Parte A: instalar (só uma vez)
| # | Programa | Link | Observação |
|---|---|---|---|
| 1 | **Docker Desktop** | https://www.docker.com/products/docker-desktop | Aceite habilitar o **WSL 2** se pedir e **reinicie o PC**. Abra o Docker Desktop e espere o ícone da baleia ficar **verde**. |
| 2 | **Flutter SDK** | https://docs.flutter.dev/get-started/install/windows | Extraia em `C:\flutter` (sem espaços no caminho) e adicione `C:\flutter\bin` ao **PATH** (Pesquisar > "variáveis de ambiente" > Path > Novo). Feche e reabra o terminal. |
| 3 | **Google Chrome** | chrome.google.com | O app roda nele; **não precisa Android Studio**. |
| 4 | **Git** | https://git-scm.com | Para o GitHub (rubrica de versionamento). |
| 5 | **Python 3.12** (opcional) | https://www.python.org | Só para rodar os testes (`testes.bat`). Marque **Add python.exe to PATH**. |

Conferir: abra o **Prompt de Comando** e rode `docker --version`, `flutter --version`, `git --version`. Todos devem mostrar uma versão.

## Parte B: abrir o projeto (3 cliques)
1. Extraia o `dsm-conecta.zip` (clique direito > Extrair tudo), por exemplo em `C:\projetos\dsm-conecta`.
2. **Duplo clique em `iniciar.bat`**
   - Sobe broker, banco, ingestão, API e totem simulado.
   - Na 1ª vez demora vários minutos (baixa as imagens). No fim abre http://localhost:8000/docs.
3. **Duplo clique em `app.bat`**
   - Na 1ª vez gera as pastas de plataforma e baixa pacotes (alguns minutos).
   - Abre o aplicativo no Chrome.

Para desktop Windows (em vez do Chrome): `app_desktop.bat` (exige "Desenvolvimento para desktop com C++" do Visual Studio; use o Chrome se não quiser instalar).

## Parte C: conferir se funciona
1. No app, **aceite** o consentimento.
2. Navegue pelas abas **Início, Curso, Eventos, Quiz, Painel** e responda o quiz.
3. Ícone de **escudo** (topo): veja seu histórico de interações e o botão **Excluir meus dados**.
4. Ícone de **coordenação** (topo): login `admin` / `admin123` > aba **Tempo real**: os números sobem enquanto você usa o app e o status do totem aparece como `online`.
5. Aba **Eventos** > ícone de QR > código **DSM2026** > "Presença registrada!". Tente de novo: o app avisa que a presença **já foi registrada** (RN05). Na "Visita à escola parceira", use **Usar minha localização** (só confirma se você estiver a até 150 m do local cadastrado).
5b. Em **Privacidade e meus dados**: leia o termo, mude o **tamanho da fonte** e envie a localização aproximada.
5c. Abra http://localhost:8000/simulador/ , clique **Conectar** e **Modo automático**: o totem do navegador publica no broker e o painel admin reage.
6. Aba **Conteúdo** (admin): crie/edite/remova itens. Aba **Exportar**: CSV/JSON.

## Parte D: arquivos de apoio (duplo clique)
| Arquivo | Para quê | Iteração |
|---|---|---|
| `iniciar.bat` | sobe o back-end | todas |
| `app.bat` | abre o app no Chrome | 5 |
| `app_desktop.bat` | abre o app como programa Windows | 5 |
| `testes.bat` | lint + testes + cobertura (≥70%) | 1 e todas |
| `benchmark.bat` | 1 milhão de registros + comparativo de desempenho | 3 |
| `carga.bat` | ensaio de carga 50 msg/s (1 conexão e **1000 conexões reais**), mostra mensagens perdidas | 6 |
| `dados_abertos.bat` | baixa os dados abertos e o dicionário para a pasta `dados-abertos\` | 6 |
| `build_artefatos.bat` | gera web, Windows e APK em `dist\` (e copia o web para a API servir) | 5 |
| `parar.bat` | desliga tudo | – |

## Parte E: o que EU tenho que fazer para a nota (checklist)
**Obrigatório (feche nesta ordem):**
- [ ] Rodar `iniciar.bat` + `app.bat` e confirmar a Parte C.
- [ ] Rodar `testes.bat` e salvar um print (testes passando, cobertura).
- [ ] Criar repositório no GitHub e enviar o projeto (`docs/PASSO_A_PASSO.md`, seção 1).
- [ ] Proteger a branch `main` e abrir PRs revisados por colega de outra equipe (seção 3: commits do teste **antes** do código).
- [ ] Rodar `benchmark.bat` e copiar a tabela de resultados.
- [ ] Rodar `carga.bat` e copiar a linha `RESULTADO ... perdidas=0`.
- [ ] Preencher `docs/DOCUMENTACAO.md` (campos **[PREENCHER]**) com nomes, datas, prints e resultados.
- [ ] Rodar `dados_abertos.bat` e fazer commit da pasta `dados-abertos\`.
- [ ] Fazer a ação de divulgação e gerar o **Relatório para a escola** (aba Exportar); usar os modelos de `docs\modelos\`.
- [ ] Preencher o `docs/CHECKLIST_RUBRICA.md` com as evidências.

**Plano para pouco tempo:** (1) abrir e testar; (2) GitHub + commits + CI; (3) benchmark e carga com prints; (4) documentação; (5) ensaio da apresentação.

## Problemas comuns no Windows
| Problema | Solução |
|---|---|
| "Docker Desktop não está rodando" | Abra o Docker Desktop e espere ficar verde. |
| "WSL 2 installation is incomplete" | PowerShell como administrador: `wsl --install` e reinicie. |
| `'flutter' não é reconhecido` | PATH não configurado; reabra o terminal depois de configurar. |
| Porta 8000, 1883 ou 5432 em uso | Feche o programa que usa a porta (ex.: outro PostgreSQL) ou mude em `docker-compose.yml`. |
| Banco sem tabelas / erro estranho (ou versão anterior do projeto) | `docker compose down -v` e rode `iniciar.bat` de novo. |
| APK não gera | Precisa do Android SDK (Android Studio). Web e Windows não precisam. |
| App não carrega dados | Confirme `http://localhost:8000/health` no navegador. |
| Erro de compilação no Flutter | Copie a mensagem completa e peça correção. |
| Antivírus/Windows Defender bloqueia | Permita o Docker e o Flutter. |
