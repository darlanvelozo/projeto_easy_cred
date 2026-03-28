"""
Management command: popular_banco
Popula o banco com dados realistas de operacao de credito no Piaui.

Uso:
    python manage.py popular_banco
    python manage.py popular_banco --limpar   # apaga tudo antes de popular
"""

from decimal import Decimal
from datetime import date, timedelta
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Empresa, Usuario
from rotas.models import Rota, ConfiguracaoRota, CaixaRota, VendedorRota
from clientes.models import Cliente
from emprestimos.models import Emprestimo, Parcela
from financeiro.models import Pagamento, MovimentacaoFinanceira


# ─── Empresa ─────────────────────────────────────────────────────────────────

EMPRESA = {
    "nome": "EasyCred Piaui",
    "cnpj": "45.123.678/0001-55",
    "email": "contato@easycredpi.com.br",
    "telefone": "(86) 99900-1000",
}

# ─── Usuarios ────────────────────────────────────────────────────────────────
# (username, nome, sobrenome, perfil, senha)

USUARIOS = [
    ("darlan",     "Darlan",    "Velozo",      "admin",    "darlan123"),
    ("marcos",     "Marcos",    "Oliveira",    "gerente",  "marcos123"),
    ("raimundo",   "Raimundo",  "Silva",       "vendedor", "raimundo123"),
    ("chico",      "Francisco", "Santos",      "vendedor", "chico123"),
]

# ─── Rotas (2 cidades do Piaui) ─────────────────────────────────────────────

ROTAS = [
    {
        "nome": "Rota Teresina",
        "taxa": Decimal("20.00"),
        "periodicidade": "diario",
        "parcelas": 20,
        "limite": Decimal("3000.00"),
        "aporte": Decimal("15000.00"),
        "vendedores": ["raimundo"],
    },
    {
        "nome": "Rota Picos",
        "taxa": Decimal("25.00"),
        "periodicidade": "diario",
        "parcelas": 24,
        "limite": Decimal("2000.00"),
        "aporte": Decimal("10000.00"),
        "vendedores": ["chico"],
    },
]

# ─── Clientes ────────────────────────────────────────────────────────────────
# Nomes comuns do Piaui com enderecos e coordenadas reais

