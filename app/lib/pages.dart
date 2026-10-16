import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import 'api.dart';
import 'quiz_logic.dart';
import 'telemetry.dart';

/// RF07: abre o menu de compartilhamento do sistema; se a plataforma não oferecer, copia o texto.
Future<void> compartilhar(BuildContext context, String titulo, String texto) async {
  final aviso = ScaffoldMessenger.of(context);
  final mensagem = '$titulo\n$texto\n\nConheça o curso DSM — Fatec Zona Sul.';
  try {
    await Share.share(mensagem, subject: titulo);
  } catch (_) {
    await Clipboard.setData(ClipboardData(text: mensagem));
    aviso.showSnackBar(const SnackBar(content: Text('Compartilhamento indisponível aqui. Texto copiado!')));
  }
}

/// Carrega dados assíncronos com estado de erro e "tentar novamente".
class Loader<T> extends StatefulWidget {
  final Future<T> Function() load;
  final Widget Function(BuildContext, T) builder;
  const Loader({super.key, required this.load, required this.builder});
  @override
  State<Loader<T>> createState() => _LoaderState<T>();
}

class _LoaderState<T> extends State<Loader<T>> {
  late Future<T> _f;
  @override
  void initState() {
    super.initState();
    _f = widget.load();
  }

  void _reload() => setState(() => _f = widget.load());

  @override
  Widget build(BuildContext context) => FutureBuilder<T>(
        future: _f,
        builder: (c, s) {
          if (s.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (s.hasError) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.cloud_off, size: 48, semanticLabel: 'Sem conexão'),
                const SizedBox(height: 8),
                const Text('Sem conexão e sem dados salvos.'),
                const SizedBox(height: 8),
                FilledButton(onPressed: _reload, child: const Text('Tentar novamente')),
              ]),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => _reload(),
            child: widget.builder(c, s.data as T),
          );
        },
      );
}

class ContentList extends StatelessWidget {
  final String kind;
  const ContentList(this.kind, {super.key});

  @override
  Widget build(BuildContext context) => Loader<List<dynamic>>(
        load: () => Api.i.content(kind: kind),
        builder: (c, items) => ListView(
          padding: const EdgeInsets.all(12),
          children: items.isEmpty
              ? const [ListTile(title: Text('Nenhum conteúdo disponível.'))]
              : [
                  for (final it in items)
                    Card(
                      child: ListTile(
                        title: Text(it['title'] as String),
                        subtitle: Text((it['body'] ?? '') as String),
                        trailing: IconButton(
                          tooltip: 'Compartilhar',
                          icon: const Icon(Icons.share),
                          onPressed: () => compartilhar(c, it['title'] as String, (it['body'] ?? '') as String),
                        ),
                      ),
                    ),
                ],
        ),
      );
}

class InicioPage extends StatelessWidget {
  const InicioPage({super.key});

  @override
  Widget build(BuildContext context) => Loader<List<dynamic>>(
        load: () => Api.i.content(kind: 'apresentacao'),
        builder: (c, items) => ListView(padding: const EdgeInsets.all(12), children: [
          Text('Conheça o curso de Desenvolvimento de Software Multiplataforma',
              style: Theme.of(c).textTheme.headlineSmall),
          const SizedBox(height: 12),
          for (final it in items)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(it['title'] as String, style: Theme.of(c).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text((it['body'] ?? '') as String),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      icon: const Icon(Icons.share),
                      label: const Text('Compartilhar'),
                      onPressed: () => compartilhar(c, it['title'] as String, (it['body'] ?? '') as String),
                    ),
                  ),
                ]),
              ),
            ),
        ]),
      );
}

class CursoPage extends StatelessWidget {
  const CursoPage({super.key});

  @override
  Widget build(BuildContext context) => DefaultTabController(
        length: 4,
        child: Column(children: [
          const TabBar(isScrollable: true, tabs: [
            Tab(text: 'Matriz'),
            Tab(text: 'Projetos'),
            Tab(text: 'Depoimentos'),
            Tab(text: 'Dúvidas'),
          ]),
          const Expanded(
            child: TabBarView(children: [
              ContentList('disciplina'),
              ContentList('projeto'),
              ContentList('depoimento'),
              FaqTab(),
            ]),
          ),
        ]),
      );
}

class FaqTab extends StatelessWidget {
  const FaqTab({super.key});

  Future<void> _msg(BuildContext context) async {
    final nome = TextEditingController();
    final texto = TextEditingController();
    final enviar = await showDialog<bool>(
      context: context,
      builder: (d) => AlertDialog(
        title: const Text('Fale com a coordenação'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: nome, decoration: const InputDecoration(labelText: 'Seu nome (opcional)')),
          TextField(controller: texto, maxLines: 3, decoration: const InputDecoration(labelText: 'Sua dúvida')),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(d, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(d, true), child: const Text('Enviar')),
        ],
      ),
    );
    if (enviar != true) return;
    String r = 'Mensagem enviada!';
    try {
      await Api.i.sendMessage(nome.text, texto.text);
    } catch (e) {
      r = 'Não foi possível enviar: $e';
    }
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(r)));
  }

  @override
  Widget build(BuildContext context) => Column(children: [
        const Expanded(child: ContentList('faq')),
        Padding(
          padding: const EdgeInsets.all(12),
          child: FilledButton.icon(
            icon: const Icon(Icons.mail_outline),
            label: const Text('Falar com a coordenação'),
            onPressed: () => _msg(context),
          ),
        ),
      ]);
}

class EventosPage extends StatelessWidget {
  const EventosPage({super.key});

