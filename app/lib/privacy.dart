import 'package:flutter/material.dart';
import 'a11y.dart';
import 'api.dart';
import 'consent_text.dart';
import 'telemetry.dart';

/// Parágrafos do termo (mesmo texto de docs/TERMO_DE_CONSENTIMENTO.md).
List<Widget> _paragrafosDoTermo() => [
      for (final p in termoConsentimento)
        Padding(padding: const EdgeInsets.only(bottom: 10), child: Text(p)),
    ];

Future<void> consentDialog(BuildContext context) => showDialog(
      context: context,
      barrierDismissible: false,
      builder: (d) => AlertDialog(
        title: const Text('Termo de consentimento'),
        scrollable: true,
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: _paragrafosDoTermo(),
        ),
        actions: [
          TextButton(
            onPressed: () async {
              await Telemetry.i.setConsent(false);
              if (d.mounted) Navigator.pop(d);
            },
            child: const Text('Não aceito'),
          ),
          FilledButton(
            onPressed: () async {
              await Telemetry.i.setConsent(true);
              if (d.mounted) Navigator.pop(d);
            },
            child: const Text('Aceito'),
          ),
        ],
      ),
    );

class PrivacyPage extends StatefulWidget {
  const PrivacyPage({super.key});
  @override
  State<PrivacyPage> createState() => _PrivacyPageState();
}

class _PrivacyPageState extends State<PrivacyPage> {
  Future<List<dynamic>>? _hist;

  @override
  void initState() {
    super.initState();
    Telemetry.i.addListener(_r);
    _carregar();
  }

  @override
  void dispose() {
    Telemetry.i.removeListener(_r);
    super.dispose();
  }

  void _r() => setState(() {});

  void _carregar() {
    final sid = Telemetry.i.sessionId;
    _hist = sid == null ? Future.value([]) : Api.i.history(sid);
  }

  void _aviso(String m) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));

  @override
  Widget build(BuildContext context) {
    final t = Telemetry.i;
    return Scaffold(
      appBar: AppBar(title: const Text('Privacidade e meus dados')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        SwitchListTile(
          title: const Text('Permitir coleta de dados de uso'),
          subtitle: const Text('Você pode revogar quando quiser.'),
          value: t.consent,
          onChanged: (v) async {
            await t.setConsent(v);
            setState(_carregar);
          },
        ),
        ExpansionTile(
          title: Text('Ler o termo de consentimento (versão $termoVersao)'),
          childrenPadding: const EdgeInsets.symmetric(horizontal: 16),
          expandedCrossAxisAlignment: CrossAxisAlignment.start,
          children: _paragrafosDoTermo(),
        ),
        const Divider(height: 32),
        Text('Acessibilidade', style: Theme.of(context).textTheme.titleMedium),
        ListenableBuilder(
          listenable: Acessibilidade.i,
          builder: (c, _) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Tamanho da fonte: ${(Acessibilidade.i.escala * 100).round()}%'),
            Slider(
              value: Acessibilidade.i.escala,
              min: escalaMinima,
              max: escalaMaxima,
              divisions: 23,
              label: '${(Acessibilidade.i.escala * 100).round()}%',
              semanticFormatterCallback: (v) => 'Tamanho da fonte ${(v * 100).round()} por cento',
              onChanged: (v) => Acessibilidade.i.definir(v),
            ),
            TextButton(onPressed: () => Acessibilidade.i.definir(1.0), child: const Text('Restaurar tamanho padrão')),
          ]),
        ),
        const Divider(height: 32),
        Text('Eventos aguardando envio: ${t.pendentes}'),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          icon: const Icon(Icons.sensors),
          label: const Text('Enviar leitura do sensor do aparelho'),
          onPressed: () async => _aviso(await t.enviarSensor()),
        ),
        OutlinedButton.icon(
          icon: const Icon(Icons.my_location),
          label: const Text('Enviar localização aproximada'),
          onPressed: () async => _aviso(await t.enviarLocalizacaoAproximada()),
        ),
        const Divider(height: 32),
        Text('Meu histórico de interações', style: Theme.of(context).textTheme.titleMedium),
        FutureBuilder<List<dynamic>>(
          future: _hist,
          builder: (c, s) {
            if (s.connectionState != ConnectionState.done) return const LinearProgressIndicator();
            if (s.hasError) return const Text('Histórico indisponível sem conexão.');
            final h = s.data!;
            if (h.isEmpty) return const Text('Nenhuma interação registrada.');
            return Column(children: [
              for (final e in h.take(20))
                ListTile(
                  dense: true,
                  title: Text('${e['categoria']}: ${e['payload']}'),
                  subtitle: Text('${e['ts']}'),
                ),
            ]);
          },
        ),
        const Divider(height: 32),
        FilledButton.icon(
          style: FilledButton.styleFrom(backgroundColor: Colors.red.shade800),
          icon: const Icon(Icons.delete_forever),
          label: const Text('Excluir meus dados'),
          onPressed: () async {
            try {
              await t.excluirDados();
              setState(_carregar);
              _aviso('Dados excluídos.');
            } catch (e) {
              _aviso('Não foi possível excluir agora: $e');
            }
          },
        ),
      ]),
    );
  }
}