CLIENTES = {
    "Rota Teresina": [
        {"nome": "Maria Jose da Silva",       "cpf": "111.222.333-01", "telefone": "(86) 99811-0001", "endereco": "Rua Coelho Rodrigues, 1500",   "bairro": "Centro",         "cidade": "Teresina", "uf": "PI", "lat": -5.0892, "lng": -42.8019},
        {"nome": "Raimunda Nonata Sousa",      "cpf": "111.222.333-02", "telefone": "(86) 99812-0002", "endereco": "Rua Areolino de Abreu, 800",  "bairro": "Centro",         "cidade": "Teresina", "uf": "PI", "lat": -5.0887, "lng": -42.8038},
        {"nome": "Francisco das Chagas Lima",  "cpf": "111.222.333-03", "telefone": "(86) 99813-0003", "endereco": "Av. Frei Serafim, 2200",      "bairro": "Centro",         "cidade": "Teresina", "uf": "PI", "lat": -5.0919, "lng": -42.8058},
        {"nome": "Antonia Alves de Sousa",     "cpf": "111.222.333-04", "telefone": "(86) 99814-0004", "endereco": "Rua Simplicio Mendes, 350",   "bairro": "Pirajá",         "cidade": "Teresina", "uf": "PI", "lat": -5.0788, "lng": -42.7943},
        {"nome": "Jose Ribamar Pereira",       "cpf": "111.222.333-05", "telefone": "(86) 99815-0005", "endereco": "Rua Magalhães Filho, 120",    "bairro": "Marquês",        "cidade": "Teresina", "uf": "PI", "lat": -5.0857, "lng": -42.7973},
        {"nome": "Francisca Carvalho Santos",  "cpf": "111.222.333-06", "telefone": "(86) 99816-0006", "endereco": "Av. Miguel Rosa, 4500",       "bairro": "Ilhotas",        "cidade": "Teresina", "uf": "PI", "lat": -5.0832, "lng": -42.8095},
        {"nome": "Antonio Soares Filho",       "cpf": "111.222.333-07", "telefone": "(86) 99817-0007", "endereco": "Rua Desemb. Freitas, 600",    "bairro": "Noivos",         "cidade": "Teresina", "uf": "PI", "lat": -5.0743, "lng": -42.7881},
        {"nome": "Luzia Ferreira Costa",       "cpf": "111.222.333-08", "telefone": "(86) 99818-0008", "endereco": "Rua Firmino Pires, 90",       "bairro": "Centro",         "cidade": "Teresina", "uf": "PI", "lat": -5.0901, "lng": -42.8003},
        {"nome": "Pedro Paulo de Moura",       "cpf": "111.222.333-09", "telefone": "(86) 99819-0009", "endereco": "Av. Maranhao, 1300",          "bairro": "Matinha",        "cidade": "Teresina", "uf": "PI", "lat": -5.0776, "lng": -42.7919},
        {"nome": "Ana Maria Goncalves",        "cpf": "111.222.333-10", "telefone": "(86) 99820-0010", "endereco": "Rua Lisandro Nogueira, 200",  "bairro": "Centro",         "cidade": "Teresina", "uf": "PI", "lat": -5.0863, "lng": -42.8012},
        {"nome": "Sebastiao Rodrigues Neto",   "cpf": "111.222.333-11", "telefone": "(86) 99821-0011", "endereco": "Rua David Caldas, 450",       "bairro": "Centro",         "cidade": "Teresina", "uf": "PI", "lat": -5.0880, "lng": -42.8045},
        {"nome": "Teresinha de Jesus Araujo",  "cpf": "111.222.333-12", "telefone": "(86) 99822-0012", "endereco": "Rua Barroso, 700",            "bairro": "Centro",         "cidade": "Teresina", "uf": "PI", "lat": -5.0910, "lng": -42.8030},
        {"nome": "Joao Batista Nascimento",    "cpf": "111.222.333-13", "telefone": "(86) 99823-0013", "endereco": "Av. Centenario, 3000",        "bairro": "Dirceu Arcoverde","cidade": "Teresina", "uf": "PI", "lat": -5.1018, "lng": -42.7623},
        {"nome": "Domingas Ribeiro Lopes",     "cpf": "111.222.333-14", "telefone": "(86) 99824-0014", "endereco": "Rua Rui Barbosa, 55",         "bairro": "Piçarra",        "cidade": "Teresina", "uf": "PI", "lat": -5.0825, "lng": -42.8110},
        {"nome": "Carlos Alberto Mendes",      "cpf": "111.222.333-15", "telefone": "(86) 99825-0015", "endereco": "Rua Olavo Bilac, 180",        "bairro": "Jockey",         "cidade": "Teresina", "uf": "PI", "lat": -5.0680, "lng": -42.7860},
    ],
    "Rota Picos": [
        {"nome": "Manoel Bezerra da Cruz",     "cpf": "222.333.444-01", "telefone": "(89) 99901-0001", "endereco": "Rua Monsenhor Hipolito, 500",  "bairro": "Centro",         "cidade": "Picos", "uf": "PI", "lat": -7.0769, "lng": -41.4669},
        {"nome": "Josefa Maria do Carmo",      "cpf": "222.333.444-02", "telefone": "(89) 99902-0002", "endereco": "Rua Coelho de Resende, 200",   "bairro": "Centro",         "cidade": "Picos", "uf": "PI", "lat": -7.0773, "lng": -41.4658},
        {"nome": "Cicero Pereira de Sousa",    "cpf": "222.333.444-03", "telefone": "(89) 99903-0003", "endereco": "Av. Senador Helvidio Nunes, 900","bairro": "Junco",         "cidade": "Picos", "uf": "PI", "lat": -7.0810, "lng": -41.4710},
        {"nome": "Marlene dos Santos Oliveira","cpf": "222.333.444-04", "telefone": "(89) 99904-0004", "endereco": "Rua Benjamin Constant, 150",   "bairro": "Centro",         "cidade": "Picos", "uf": "PI", "lat": -7.0758, "lng": -41.4650},
        {"nome": "Geraldo Alves Teixeira",     "cpf": "222.333.444-05", "telefone": "(89) 99905-0005", "endereco": "Rua Demerval Lobao, 80",       "bairro": "Conduru",        "cidade": "Picos", "uf": "PI", "lat": -7.0825, "lng": -41.4630},
        {"nome": "Rita de Cassia Moura",       "cpf": "222.333.444-06", "telefone": "(89) 99906-0006", "endereco": "Rua Cel. Zuza, 300",           "bairro": "Centro",         "cidade": "Picos", "uf": "PI", "lat": -7.0765, "lng": -41.4675},
        {"nome": "Expedito Gomes da Silva",    "cpf": "222.333.444-07", "telefone": "(89) 99907-0007", "endereco": "Av. Presidente Vargas, 1200",  "bairro": "Catavento",      "cidade": "Picos", "uf": "PI", "lat": -7.0740, "lng": -41.4590},
        {"nome": "Ivone Maria Rodrigues",      "cpf": "222.333.444-08", "telefone": "(89) 99908-0008", "endereco": "Rua Jose Borges, 45",          "bairro": "Parque de Exposicao","cidade": "Picos", "uf": "PI", "lat": -7.0830, "lng": -41.4580},
        {"nome": "Jose Airton Sousa Lima",     "cpf": "222.333.444-09", "telefone": "(89) 99909-0009", "endereco": "Rua Pres. Kennedy, 650",       "bairro": "Bomba",          "cidade": "Picos", "uf": "PI", "lat": -7.0700, "lng": -41.4695},
        {"nome": "Vera Lucia Carvalho",        "cpf": "222.333.444-10", "telefone": "(89) 99910-0010", "endereco": "Rua Oscar Clark, 100",         "bairro": "Junco",          "cidade": "Picos", "uf": "PI", "lat": -7.0795, "lng": -41.4720},
        {"nome": "Damiao Pereira Nunes",       "cpf": "222.333.444-11", "telefone": "(89) 99911-0011", "endereco": "Rua Anisio de Abreu, 70",      "bairro": "Paroquial",      "cidade": "Picos", "uf": "PI", "lat": -7.0780, "lng": -41.4640},
        {"nome": "Creusa Barros de Sousa",     "cpf": "222.333.444-12", "telefone": "(89) 99912-0012", "endereco": "Rua 7 de Setembro, 400",       "bairro": "Centro",         "cidade": "Picos", "uf": "PI", "lat": -7.0755, "lng": -41.4660},
    ],
}

