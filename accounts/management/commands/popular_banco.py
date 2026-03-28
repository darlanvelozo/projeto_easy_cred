"""
Management command: popular_banco
Popula o banco com dados realistas para demonstração do sistema.

Uso:
    python manage.py popular_banco
    python manage.py popular_banco --limpar   # apaga tudo antes de popular
"""

from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Empresa, Usuario
from rotas.models import Rota, ConfiguracaoRota, CaixaRota, VendedorRota
from clientes.models import Cliente
from emprestimos.models import Emprestimo, Parcela
from financeiro.models import Pagamento, MovimentacaoFinanceira


# ─── dados fictícios ──────────────────────────────────────────────────────────

EMPRESAS = [
    {"nome": "Crédito Fácil Ltda",   "cnpj": "12.345.678/0001-90", "email": "contato@creditofacil.com.br",   "telefone": "(11) 98000-1111"},
    {"nome": "FinCred Soluções ME",   "cnpj": "98.765.432/0001-10", "email": "financeiro@fincred.com.br",     "telefone": "(21) 97000-2222"},
]

# usuários por empresa: (username, nome, sobrenome, perfil, senha)
USUARIOS = {
    "Crédito Fácil Ltda": [
        ("admin_cf",    "Carlos",   "Mendes",   "admin",    "admin123"),
        ("gerente_cf",  "Fernanda", "Lima",     "gerente",  "gerente123"),
        ("vendedor_cf1","Ricardo",  "Souza",    "vendedor", "vend123"),
        ("vendedor_cf2","Patrícia", "Oliveira", "vendedor", "vend123"),
    ],
    "FinCred Soluções ME": [
        ("admin_fc",    "Marcos",   "Ferreira", "admin",    "admin123"),
        ("gerente_fc",  "Juliana",  "Costa",    "gerente",  "gerente123"),
        ("vendedor_fc1","Anderson", "Santos",   "vendedor", "vend123"),
        ("vendedor_fc2","Beatriz",  "Alves",    "vendedor", "vend123"),
    ],
}

ROTAS = {
    "Crédito Fácil Ltda": [
        {"nome": "Rota Centro",     "taxa": Decimal("15.00"), "periodicidade": "semanal",   "parcelas": 10, "vendedores": ["vendedor_cf1"]},
        {"nome": "Rota Zona Norte", "taxa": Decimal("18.00"), "periodicidade": "quinzenal", "parcelas": 6,  "vendedores": ["vendedor_cf2"]},
    ],
    "FinCred Soluções ME": [
        {"nome": "Rota Baixada",    "taxa": Decimal("20.00"), "periodicidade": "semanal",   "parcelas": 12, "vendedores": ["vendedor_fc1"]},
        {"nome": "Rota Litoral",    "taxa": Decimal("12.00"), "periodicidade": "mensal",    "parcelas": 6,  "vendedores": ["vendedor_fc2"]},
    ],
}