  Future<void> _presenca(BuildContext context, Map it) async {
    final ctrl = TextEditingController();
    final modo = await showDialog<String>(
      context: context,
      builder: (d) => AlertDialog(
        title: const Text('Registrar presença'),
        scrollable: true,
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          TextField(
            controller: ctrl,
            decoration: const InputDecoration(labelText: 'Código do evento (do QR no estande)'),
          ),
          const SizedBox(height: 16),
          const Text('Ou confirme pela sua localização (é preciso estar a até 150 m do local do evento).'),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(d), child: const Text('Cancelar')),
          OutlinedButton.icon(
            icon: const Icon(Icons.my_location),
            label: const Text('Usar minha localização'),
            onPressed: () => Navigator.pop(d, 'local'),
          ),
          FilledButton(onPressed: () => Navigator.pop(d, 'codigo'), child: const Text('Confirmar código')),
        ],
      ),
    );
    if (modo == null) return;
    final id = it['id'] as int;
    final msg = modo == 'local'
        ? await Telemetry.i.presencaPorLocalizacao(id)
        : await Telemetry.i.presenca(id, codigo: ctrl.text);
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) => Loader<List<dynamic>>(
        load: () => Api.i.content(kind: 'evento'),
        builder: (c, items) => ListView(padding: const EdgeInsets.all(12), children: [
          for (final it in items)
            Card(
              child: ListTile(
                title: Text(it['title'] as String),
                subtitle: Text((it['body'] ?? '') as String),
                trailing: IconButton(
                  tooltip: 'Registrar presença (código ou localização)',
                  icon: const Icon(Icons.qr_code_2),
                  onPressed: () => _presenca(c, it as Map),
                ),
              ),
            ),
        ]),
      );
}

class QuizPage extends StatefulWidget {
  const QuizPage({super.key});
  @override
  State<QuizPage> createState() => _QuizPageState();
}

class _QuizPageState extends State<QuizPage> {
  int _q = 0;
  final List<String> _resp = [];

  @override
  Widget build(BuildContext context) => Loader<Map<String, dynamic>>(
        load: Api.i.quiz,
        builder: (c, quiz) {
          final perguntas = quiz['perguntas'] as List;
          if (_q >= perguntas.length) {
            final perfil = perfilVencedor(_resp);
            final info = (quiz['perfis'] as Map)[perfil] as Map;
            return ListView(padding: const EdgeInsets.all(16), children: [
              Text('Seu perfil:', style: Theme.of(c).textTheme.titleMedium),
              Text(info['titulo'] as String, style: Theme.of(c).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text(info['descricao'] as String),
              const SizedBox(height: 8),
              const Text('Resultado orientativo: não tem efeito sobre o processo seletivo.',
                  style: TextStyle(fontStyle: FontStyle.italic)),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: () => setState(() {
                  _q = 0;
                  _resp.clear();
                }),
                child: const Text('Refazer'),
              ),
            ]);
          }
          final p = perguntas[_q] as Map;
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text('Pergunta ${_q + 1} de ${perguntas.length}'),
            const SizedBox(height: 8),
            Text(p['texto'] as String, style: Theme.of(c).textTheme.titleLarge),
            const SizedBox(height: 12),
            for (final o in p['opcoes'] as List)
              Card(
                child: ListTile(
                  title: Text(o['texto'] as String),
                  onTap: () {
                    Telemetry.i.track('quiz', {'questao': p['id'], 'perfil': o['perfil']});
                    setState(() {
                      _resp.add(o['perfil'] as String);
                      _q++;
                    });
                  },
                ),
              ),
          ]);
        },
      );
}

class Barras extends StatelessWidget {
  final String titulo;
  final List<MapEntry<String, num>> dados;
  const Barras(this.titulo, this.dados, {super.key});

  @override
  Widget build(BuildContext context) {
    final maxV = dados.isEmpty ? 1 : dados.map((e) => e.value).reduce((a, b) => a > b ? a : b);
    final resumo = dados.isEmpty ? 'sem dados suficientes' : dados.map((e) => '${e.key} ${e.value}').join(', ');
    return Semantics(
      container: true,
      label: '$titulo: $resumo',
      child: ExcludeSemantics(child: Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(titulo, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          if (dados.isEmpty) const Text('Sem dados suficientes (mínimo de 10 registros por grupo).'),
          for (final d in dados)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(children: [
                SizedBox(width: 90, child: Text(d.key, overflow: TextOverflow.ellipsis)),
                Expanded(child: LinearProgressIndicator(value: d.value / maxV, minHeight: 10)),
                const SizedBox(width: 8),
                Text('${d.value}'),
              ]),
            ),
        ]),
      ),
    )));
  }
}

class PainelPage extends StatelessWidget {
  const PainelPage({super.key});

  @override
  Widget build(BuildContext context) => Loader<Map<String, dynamic>>(
        load: Api.i.publicMetrics,
        builder: (c, m) {
          final telas = [for (final t in m['telas'] as List) MapEntry(t['tela'] as String, t['total'] as num)];
          final perfis = [for (final t in m['perfis'] as List) MapEntry(t['perfil'] as String, t['total'] as num)];
          final porDia = <String, num>{};
          for (final d in m['diario'] as List) {
            porDia[d['dia'] as String] = (porDia[d['dia']] ?? 0) + (d['total'] as num);
          }
          return ListView(padding: const EdgeInsets.all(12), children: [
            Text('Painel público (dados agregados e anonimizados)', style: Theme.of(c).textTheme.titleMedium),
            const SizedBox(height: 8),
            Barras('Telas mais acessadas (7 dias)', telas),
            Barras('Perfis do questionário', perfis),
            Barras('Interações por dia', porDia.entries.take(7).toList()),
          ]);
        },
      );
}