# ─── Emprestimos ─────────────────────────────────────────────────────────────
# Definidos por cliente: (valor_principal, status, parcelas_pagas, dias_inicio)
# dias_inicio = quantos dias atras o emprestimo foi criado
# A maioria e diario, valores entre R$200 e R$2000

EMPRESTIMOS = {
    # === ROTA TERESINA (20 parcelas diarias, taxa 20%) ===
    # Clientes com emprestimos ativos em andamento
    "Maria Jose da Silva":       [(500,  "ativo",        12, 15), (300, "quitado", 20, 50)],
    "Raimunda Nonata Sousa":     [(800,  "ativo",        8,  12)],
    "Francisco das Chagas Lima": [(1000, "ativo",        15, 18), (600, "quitado", 20, 60)],
    "Antonia Alves de Sousa":    [(400,  "ativo",        5,  8)],
    "Jose Ribamar Pereira":      [(1200, "ativo",        10, 14)],
    "Francisca Carvalho Santos": [(600,  "ativo",        3,  5)],
    "Antonio Soares Filho":      [(1500, "inadimplente", 6,  25)],  # parou de pagar ha dias
    "Luzia Ferreira Costa":      [(350,  "ativo",        18, 22)],  # quase quitando
    "Pedro Paulo de Moura":      [(900,  "inadimplente", 4,  30)],  # inadimplente serio
    "Ana Maria Goncalves":       [(700,  "ativo",        7,  10)],
    "Sebastiao Rodrigues Neto":  [(2000, "ativo",        2,  5),   (800, "quitado", 20, 45)],
    "Teresinha de Jesus Araujo": [(450,  "ativo",        14, 18)],
    "Joao Batista Nascimento":   [(1000, "quitado",      20, 40)],  # ja quitou
    "Domingas Ribeiro Lopes":    [(500,  "ativo",        9,  13)],
    "Carlos Alberto Mendes":     [(1800, "ativo",        1,  3)],   # emprestimo recente

    # === ROTA PICOS (24 parcelas diarias, taxa 25%) ===
    "Manoel Bezerra da Cruz":    [(600,  "ativo",        16, 20)],
    "Josefa Maria do Carmo":     [(400,  "ativo",        10, 14), (300, "quitado", 24, 55)],
    "Cicero Pereira de Sousa":   [(1000, "inadimplente", 5,  28)],  # inadimplente
    "Marlene dos Santos Oliveira":[(500, "ativo",        20, 24)],  # quase quitando
    "Geraldo Alves Teixeira":    [(800,  "ativo",        7,  11)],
    "Rita de Cassia Moura":      [(350,  "ativo",        3,  6)],
    "Expedito Gomes da Silva":   [(1500, "ativo",        12, 16), (700, "quitado", 24, 50)],
    "Ivone Maria Rodrigues":     [(450,  "ativo",        8,  12)],
    "Jose Airton Sousa Lima":    [(2000, "inadimplente", 3,  22)],  # inadimplente alto valor
    "Vera Lucia Carvalho":       [(600,  "quitado",      24, 40)],  # ja quitou
    "Damiao Pereira Nunes":      [(900,  "ativo",        14, 18)],
    "Creusa Barros de Sousa":    [(500,  "ativo",        6,  10)],
}