CLIENTES_POR_ROTA = {
    "Rota Centro": [
        {"nome": "José Aparecido Silva",   "cpf": "111.222.333-44", "telefone": "(11) 99111-0001", "endereco": "Rua das Flores, 10",   "bairro": "Centro",      "cidade": "São Paulo",    "uf": "SP"},
        {"nome": "Maria das Graças Nunes", "cpf": "222.333.444-55", "telefone": "(11) 99222-0002", "endereco": "Av. Paulista, 500",    "bairro": "Bela Vista",  "cidade": "São Paulo",    "uf": "SP"},
        {"nome": "Antônio Pereira",        "cpf": "333.444.555-66", "telefone": "(11) 99333-0003", "endereco": "Rua Augusta, 200",     "bairro": "Consolação",  "cidade": "São Paulo",    "uf": "SP"},
        {"nome": "Rosilene Barbosa",       "cpf": "444.555.666-77", "telefone": "(11) 99444-0004", "endereco": "Rua Direita, 15",      "bairro": "Centro",      "cidade": "São Paulo",    "uf": "SP"},
        {"nome": "Valdir Moraes",          "cpf": "555.666.777-88", "telefone": "(11) 99555-0005", "endereco": "Rua 7 de Abril, 88",   "bairro": "República",   "cidade": "São Paulo",    "uf": "SP"},
    ],
    "Rota Zona Norte": [
        {"nome": "Cláudia Rodrigues",      "cpf": "666.777.888-99", "telefone": "(11) 99666-0006", "endereco": "Rua Voluntários, 50",  "bairro": "Santana",     "cidade": "São Paulo",    "uf": "SP"},
        {"nome": "Edson Carvalho",         "cpf": "777.888.999-00", "telefone": "(11) 99777-0007", "endereco": "Av. Tucuruvi, 300",    "bairro": "Tucuruvi",    "cidade": "São Paulo",    "uf": "SP"},
        {"nome": "Sueli Gonçalves",        "cpf": "888.999.000-11", "telefone": "(11) 99888-0008", "endereco": "Rua do Horto, 12",     "bairro": "Casa Verde",  "cidade": "São Paulo",    "uf": "SP"},
        {"nome": "Gilson Teixeira",        "cpf": "999.000.111-22", "telefone": "(11) 99999-0009", "endereco": "Rua Jaçanã, 77",       "bairro": "Jaçanã",      "cidade": "São Paulo",    "uf": "SP"},
    ],
    "Rota Baixada": [
        {"nome": "Luciana Campos",         "cpf": "101.202.303-40", "telefone": "(21) 98101-0010", "endereco": "Rua 1, 100",           "bairro": "Centro",      "cidade": "Duque de Caxias", "uf": "RJ"},
        {"nome": "Roberto Dias",           "cpf": "202.303.404-50", "telefone": "(21) 98202-0011", "endereco": "Av. Presidente Vargas","bairro": "Jardim",      "cidade": "Nova Iguaçu",     "uf": "RJ"},
        {"nome": "Eliane Melo",            "cpf": "303.404.505-60", "telefone": "(21) 98303-0012", "endereco": "Rua das Palmeiras, 5", "bairro": "Figueira",    "cidade": "Nilópolis",       "uf": "RJ"},
        {"nome": "Paulo Henrique Ramos",   "cpf": "404.505.606-70", "telefone": "(21) 98404-0013", "endereco": "Rua Nova, 44",         "bairro": "Heliópolis",  "cidade": "Belford Roxo",    "uf": "RJ"},
        {"nome": "Simone Araújo",          "cpf": "505.606.707-80", "telefone": "(21) 98505-0014", "endereco": "Travessa do Sol, 3",   "bairro": "Centro",      "cidade": "São João de Meriti","uf": "RJ"},
    ],
    "Rota Litoral": [
        {"nome": "Fernando Nascimento",    "cpf": "606.707.808-90", "telefone": "(21) 97606-0015", "endereco": "Rua da Praia, 20",     "bairro": "Barra",       "cidade": "Cabo Frio",    "uf": "RJ"},
        {"nome": "Adriana Pinto",          "cpf": "707.808.909-01", "telefone": "(21) 97707-0016", "endereco": "Av. Atlântica, 1000",  "bairro": "Praia Grande","cidade": "Búzios",       "uf": "RJ"},
        {"nome": "Jorge Luis Machado",     "cpf": "808.909.010-12", "telefone": "(21) 97808-0017", "endereco": "Rua das Ondas, 8",     "bairro": "Centro",      "cidade": "Arraial do Cabo","uf": "RJ"},
        {"nome": "Neuza Correia",          "cpf": "909.010.111-23", "telefone": "(21) 97909-0018", "endereco": "Rua do Caju, 55",      "bairro": "Iguabinha",   "cidade": "Araruama",     "uf": "RJ"},
    ],
}

