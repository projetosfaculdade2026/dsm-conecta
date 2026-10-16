-- Conteúdo inicial (aprovado) para o aplicativo ter o que exibir
INSERT INTO content(kind,title,body,extra,approved) VALUES
('apresentacao','Desenvolvimento de Software Multiplataforma',
 'Curso superior de tecnologia da Fatec Zona Sul. Você aprende a criar aplicações que funcionam no celular, no navegador e no computador a partir de uma única base de código.',
 '{"duracao":"6 semestres","turnos":"Noite","ingresso":"Vestibular Fatec","perfil_egresso":"Desenvolve, testa e mantém sistemas multiplataforma."}', true),
('disciplina','Laboratório de Desenvolvimento de Software Multiplataforma','Projeto integrador com sistemas distribuídos, mensageria e dados em tempo real.','{"semestre":"5º"}',true),
('disciplina','Banco de Dados','Modelagem relacional, SQL e introdução a dados não relacionais.','{"semestre":"2º"}',true),
('disciplina','Programação para Dispositivos Móveis','Aplicativos nativos e multiplataforma.','{"semestre":"4º"}',true),
('projeto','DSM Conecta','Este aplicativo: divulgação do curso com métricas em tempo real.','{"tecnologias":"Flutter/Web, FastAPI, MQTT, TimescaleDB"}',true),
('depoimento','Estudante do 4º semestre','Aprendi a construir um app inteiro do zero, do banco de dados à tela.','{}',true),
('evento','Feira de Profissões','Estande do curso com o questionário de afinidade.',
 '{"inicio":"2026-08-01T00:00:00+00:00","fim":"2026-12-31T23:59:59+00:00","codigo":"DSM2026","local":"Fatec Zona Sul","lat":-23.7617,"lon":-46.6987}',true),
('evento','Visita à escola parceira','Presença registrada pela localização do aparelho (raio de 150 m).',
 '{"inicio":"2026-08-01T00:00:00+00:00","fim":"2026-12-31T23:59:59+00:00","local":"Escola parceira","lat":-23.7617,"lon":-46.6987}',true),
('faq','Preciso saber programar para entrar?','Não. O curso começa do básico.','{}',true),
('faq','Como é o processo seletivo?','Vestibular da Fatec, com inscrição no site do Vestibulinho.','{}',true);
