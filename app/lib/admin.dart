import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'api.dart';
import 'pages.dart';

class AdminGate extends StatefulWidget {
  const AdminGate({super.key});
  @override
  State<AdminGate> createState() => _AdminGateState();
}

class _AdminGateState extends State<AdminGate> {
  final _u = TextEditingController(text: 'admin');
  final _p = TextEditingController();
  String? _erro;
  bool _busy = false;

  Future<void> _entrar() async {
    setState(() {
      _busy = true;
      _erro = null;
    });
    try {
      await Api.i.login(_u.text, _p.text);
    } catch (e) {
      _erro = 'Falha no login: $e';
    }
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    if (Api.i.token != null) return const AdminPanel();
    return Scaffold(
      appBar: AppBar(title: const Text('Coordenação')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 360),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(controller: _u, decoration: const InputDecoration(labelText: 'Usuário')),
              TextField(
                controller: _p,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Senha'),
                onSubmitted: (_) => _entrar(),
              ),
              if (_erro != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(_erro!, style: const TextStyle(color: Colors.red))),
              const SizedBox(height: 16),
              FilledButton(onPressed: _busy ? null : _entrar, child: const Text('Entrar')),
            ]),
          ),
        ),
      ),
    );
  }
}

class AdminPanel extends StatelessWidget {
  const AdminPanel({super.key});

  @override
  Widget build(BuildContext context) => DefaultTabController(
        length: 3,
        child: Scaffold(
          appBar: AppBar(
            title: const Text('Painel administrativo'),
            bottom: const TabBar(tabs: [
              Tab(text: 'Tempo real'),
              Tab(text: 'Conteúdo'),
              Tab(text: 'Exportar'),
            ]),
            actions: [
              IconButton(
                tooltip: 'Sair',
                icon: const Icon(Icons.logout),
                onPressed: () {
                  Api.i.token = null;
                  Navigator.pop(context);
                },
              ),
            ],
          ),
          body: const TabBarView(children: [LiveTab(), ContentAdminTab(), ExportTab()]),
        ),
      );
}

class LiveTab extends StatefulWidget {
  const LiveTab({super.key});
  @override
  State<LiveTab> createState() => _LiveTabState();
}

class _LiveTabState extends State<LiveTab> {
  WebSocketChannel? _ch;
  Map<String, dynamic>? _d;
  StreamSubscription? _sub;
  String _estado = 'conectando...';

  @override
  void initState() {
    super.initState();
    _conectar();
  }

  void _conectar() {
    _ch = WebSocketChannel.connect(Api.i.wsUri());
    _sub = _ch!.stream.listen(
      (m) => setState(() {
        _d = jsonDecode(m as String) as Map<String, dynamic>;
        _estado = 'ao vivo';
      }),
      onError: (_) => setState(() => _estado = 'desconectado'),
      onDone: () {
        if (mounted) setState(() => _estado = 'desconectado');
      },
    );
  }

  @override
  void dispose() {
    _sub?.cancel();
    _ch?.sink.close();
    super.dispose();
  }

  static const _janelas = [10, 30, 60, 300, 900, 3600];

  static String _rotulo(int s) => s >= 3600 ? '${s ~/ 3600} h' : (s >= 60 ? '${s ~/ 60} min' : '$s s');

  Widget _kpi(String t, String v, {Color? cor}) => Expanded(
        child: Card(
          color: cor,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(children: [
              Text(v, style: Theme.of(context).textTheme.headlineMedium),
              Text(t, textAlign: TextAlign.center),
            ]),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final d = _d;
    if (d == null) {
      return Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('Tempo real: $_estado'),
          if (_estado == 'desconectado') FilledButton(onPressed: _conectar, child: const Text('Reconectar')),
        ]),
      );
    }
    final alerta = d['alerta'] as Map;
    final janela = (d['janela_s'] as num?)?.toInt() ?? 60;
    final serie = (d['serie'] as List).map((e) => (e as num).toDouble()).toList();
    final maxS = serie.fold<double>(1, (a, b) => b > a ? b : a);
    return ListView(padding: const EdgeInsets.all(12), children: [
      Text('Status: $_estado | Totem: ${d['totem']}'),
      Row(children: [
        const Text('Janela do ranking: '),
        DropdownButton<int>(
          value: janela,
          items: [
            for (final s in ({..._janelas, janela}.toList()..sort()))
              DropdownMenuItem(value: s, child: Text(_rotulo(s))),
          ],
          onChanged: (v) async {
            if (v == null) return;
            try {
              await Api.i.setJanela(v);
            } catch (e) {
              if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erro: $e')));
            }
          },
        ),
      ]),
      Row(children: [
        _kpi('Visitantes ativos (${_rotulo(janela)})', '${d['visitantes_ativos']}'),
        _kpi('Eventos recebidos', '${d['total']}'),
      ]),
      if (alerta['anomalia'] == true)
        Card(
          color: Colors.red.shade100,
          child: ListTile(
            leading: const Icon(Icons.warning_amber, color: Colors.red),
            title: const Text('Alerta: pico de acessos acima do padrão'),
            subtitle: Text('Atual: ${alerta['atual']} | média: ${alerta['media']}'),
          ),
        ),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Eventos a cada 5 s'),
            const SizedBox(height: 8),
            SizedBox(
              height: 80,
              child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
                for (final v in serie)
                  Expanded(
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 1),
                      height: 4 + 76 * (v / maxS),
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
              ]),
            ),
          ]),
        ),
      ),
      Barras('Ranking de telas (janela de ${_rotulo(janela)})',
          [for (final r in d['ranking'] as List) MapEntry(r['tela'] as String, r['total'] as num)]),
      Barras('Presenças por evento',
          [for (final e in (d['presencas'] as Map).entries) MapEntry('evento ${e.key}', e.value as num)]),
      Barras('Distribuição do questionário',
          [for (final e in (d['quiz'] as Map).entries) MapEntry(e.key as String, e.value as num)]),
    ]);
  }
}