# empréstimos por cliente: (valor_principal, status, parcelas_pagas, dias_atraso)
# parcelas_pagas = quantas parcelas já foram pagas
# dias_atraso    = se > 0, o último vencimento está atrasado
EMPRESTIMOS_POR_CLIENTE = {
    # Rota Centro
    "José Aparecido Silva":   [(500,  "ativo",        3, 0),  (300, "quitado", 10, 0)],
    "Maria das Graças Nunes": [(800,  "ativo",        5, 0),  (200, "quitado", 10, 0)],
    "Antônio Pereira":        [(1000, "inadimplente", 2, 14)],
    "Rosilene Barbosa":       [(400,  "ativo",        1, 0)],
    "Valdir Moraes":          [(600,  "ativo",        4, 0),  (700, "quitado", 10, 0)],
    # Rota Zona Norte
    "Cláudia Rodrigues":      [(500,  "ativo",        2, 0)],
    "Edson Carvalho":         [(900,  "inadimplente", 1, 21)],
    "Sueli Gonçalves":        [(350,  "ativo",        3, 0),  (300, "quitado", 10, 0)],
    "Gilson Teixeira":        [(1200, "ativo",        6, 0)],
    # Rota Baixada
    "Luciana Campos":         [(600,  "ativo",        4, 0)],
    "Roberto Dias":           [(1000, "ativo",        2, 0),  (500, "quitado", 12, 0)],
    "Eliane Melo":            [(400,  "inadimplente", 1, 30)],
    "Paulo Henrique Ramos":   [(800,  "ativo",        5, 0)],
    "Simone Araújo":          [(500,  "ativo",        3, 0)],
    # Rota Litoral
    "Fernando Nascimento":    [(2000, "ativo",        2, 0)],
    "Adriana Pinto":          [(1500, "ativo",        1, 0),  (800, "quitado", 6, 0)],
    "Jorge Luis Machado":     [(600,  "inadimplente", 0, 45)],
    "Neuza Correia":          [(300,  "ativo",        3, 0)],
}


def _delta(periodicidade, n):
    """Retorna timedelta de n períodos conforme periodicidade."""
    if periodicidade == "diario":    return timedelta(days=n)
    if periodicidade == "semanal":   return timedelta(weeks=n)
    if periodicidade == "quinzenal": return timedelta(days=15 * n)
    return timedelta(days=30 * n)  # mensal


def _movimentar(caixa, tipo, origem, valor, usuario, referencia_pgto=None, descricao=""):
    saldo_ant = caixa.saldo
    if tipo == "entrada":
        caixa.saldo += Decimal(str(valor))
    else:
        caixa.saldo -= Decimal(str(valor))
    caixa.save()
    MovimentacaoFinanceira.objects.create(
        caixa=caixa,
        tipo=tipo,
        origem=origem,
        valor=Decimal(str(valor)),
        saldo_anterior=saldo_ant,
        saldo_posterior=caixa.saldo,
        referencia_pagamento=referencia_pgto,
        registrado_por=usuario,
        descricao=descricao,
    )


