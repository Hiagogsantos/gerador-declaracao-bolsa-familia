# Gerador de Declaração do Bolsa Família

Programa de mesa (Windows) que gera a **declaração escolar para o
Programa Bolsa Família**: busca o aluno, preenche os dados e salva em PDF
ou imprime, com ou sem o quadro de frequência mensal.

## O que ele faz

- Busca o aluno pelo nome no banco de dados local.
- Preenche nome, data de nascimento, filiação e NIS automaticamente
  (com tratamento para quem não tem NIS ou só tem o nome da mãe).
- Dois modelos: declaração simples e declaração com frequência.
- Salva em PDF e manda direto para a impressora.

## Tecnologias

Python · PyQt5 (interface, prévia e PDF) · SQLite · pandas.

## Download

Baixe a versão pronta para Windows na página **Releases** deste repositório
(arquivo `.zip`; descompacte e abra o `.exe`). O Windows pode mostrar um
aviso de segurança na primeira vez, porque o programa não tem assinatura
digital: clique em **Mais informações → Executar assim mesmo**.

## Como rodar pelo código

```bash
pip install -r requirements.txt
python criar_banco_exemplo.py          # cria um banco com 40 alunos fictícios
python gerador_declaracao_bolsafamilia.py
```

O programa lê o banco `alunos_2025.db` da mesma pasta. O banco real da
escola **não** faz parte deste repositório; o `criar_banco_exemplo.py`
gera um com alunos fictícios para testar. A versão pronta da página
Releases já vem com esse banco de exemplo.

## Privacidade

Este repositório tem **apenas o código**. Nenhum dado de aluno, planilha,
banco de dados ou credencial faz parte dele: esses arquivos ficam só no
computador da escola e estão bloqueados pelo `.gitignore`.
