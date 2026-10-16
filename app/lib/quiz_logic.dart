/// Retorna o perfil mais frequente; em empate, vence o que apareceu primeiro.
String perfilVencedor(List<String> respostas) {
  if (respostas.isEmpty) throw ArgumentError('sem respostas');
  final cont = <String, int>{};
  for (final p in respostas) {
    cont[p] = (cont[p] ?? 0) + 1;
  }
  var melhor = respostas.first;
  for (final p in respostas) {
    if (cont[p]! > cont[melhor]!) melhor = p;
  }
  return melhor;
}