class ContentAdminTab extends StatefulWidget {
  const ContentAdminTab({super.key});
  @override
  State<ContentAdminTab> createState() => _ContentAdminTabState();
}

class _ContentAdminTabState extends State<ContentAdminTab> {
  late Future<List<dynamic>> _f = Api.i.adminContent();

  void _recarregar() => setState(() => _f = Api.i.adminContent());

  Future<void> _editar({Map? atual}) async {
    final kinds = ['apresentacao', 'disciplina', 'projeto', 'depoimento', 'evento', 'faq'];
    String kind = (atual?['kind'] as String?) ?? 'projeto';
    final titulo = TextEditingController(text: atual?['title'] as String? ?? '');
    final corpo = TextEditingController(text: atual?['body'] as String? ?? '');
    final extra = TextEditingController(text: jsonEncode(atual?['extra'] ?? {}));
    bool aprovado = (atual?['approved'] as bool?) ?? true;
    final salvar = await showDialog<bool>(
      context: context,
      builder: (d) => StatefulBuilder(
        builder: (d, setD) => AlertDialog(
          title: Text(atual == null ? 'Novo conteúdo' : 'Editar conteúdo'),
          content: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              DropdownButton<String>(
                value: kind,
                isExpanded: true,
                items: [for (final k in kinds) DropdownMenuItem(value: k, child: Text(k))],
                onChanged: (v) => setD(() => kind = v!),
              ),
              TextField(controller: titulo, decoration: const InputDecoration(labelText: 'Título')),
              TextField(controller: corpo, maxLines: 3, decoration: const InputDecoration(labelText: 'Texto')),
              TextField(controller: extra, decoration: const InputDecoration(labelText: 'Extra (JSON; eventos: inicio, fim, codigo)')),
              SwitchListTile(title: const Text('Aprovado para publicação'), value: aprovado, onChanged: (v) => setD(() => aprovado = v)),
            ]),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(d, false), child: const Text('Cancelar')),
            FilledButton(onPressed: () => Navigator.pop(d, true), child: const Text('Salvar')),
          ],
        ),
      ),
    );
    if (salvar != true) return;
    try {
      await Api.i.saveContent(
        {'kind': kind, 'title': titulo.text, 'body': corpo.text, 'extra': jsonDecode(extra.text), 'approved': aprovado},
        id: atual?['id'] as int?,
      );
      _recarregar();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erro: $e')));
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        floatingActionButton: FloatingActionButton(
          tooltip: 'Novo conteúdo',
          onPressed: () => _editar(),
          child: const Icon(Icons.add),
        ),
        body: FutureBuilder<List<dynamic>>(
          future: _f,
          builder: (c, s) {
            if (s.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
            if (s.hasError) return Center(child: Text('Erro: ${s.error}'));
            return ListView(children: [
              for (final it in s.data!)
                ListTile(
                  title: Text('${it['title']}'),
                  subtitle: Text('${it['kind']}${it['approved'] == true ? '' : ' (não aprovado)'}'),
                  onTap: () => _editar(atual: it as Map),
                  trailing: IconButton(
                    tooltip: 'Remover',
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () async {
                      await Api.i.deleteContent(it['id'] as int);
                      _recarregar();
                    },
                  ),
                ),
            ]);
          },
        ),
      );
}

class ExportTab extends StatelessWidget {
  const ExportTab({super.key});

  Future<void> _mostrar(BuildContext context, String titulo, Future<String> Function() carregar) async {
    try {
      final txt = await carregar();
      if (!context.mounted) return;
      await showDialog(
        context: context,
        builder: (d) => AlertDialog(
          title: Text(titulo),
          content: SingleChildScrollView(child: SelectableText(txt)),
          actions: [
            TextButton(
              onPressed: () => Clipboard.setData(ClipboardData(text: txt)),
              child: const Text('Copiar'),
            ),
            TextButton(onPressed: () => Navigator.pop(d), child: const Text('Fechar')),
          ],
        ),
      );
    } catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erro: $e')));
    }
  }

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
        FilledButton.icon(
          icon: const Icon(Icons.table_chart),
          label: const Text('Exportar CSV'),
          onPressed: () => _mostrar(context, 'Dados agregados (csv)', () => Api.i.export('csv')),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          icon: const Icon(Icons.data_object),
          label: const Text('Exportar JSON'),
          onPressed: () => _mostrar(context, 'Dados agregados (json)', () => Api.i.export('json')),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          icon: const Icon(Icons.school),
          label: const Text('Relatório para a escola parceira'),
          onPressed: () => _mostrar(context, 'Devolutiva para a escola', Api.i.relatorio),
        ),
        const SizedBox(height: 24),
        Text('Dados abertos (sem login)', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 4),
        SelectableText('${Api.i.dadosAbertosUrl}\n$apiUrl/open-data/dicionario'),
        const Text('Somente agregados com no mínimo 10 registros por grupo.'),
      ]);
}