def _movimentar_aporte(caixa, valor, usuario, descricao=""):
    """Registra aporte manual (sem signal) — usado apenas para capital inicial."""
    saldo_ant = caixa.saldo
    caixa.saldo += Decimal(str(valor))
    caixa.save()
    MovimentacaoFinanceira.objects.create(
        caixa=caixa,
        tipo="entrada",
        origem="aporte",
        valor=Decimal(str(valor)),
        saldo_anterior=saldo_ant,
        saldo_posterior=caixa.saldo,
        registrado_por=usuario,
        descricao=descricao,
    )


class Command(BaseCommand):
    help = "Popula o banco com dados realistas de operacao de credito no Piaui"

    def add_arguments(self, parser):
        parser.add_argument("--limpar", action="store_true", help="Limpa dados existentes antes de popular")

    def handle(self, *args, **options):
        if options["limpar"]:
            self.stdout.write("Limpando dados existentes...")
            MovimentacaoFinanceira.objects.all().delete()
            Pagamento.objects.all().delete()
            Parcela.objects.all().delete()
            Emprestimo.objects.all().delete()
            Cliente.objects.all().delete()
            VendedorRota.objects.all().delete()
            CaixaRota.objects.all().delete()
            ConfiguracaoRota.objects.all().delete()
            Rota.objects.all().delete()
            # Desvincula todos os usuarios da empresa e deleta tudo
            Usuario.objects.all().update(empresa=None)
            Usuario.objects.all().delete()
            Empresa.objects.all().delete()
            self.stdout.write(self.style.WARNING("  Dados removidos."))

        hoje = date.today()
        formas_pagamento = ["dinheiro", "dinheiro", "dinheiro", "pix", "dinheiro"]  # maioria dinheiro

        # ── 1. Empresa ───────────────────────────────────────────────────────
        self.stdout.write("\n[1/6] Criando empresa...")
        empresa, _ = Empresa.objects.get_or_create(
            cnpj=EMPRESA["cnpj"],
            defaults={k: v for k, v in EMPRESA.items() if k != "cnpj"},
        )
        self.stdout.write(f"  + {empresa.nome}")

        # ── 2. Usuarios ──────────────────────────────────────────────────────
        self.stdout.write("\n[2/6] Criando usuarios...")
        usuarios_map = {}

        for username, nome, sobrenome, perfil, senha in USUARIOS:
            if not Usuario.objects.filter(username=username).exists():
                u = Usuario.objects.create_user(
                    username=username, password=senha,
                    first_name=nome, last_name=sobrenome,
                    email=f"{username}@easycredpi.com.br",
                    empresa=empresa, perfil=perfil,
                )
                self.stdout.write(f"  + {perfil:8s}  {username}  (senha: {senha})")
            else:
                u = Usuario.objects.get(username=username)
            usuarios_map[username] = u

        # Superuser
        if not Usuario.objects.filter(username="admin").exists():
            Usuario.objects.create_superuser(
                username="admin", password="admin123",
                email="admin@easycredpi.com.br",
            )
            self.stdout.write(f"  + {'super':8s}  admin  (senha: admin123)")

        # ── 3. Rotas ─────────────────────────────────────────────────────────
        self.stdout.write("\n[3/6] Criando rotas (Teresina e Picos)...")
        rotas_map = {}
        gerente = usuarios_map["marcos"]

        for r in ROTAS:
            rota, _ = Rota.objects.get_or_create(nome=r["nome"], empresa=empresa)
            rotas_map[rota.nome] = rota
            self.stdout.write(f"  + {rota.nome} ({r['periodicidade']}, {r['taxa']}%, {r['parcelas']}x, limite R${r['limite']})")

            ConfiguracaoRota.objects.get_or_create(
                rota=rota,
                defaults={
                    "taxa_juros_padrao": r["taxa"],
                    "periodicidade_padrao": r["periodicidade"],
                    "num_parcelas_padrao": r["parcelas"],
                    "limite_emprestimo_max": r["limite"],
                },
            )

            caixa, _ = CaixaRota.objects.get_or_create(rota=rota)
            if caixa.saldo == 0:
                _movimentar_aporte(caixa, r["aporte"], gerente,
                                   descricao=f"Capital inicial — {rota.nome}")
                self.stdout.write(f"    Caixa: R$ {r['aporte']}")

            for vend_username in r["vendedores"]:
                vendedor = usuarios_map.get(vend_username)
                if vendedor:
                    VendedorRota.objects.get_or_create(vendedor=vendedor, rota=rota)
                    self.stdout.write(f"    Vendedor: {vend_username}")

        # ── 4. Clientes ──────────────────────────────────────────────────────
        self.stdout.write("\n[4/6] Criando clientes...")
        clientes_map = {}

        for rota_nome, lista_clientes in CLIENTES.items():
            rota = rotas_map[rota_nome]
            for c in lista_clientes:
                cliente, _ = Cliente.objects.get_or_create(
                    cpf=c["cpf"],
                    defaults={
                        "empresa": empresa,
                        "rota": rota,
                        "nome": c["nome"],
                        "telefone": c["telefone"],
                        "endereco": c["endereco"],
                        "bairro": c["bairro"],
                        "cidade": c["cidade"],
                        "uf": c["uf"],
                        "latitude": Decimal(str(c["lat"])),
                        "longitude": Decimal(str(c["lng"])),
                    },
                )
                clientes_map[cliente.nome] = cliente

        self.stdout.write(f"  + {len(clientes_map)} clientes (Teresina: 15, Picos: 12)")

        # ── 5. Emprestimos ───────────────────────────────────────────────────
        self.stdout.write("\n[5/6] Criando emprestimos e parcelas...")
        total_emp = 0

        for rota_data in ROTAS:
            rota = rotas_map[rota_data["nome"]]
            config = ConfiguracaoRota.objects.get(rota=rota)
            vr = VendedorRota.objects.filter(rota=rota).first()
            vendedor = vr.vendedor

            for c_data in CLIENTES.get(rota.nome, []):
                cliente = clientes_map[c_data["nome"]]
                emprestimos_def = EMPRESTIMOS.get(cliente.nome, [])

                for valor, status, pagas, dias_inicio in emprestimos_def:
                    criado_ha = hoje - timedelta(days=dias_inicio)

                    # Primeiro vencimento = dia seguinte a criacao (diario)
                    primeiro_venc = criado_ha + timedelta(days=1)

                    emp = Emprestimo(
                        cliente=cliente,
                        rota=rota,
                        vendedor=vendedor,
                        valor_principal=Decimal(str(valor)),
                        taxa_juros=config.taxa_juros_padrao,
                        num_parcelas=config.num_parcelas_padrao,
                        periodicidade=config.periodicidade_padrao,
                        data_primeiro_vencimento=primeiro_venc,
                        status="ativo",  # sera ajustado depois
                    )
                    emp.save()  # signal gera parcelas + saida caixa

                    # ── Atualizar parcelas e criar pagamentos ─────────��──
                    parcelas = list(emp.parcelas.order_by("numero"))

                    for parcela in parcelas:
                        i = parcela.numero
                        venc = parcela.vencimento

                        if status == "quitado":
                            novo_status = "paga"
                        elif i <= pagas:
                            novo_status = "paga"
                        elif status == "inadimplente" and venc < hoje:
                            novo_status = "atrasada"
                        elif venc < hoje and i > pagas:
                            # parcelas vencidas nao pagas em emprestimo ativo
                            # algumas podem estar atrasadas para dar realismo
                            novo_status = "pendente"
                        else:
                            novo_status = "pendente"

                        if novo_status != "pendente":
                            parcela.status = novo_status
                            if novo_status == "paga":
                                # pago no dia do vencimento ou 1 dia depois
                                dia_pgto = venc + timedelta(days=random.choice([0, 0, 0, 1]))
                                parcela.pago_em = timezone.make_aware(
                                    timezone.datetime.combine(
                                        dia_pgto,
                                        timezone.datetime.min.time().replace(
                                            hour=random.randint(7, 17),
                                            minute=random.randint(0, 59),
                                        ),
                                    )
                                )
                            parcela.save(update_fields=["status", "pago_em"])

                    # Criar pagamentos para parcelas pagas (signal registra entrada caixa)
                    for parcela in parcelas:
                        if parcela.status == "paga":
                            Pagamento.objects.create(
                                parcela=parcela,
                                recebido_por=vendedor,
                                valor=parcela.valor,
                                forma=random.choice(formas_pagamento),
                            )

                    # Atualizar status final do emprestimo
                    if status != "ativo":
                        emp.status = status
                        emp.save(update_fields=["status"])

                    total_emp += 1

        self.stdout.write(f"  + {total_emp} emprestimos criados")

        # ── 6. Resumo ────────────────────────────────────────────────────────
        n_empresas = Empresa.objects.count()
        n_usuarios = Usuario.objects.filter(is_superuser=False).count()
        n_rotas = Rota.objects.count()
        n_clientes = Cliente.objects.count()
        n_emprestimos = Emprestimo.objects.count()
        n_parcelas = Parcela.objects.count()
        n_pagamentos = Pagamento.objects.count()
        n_movimentacoes = MovimentacaoFinanceira.objects.count()

        n_ativos = Emprestimo.objects.filter(status="ativo").count()
        n_quitados = Emprestimo.objects.filter(status="quitado").count()
        n_inadimplentes = Emprestimo.objects.filter(status="inadimplente").count()
        n_pagas = Parcela.objects.filter(status="paga").count()
        n_atrasadas = Parcela.objects.filter(status="atrasada").count()
        n_pendentes = Parcela.objects.filter(status="pendente").count()

        self.stdout.write("\n" + "=" * 58)
        self.stdout.write(self.style.SUCCESS("  BANCO POPULADO COM SUCESSO"))
        self.stdout.write("=" * 58)
        self.stdout.write(f"  Empresa:        {n_empresas} (EasyCred Piaui)")
        self.stdout.write(f"  Usuarios:       {n_usuarios}")
        self.stdout.write(f"  Rotas:          {n_rotas} (Teresina + Picos)")
        self.stdout.write(f"  Clientes:       {n_clientes}")
        self.stdout.write(f"  Emprestimos:    {n_emprestimos} (ativos: {n_ativos}, quitados: {n_quitados}, inadimp: {n_inadimplentes})")
        self.stdout.write(f"  Parcelas:       {n_parcelas} (pagas: {n_pagas}, atrasadas: {n_atrasadas}, pendentes: {n_pendentes})")
        self.stdout.write(f"  Pagamentos:     {n_pagamentos}")
        self.stdout.write(f"  Movimentacoes:  {n_movimentacoes}")
        self.stdout.write("")

        for rota_data in ROTAS:
            rota = rotas_map[rota_data["nome"]]
            caixa = CaixaRota.objects.get(rota=rota)
            self.stdout.write(f"  Caixa {rota.nome}: R$ {caixa.saldo:.2f}")

        self.stdout.write("")
        self.stdout.write("  CREDENCIAIS DE ACESSO")
        self.stdout.write("  " + "-" * 54)
        self.stdout.write(f"  {'Usuario':<16} {'Perfil':<18} {'Senha':<14}")
        self.stdout.write("  " + "-" * 54)
        self.stdout.write(f"  {'admin':<16} {'Superuser':<18} {'admin123':<14}")
        self.stdout.write(f"  {'darlan':<16} {'Admin SaaS':<18} {'darlan123':<14}")
        self.stdout.write(f"  {'marcos':<16} {'Gerente':<18} {'marcos123':<14}")
        self.stdout.write(f"  {'raimundo':<16} {'Vendedor (THE)':<18} {'raimundo123':<14}")
        self.stdout.write(f"  {'chico':<16} {'Vendedor (PIC)':<18} {'chico123':<14}")
        self.stdout.write("  " + "-" * 54)
        self.stdout.write("=" * 58 + "\n")