class Command(BaseCommand):
    help = "Popula o banco com dados realistas para demonstração"

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
            Usuario.objects.filter(is_superuser=False).delete()
            Empresa.objects.all().delete()
            self.stdout.write(self.style.WARNING("  Dados removidos."))

        hoje = date.today()

        # ── 1. Empresas ───────────────────────────────────────────────────────
        self.stdout.write("\n[1/6] Criando empresas e usuários...")
        usuarios_map = {}  # username → objeto Usuario

        for emp_data in EMPRESAS:
            empresa, _ = Empresa.objects.get_or_create(
                cnpj=emp_data["cnpj"],
                defaults={k: v for k, v in emp_data.items() if k != "cnpj"},
            )
            self.stdout.write(f"  + Empresa: {empresa.nome}")

            # ── 2. Usuários ───────────────────────────────────────────────────
            for username, nome, sobrenome, perfil, senha in USUARIOS[empresa.nome]:
                if not Usuario.objects.filter(username=username).exists():
                    u = Usuario.objects.create_user(
                        username=username,
                        password=senha,
                        first_name=nome,
                        last_name=sobrenome,
                        email=f"{username}@easycred.com.br",
                        empresa=empresa,
                        perfil=perfil,
                    )
                    self.stdout.write(f"    → {perfil:8s}  {username}  (senha: {senha})")
                else:
                    u = Usuario.objects.get(username=username)
                usuarios_map[username] = u

        # ── 3. Rotas ──────────────────────────────────────────────────────────
        self.stdout.write("\n[2/6] Criando rotas...")
        rotas_map = {}  # nome da rota → objeto Rota

        for emp_data in EMPRESAS:
            empresa = Empresa.objects.get(cnpj=emp_data["cnpj"])
            for r in ROTAS[empresa.nome]:
                rota, _ = Rota.objects.get_or_create(nome=r["nome"], empresa=empresa)
                rotas_map[rota.nome] = rota
                self.stdout.write(f"  + Rota: {rota.nome} ({r['periodicidade']}, {r['taxa']}% juros)")

                ConfiguracaoRota.objects.get_or_create(
                    rota=rota,
                    defaults={
                        "taxa_juros_padrao": r["taxa"],
                        "periodicidade_padrao": r["periodicidade"],
                        "num_parcelas_padrao": r["parcelas"],
                        "limite_emprestimo_max": Decimal("5000.00"),
                    },
                )

                caixa, _ = CaixaRota.objects.get_or_create(rota=rota)

                # aporte inicial de capital
                gerente = Usuario.objects.filter(empresa=empresa, perfil="gerente").first()
                if caixa.saldo == 0:
                    _movimentar(caixa, "entrada", "aporte", 10000, gerente,
                                descricao="Capital inicial da rota")
                    self.stdout.write(f"    → Caixa aberto com R$ 10.000,00")

                # vincular vendedores
                for vend_username in r["vendedores"]:
                    vendedor = usuarios_map.get(vend_username)
                    if vendedor:
                        VendedorRota.objects.get_or_create(vendedor=vendedor, rota=rota)
                        self.stdout.write(f"    → Vendedor vinculado: {vend_username}")

        # ── 4. Clientes ───────────────────────────────────────────────────────
        self.stdout.write("\n[3/6] Criando clientes...")
        clientes_map = {}  # nome → objeto Cliente

        for emp_data in EMPRESAS:
            empresa = Empresa.objects.get(cnpj=emp_data["cnpj"])
            for r in ROTAS[empresa.nome]:
                rota = rotas_map[r["nome"]]
                for c in CLIENTES_POR_ROTA.get(rota.nome, []):
                    cliente, _ = Cliente.objects.get_or_create(
                        cpf=c["cpf"],
                        defaults={**c, "empresa": empresa, "rota": rota},
                    )
                    clientes_map[cliente.nome] = cliente
        self.stdout.write(f"  → {len(clientes_map)} clientes criados")

        # ── 5. Empréstimos + Parcelas ─────────────────────────────────────────
        self.stdout.write("\n[4/6] Criando empréstimos e parcelas...")
        total_emp = 0

        for emp_data in EMPRESAS:
            empresa = Empresa.objects.get(cnpj=emp_data["cnpj"])
            for r_data in ROTAS[empresa.nome]:
                rota = rotas_map[r_data["nome"]]
                caixa = CaixaRota.objects.get(rota=rota)
                config = ConfiguracaoRota.objects.get(rota=rota)
                vendedor = VendedorRota.objects.filter(rota=rota).first().vendedor

                for c_data in CLIENTES_POR_ROTA.get(rota.nome, []):
                    cliente = clientes_map[c_data["nome"]]
                    emprestimos_def = EMPRESTIMOS_POR_CLIENTE.get(cliente.nome, [])

                    for idx, (valor, status, pagas, dias_atraso) in enumerate(emprestimos_def):
                        # data de criação: empréstimos mais antigos para quitados
                        if status == "quitado":
                            criado_ha = hoje - timedelta(days=90 + idx * 30)
                        elif status == "inadimplente":
                            criado_ha = hoje - timedelta(days=60 + dias_atraso)
                        else:
                            criado_ha = hoje - timedelta(days=30 + idx * 15)

                        primeiro_venc = criado_ha + _delta(config.periodicidade_padrao, 1)

                        emp = Emprestimo(
                            cliente=cliente,
                            rota=rota,
                            vendedor=vendedor,
                            valor_principal=Decimal(str(valor)),
                            taxa_juros=config.taxa_juros_padrao,
                            num_parcelas=config.num_parcelas_padrao,
                            periodicidade=config.periodicidade_padrao,
                            data_primeiro_vencimento=primeiro_venc,
                            status=status,
                        )
                        emp.save()  # dispara cálculo de valor_total e valor_parcela

                        # movimentação de saída no caixa (concessão)
                        _movimentar(caixa, "saida", "emprestimo", emp.valor_principal, vendedor,
                                    descricao=f"Empréstimo #{emp.pk} — {cliente.nome}")

                        # gerar parcelas
                        parcelas_criadas = []
                        for i in range(1, config.num_parcelas_padrao + 1):
                            venc = primeiro_venc + _delta(config.periodicidade_padrao, i - 1)

                            if status == "quitado":
                                p_status = "paga"
                            elif i <= pagas:
                                p_status = "paga"
                            elif dias_atraso > 0 and i == pagas + 1:
                                p_status = "atrasada"
                            elif venc < hoje:
                                p_status = "atrasada" if status == "inadimplente" else "pendente"
                            else:
                                p_status = "pendente"

                            pago_em = None
                            if p_status == "paga":
                                pago_em = timezone.make_aware(
                                    timezone.datetime.combine(venc + timedelta(days=1), timezone.datetime.min.time())
                                )

                            parcela = Parcela.objects.create(
                                emprestimo=emp,
                                numero=i,
                                valor=emp.valor_parcela,
                                vencimento=venc,
                                status=p_status,
                                pago_em=pago_em,
                            )
                            parcelas_criadas.append(parcela)

                        # ── 6. Pagamentos para parcelas pagas ─────────────────
                        for parcela in parcelas_criadas:
                            if parcela.status == "paga":
                                pgto = Pagamento.objects.create(
                                    parcela=parcela,
                                    recebido_por=vendedor,
                                    valor=parcela.valor,
                                    forma="dinheiro",
                                )
                                _movimentar(caixa, "entrada", "pagamento", parcela.valor, vendedor,
                                            referencia_pgto=pgto,
                                            descricao=f"Parcela {parcela.numero}/{emp.num_parcelas} — {cliente.nome}")

                        total_emp += 1

        self.stdout.write(f"  → {total_emp} empréstimos criados")

        # ── Resumo final ──────────────────────────────────────────────────────
        self.stdout.write("\n" + "─" * 54)
        self.stdout.write(self.style.SUCCESS("  BANCO POPULADO COM SUCESSO"))
        self.stdout.write("─" * 54)
        self.stdout.write(f"  Empresas:       {Empresa.objects.count()}")
        self.stdout.write(f"  Usuários:       {Usuario.objects.filter(is_superuser=False).count()}")
        self.stdout.write(f"  Rotas:          {Rota.objects.count()}")
        self.stdout.write(f"  Clientes:       {Cliente.objects.count()}")
        self.stdout.write(f"  Empréstimos:    {Emprestimo.objects.count()}")
        self.stdout.write(f"  Parcelas:       {Parcela.objects.count()}")
        self.stdout.write(f"  Pagamentos:     {Pagamento.objects.count()}")
        self.stdout.write(f"  Movimentações:  {MovimentacaoFinanceira.objects.count()}")
        self.stdout.write("")
        self.stdout.write("  CREDENCIAIS DE ACESSO")
        self.stdout.write("  ┌──────────────────────┬──────────────┬────────────┐")
        self.stdout.write("  │ Usuário              │ Perfil       │ Senha      │")
        self.stdout.write("  ├──────────────────────┼──────────────┼────────────┤")
        self.stdout.write("  │ admin                │ Superuser    │ admin123   │")
        self.stdout.write("  │ admin_cf             │ Admin SaaS   │ admin123   │")
        self.stdout.write("  │ gerente_cf           │ Gerente      │ gerente123 │")
        self.stdout.write("  │ vendedor_cf1         │ Vendedor     │ vend123    │")
        self.stdout.write("  │ vendedor_cf2         │ Vendedor     │ vend123    │")
        self.stdout.write("  │ admin_fc             │ Admin SaaS   │ admin123   │")
        self.stdout.write("  │ gerente_fc           │ Gerente      │ gerente123 │")
        self.stdout.write("  │ vendedor_fc1         │ Vendedor     │ vend123    │")
        self.stdout.write("  │ vendedor_fc2         │ Vendedor     │ vend123    │")
        self.stdout.write("  └──────────────────────┴──────────────┴────────────┘")
        self.stdout.write("─" * 54 + "\n")
