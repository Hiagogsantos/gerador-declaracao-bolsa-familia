# -*- coding: utf-8 -*-
"""
criar_banco_exemplo.py
----------------------
Cria um banco `alunos_2025.db` com alunos FICTÍCIOS, só para testar e
demonstrar o programa. Nenhum dado aqui pertence a uma pessoa real.

Uso:
    python criar_banco_exemplo.py
"""

import os
import random
import sqlite3

CAMINHO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alunos_2025.db")

NOMES_F = ["ANA CLARA", "BEATRIZ", "CECÍLIA", "HELENA", "ISABELA", "JÚLIA",
           "LARA", "MARIA LUÍSA", "SOFIA", "VALENTINA"]
NOMES_M = ["ARTHUR", "BERNARDO", "DAVI", "GABRIEL", "HEITOR", "LUCAS",
           "MIGUEL", "PEDRO", "SAMUEL", "THEO"]
SOBRENOMES = ["ALMEIDA", "BARBOSA", "CARVALHO", "FERREIRA", "GOMES",
              "LIMA", "OLIVEIRA", "PEREIRA", "RIBEIRO", "SOUZA"]
NOMES_MAE = ["ADRIANA", "CLÁUDIA", "FERNANDA", "JULIANA", "PATRÍCIA", "SIMONE"]
NOMES_PAI = ["ANDRÉ", "CARLOS", "EDUARDO", "MARCELO", "RODRIGO", "SÉRGIO"]
CIDADES = ["CIDADE EXEMPLO", "CIDADE VIZINHA", "CAPITAL EXEMPLO"]


def criar():
    random.seed(2025)  # sempre gera os mesmos alunos
    if os.path.exists(CAMINHO):
        os.remove(CAMINHO)
    conn = sqlite3.connect(CAMINHO)
    conn.execute('''
        CREATE TABLE "dados_dos_aluno" (
            "NOME COMPLETO" TEXT, "DATA DE NASCIMENTO" TEXT, NATURALIDADE TEXT,
            "NOME DA MÃE" TEXT, "NOME DO PAI" TEXT, "NIS DO ALUNO" TEXT,
            GÊNERO TEXT, ANO TEXT, TURMA TEXT, TRANSFERENCIA TEXT
        )''')
    linhas = []
    for ano in range(1, 6):
        for turma in ("A", "B"):
            for _ in range(4):
                feminino = random.random() < 0.5
                nome = random.choice(NOMES_F if feminino else NOMES_M)
                s1, s2 = random.sample(SOBRENOMES, 2)
                mae = f"{random.choice(NOMES_MAE)} {s1}"
                pai = "" if random.random() < 0.25 else f"{random.choice(NOMES_PAI)} {s2}"
                nis = "NÃO TEM NIS" if random.random() < 0.15 else f"999{random.randint(10000000, 99999999)}"
                nascimento = f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{2019 - ano}"
                linhas.append((f"{nome} {s1} {s2}", nascimento, random.choice(CIDADES), mae, pai,
                               nis, "F" if feminino else "M", f"{ano}º ANO", turma, ""))
    conn.executemany('INSERT INTO "dados_dos_aluno" VALUES (?,?,?,?,?,?,?,?,?,?)', linhas)
    conn.commit()
    conn.close()
    print(f"Banco de exemplo criado com {len(linhas)} alunos fictícios: {CAMINHO}")


if __name__ == "__main__":
    criar()
