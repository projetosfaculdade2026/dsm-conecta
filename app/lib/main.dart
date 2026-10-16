import 'package:flutter/material.dart';
import 'a11y.dart';
import 'admin.dart';
import 'pages.dart';
import 'privacy.dart';
import 'telemetry.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Telemetry.i.init();
  await Acessibilidade.i.init();
  runApp(const DsmApp());
}

class DsmApp extends StatelessWidget {
  const DsmApp({super.key});

  @override
  Widget build(BuildContext context) => ListenableBuilder(
        listenable: Acessibilidade.i,
        builder: (context, _) => MaterialApp(
          title: 'DSM Conecta',
          debugShowCheckedModeBanner: false,
          theme: temaDsm(),
          // RNF19: a escala escolhida no app soma-se ao tamanho de fonte do sistema.
          builder: (context, child) {
            final mq = MediaQuery.of(context);
            return MediaQuery(
              data: mq.copyWith(textScaler: TextScaler.linear(mq.textScaler.scale(1) * Acessibilidade.i.escala)),
              child: child!,
            );
          },
          home: const Home(),
        ),
      );
}

class Home extends StatefulWidget {
  const Home({super.key});
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  int _i = 0;
  static const _telas = ['inicio', 'curso', 'eventos', 'quiz', 'painel'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!Telemetry.i.decided) consentDialog(context);
      Telemetry.i.track('interacao', {'tela': _telas[0]});
    });
  }

  @override
  Widget build(BuildContext context) {
    final paginas = [
      const InicioPage(),
      const CursoPage(),
      const EventosPage(),
      const QuizPage(),
      const PainelPage(),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('DSM Conecta'),
        actions: [
          IconButton(
            tooltip: 'Privacidade e meus dados',
            icon: const Icon(Icons.privacy_tip_outlined),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PrivacyPage())),
          ),
          IconButton(
            tooltip: 'Área da coordenação',
            icon: const Icon(Icons.admin_panel_settings_outlined),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminGate())),
          ),
        ],
      ),
      body: SafeArea(child: paginas[_i]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _i,
        onDestinationSelected: (v) {
          setState(() => _i = v);
          Telemetry.i.track('interacao', {'tela': _telas[v]});
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Início'),
          NavigationDestination(icon: Icon(Icons.school_outlined), label: 'Curso'),
          NavigationDestination(icon: Icon(Icons.event_outlined), label: 'Eventos'),
          NavigationDestination(icon: Icon(Icons.quiz_outlined), label: 'Quiz'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), label: 'Painel'),
        ],
      ),
    );
  }
}
