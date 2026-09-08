# CONTRU ESTOQUE - Seed Data
from datetime import datetime, timezone, timedelta
from database import (
    SessionLocal, init_db, Role, User, Category, Location, Unit, 
    Product, Stock, Price, StockMovement, PriceHistory, 
    Inventory, InventoryItem, PDVIntegration, AuditLog
)

def populate_database():
    init_db()
    db = SessionLocal()
    if db.query(Product).count() > 0:
        print('Banco de dados ja possui registros cadastrados.')
        db.close()
        return

    print('Iniciando injecao de dados demonstrativos do CONTRU ESTOQUE...')
    now = datetime.now(timezone.utc)

    # 1. UNIDADES
    units = [
        ('UN', 'Unidade'), ('M', 'Metro Linear'), ('M2', 'Metro Quadrado'),
        ('KG', 'Quilograma'), ('CX', 'Caixa'), ('SC', 'Saco'),
        ('L', 'Litro'), ('PC', 'Peca'), ('RL', 'Rolo')
    ]
    unit_map = {}
    for code, name in units:
        u = Unit(code=code, name=name)
        db.add(u)
        db.flush()
        unit_map[code] = u.id

    # 2. PERFIS E USUARIOS
    roles = [
        ('admin', 'Administrador', 'Acesso irrestrito a todo o sistema e auditoria.', ['all']),
        ('manager', 'Gestor', 'Visualizacao de indicadores, precos e relatorios.', ['view_dashboard', 'view_stock', 'view_reports', 'view_prices', 'edit_prices', 'view_movements']),
        ('stockist', 'Estoquista', 'Execucao de entradas, saidas, ajustes e inventario.', ['view_stock', 'register_entry', 'register_exit', 'adjust_stock', 'inventory']),
        ('viewer', 'Consulta', 'Acesso apenas de leitura para conferencia.', ['view_stock', 'view_items']),
        ('financial', 'Financeiro', 'Gestao de custos, precos de venda e valor de estoque.', ['view_stock', 'view_prices', 'edit_prices', 'view_reports', 'view_valuation'])
    ]
    role_map = {}
    for r_name, d_name, desc, perms in roles:
        r = Role(name=r_name, display_name=d_name, description=desc, permissions=perms)
        db.add(r)
        db.flush()
        role_map[r_name] = r.id

    users = [
        ('Carlos Silva', 'carlos.admin@contruestoque.com.br', 'admin', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&auto=format&fit=crop&q=80'),
        ('Mariana Souza', 'mariana.gestora@contruestoque.com.br', 'manager', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80'),
        ('Roberto Santos', 'roberto.estoque@contruestoque.com.br', 'stockist', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80'),
        ('Juliana Lima', 'juliana.consulta@contruestoque.com.br', 'viewer', 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&auto=format&fit=crop&q=80'),
        ('Fernando Rocha', 'fernando.financeiro@contruestoque.com.br', 'financial', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80')
    ]
    user_map = {}
    for u_name, email, r_name, avatar in users:
        u = User(name=u_name, email=email, role_id=role_map[r_name], avatar=avatar)
        db.add(u)
        db.flush()
        user_map[r_name] = u

    # 3. CATEGORIAS E LOCAIS
    categories = [
        ('Materiais de Inclusao e Acessibilidade', 'Pisos tateis, barras de apoio e braille', 'accessibility'),
        ('Alvenaria e Argamassas', 'Cimentos, blocos e argamassas colantes', 'brick-wall'),
        ('Hidraulica e Tubulacoes', 'Tubos PVC, conexoes e registros', 'droplet'),
        ('Eletrica e Iluminacao', 'Cabos flexiveis, disjuntores e luminarias', 'zap'),
        ('Tintas e Impermeabilizantes', 'Tintas acrilicas e mantas liquidas', 'paint-bucket'),
        ('EPIs e Seguranca do Trabalho', 'Capacetes, oculos e luvas de protecao', 'shield-check'),
        ('Ferramentas e Fixacao', 'Trenas, parafusos e brocas videa', 'wrench')
    ]
    cat_map = {}
    for c_name, desc, icon in categories:
        c = Category(name=c_name, description=desc, icon=icon)
        db.add(c)
        db.flush()
        cat_map[c_name] = c.id

    locations = [
        ('Almoxarifado Central - Prat. A1', 'Almoxarifado', 'Setor de acessibilidade e inclusao'),
        ('Almoxarifado Central - Prat. B2', 'Almoxarifado', 'Eletrica e fixadores'),
        ('Deposito Geral - Galpao 01', 'Deposito', 'Cimentos, argamassas e tintas'),
        ('Deposito Geral - Galpao 02', 'Deposito', 'Tubos e conexoes'),
        ('Loja Principal - Balcao', 'Loja', 'Exposicao e mostruario'),
        ('Armario EPIs - Seguranca', 'Armario', 'Equipamentos individuais')
    ]
    loc_map = {}
    for l_name, l_type, desc in locations:
        loc = Location(name=l_name, type=l_type, description=desc)
        db.add(loc)
        db.flush()
        loc_map[l_name] = loc.id

    # 4. ITENS DO CATALOGO
    products_seed = [
        # Inclusao e Acessibilidade (Foco Inicial)
        ('INC-101', 'Piso Tatil Direcional 25x25cm Amarelo', 'Piso podotatil de concreto para orientacao visual NBR 9050.', 'Materiais de Inclusao e Acessibilidade', 'Pisos Tateis', 'M2', 'Almoxarifado Central - Prat. A1', 30.0, 150.0, 85.0, 42.00, 68.50, '7891010001015', 'https://images.unsplash.com/photo-1590069261209-f8e9b8642343?w=400&auto=format&fit=crop&q=80'),
        ('INC-102', 'Piso Tatil Alerta 25x25cm Amarelo', 'Piso podotatil de alerta para indicacao de obstaculos e travessias NBR 9050.', 'Materiais de Inclusao e Acessibilidade', 'Pisos Tateis', 'M2', 'Almoxarifado Central - Prat. A1', 30.0, 150.0, 18.0, 44.50, 72.00, '7891010001022', 'https://images.unsplash.com/photo-1590069261209-f8e9b8642343?w=400&auto=format&fit=crop&q=80'),
        ('INC-103', 'Barra de Apoio Reta Inox 304 Polido 80cm', 'Barra de apoio para sanitarios acessiveis em aco inox com flanges.', 'Materiais de Inclusao e Acessibilidade', 'Barras de Apoio', 'UN', 'Almoxarifado Central - Prat. A1', 15.0, 60.0, 34.0, 78.90, 129.90, '7891010001039', 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=400&auto=format&fit=crop&q=80'),
        ('INC-104', 'Barra de Apoio Articulada Sanitarios Inox 70cm', 'Barra articulada com trava de seguranca para transferencia lateral.', 'Materiais de Inclusao e Acessibilidade', 'Barras de Apoio', 'UN', 'Almoxarifado Central - Prat. A1', 8.0, 30.0, 0.0, 185.00, 298.00, '7891010001046', 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=400&auto=format&fit=crop&q=80'),
        ('INC-105', 'Placa de Sinalizacao Braille Sanitario Acessivel', 'Placa de sinalizacao visual e tatil em braille padrao ABNT.', 'Materiais de Inclusao e Acessibilidade', 'Sinalizacao', 'PC', 'Almoxarifado Central - Prat. A1', 12.0, 50.0, 6.0, 22.00, 39.90, '7891010001053', 'https://images.unsplash.com/photo-1572945550744-57049dcbc1b3?w=400&auto=format&fit=crop&q=80'),
        ('INC-106', 'Fita Adesiva Antiderrapante Fotoluminescente 50mmx15m', 'Fita de alta aderencia para rampas e degraus com efeito fotoluminescente.', 'Materiais de Inclusao e Acessibilidade', 'Seguranca e Rampas', 'RL', 'Almoxarifado Central - Prat. A1', 10.0, 40.0, 25.0, 38.00, 65.00, '7891010001060', 'https://images.unsplash.com/photo-1607613009820-a29f7bb81c04?w=400&auto=format&fit=crop&q=80'),

        # Alvenaria e Estrutura
        ('ALV-201', 'Cimento Portland CP II-F-32 Saco 50kg Votoran', 'Cimento de alta versatilidade para fundacoes, lajes e assentamentos.', 'Alvenaria e Argamassas', 'Cimentos', 'SC', 'Deposito Geral - Galpao 01', 50.0, 300.0, 160.0, 31.50, 42.90, '7892010002012', 'https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=400&auto=format&fit=crop&q=80'),
        ('ALV-202', 'Argamassa Colante AC-III Branca 20kg Quartzolit', 'Argamassa para assentamento de porcelanatos e grandes formatos.', 'Alvenaria e Argamassas', 'Argamassas', 'SC', 'Deposito Geral - Galpao 01', 40.0, 200.0, 28.0, 27.80, 44.50, '7892010002029', 'https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=400&auto=format&fit=crop&q=80'),
        ('ALV-203', 'Bloco Ceramico de Vedacao 9x19x19cm 8 Furos', 'Tijolo ceramico para alvenaria de vedacao.', 'Alvenaria e Argamassas', 'Tijolos', 'UN', 'Deposito Geral - Galpao 01', 500.0, 3000.0, 1400.0, 1.15, 1.85, '7892010002036', 'https://images.unsplash.com/photo-1590069261209-f8e9b8642343?w=400&auto=format&fit=crop&q=80'),
        ('ALV-204', 'Barra de Aco Nervurado CA-50 10mm 12m Gerdau', 'Vergalhao de aco para estruturas de concreto armado.', 'Alvenaria e Argamassas', 'Aco', 'PC', 'Deposito Geral - Galpao 01', 40.0, 180.0, 95.0, 48.00, 74.00, '7892010002043', 'https://images.unsplash.com/photo-1504917599217-d4dc5ebe6122?w=400&auto=format&fit=crop&q=80'),

        # Hidraulica
        ('HID-301', 'Tubo PVC Soldavel Marrom 25mm 3/4 pol 6m Tigre', 'Tubo para conducao de agua fria predial junta soldavel.', 'Hidraulica e Tubulacoes', 'Agua Fria', 'PC', 'Deposito Geral - Galpao 02', 25.0, 120.0, 68.0, 18.20, 29.90, '7893010003019', 'https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?w=400&auto=format&fit=crop&q=80'),
        ('HID-302', 'Tubo PVC Esgoto Serie Normal 100mm 6m Amanco', 'Tubo para instalacoes prediais de esgoto e ventilacao.', 'Hidraulica e Tubulacoes', 'Esgoto', 'PC', 'Deposito Geral - Galpao 02', 15.0, 80.0, 42.0, 41.50, 66.00, '7893010003026', 'https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?w=400&auto=format&fit=crop&q=80'),
        ('HID-303', 'Registro de Gaveta Bruto 3/4 pol Docol', 'Registro de bloqueio em latao para agua potavel.', 'Hidraulica e Tubulacoes', 'Registros', 'UN', 'Loja Principal - Balcao', 10.0, 50.0, 0.0, 36.40, 59.90, '7893010003033', 'https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&auto=format&fit=crop&q=80'),
        ('HID-304', 'Caixa Sifonada PVC com Grelha Redonda Branca 100x100x50mm', 'Caixa para escoamento e sifonamento de banheiros.', 'Hidraulica e Tubulacoes', 'Ralos', 'UN', 'Deposito Geral - Galpao 02', 15.0, 70.0, 35.0, 14.80, 25.50, '7893010003040', 'https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&auto=format&fit=crop&q=80'),

        # Eletrica
        ('ELE-401', 'Cabo Flexivel 2.5mm 750V Azul 100m Sil Fios', 'Condutor flexivel de cobre eletrolitico para tomadas e neutro.', 'Eletrica e Iluminacao', 'Cabos', 'RL', 'Almoxarifado Central - Prat. B2', 10.0, 50.0, 22.0, 135.00, 219.00, '7894010004016', 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&auto=format&fit=crop&q=80'),
        ('ELE-402', 'Cabo Flexivel 4.0mm 750V Vermelho 100m Sil Fios', 'Condutor para circuitos especiais e chuveiros.', 'Eletrica e Iluminacao', 'Cabos', 'RL', 'Almoxarifado Central - Prat. B2', 8.0, 40.0, 4.0, 210.00, 329.00, '7894010004023', 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&auto=format&fit=crop&q=80'),
        ('ELE-403', 'Disjuntor Termomagnetico Bipolar 32A Curva C Steck', 'Protecao contra sobrecargas eletricas em quadros de distribuicao.', 'Eletrica e Iluminacao', 'Protecao', 'UN', 'Almoxarifado Central - Prat. B2', 12.0, 60.0, 29.0, 28.50, 46.90, '7894010004030', 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&auto=format&fit=crop&q=80'),
        ('ELE-404', 'Painel Plafon LED Sobrepor Quadrado 24W 6500K', 'Luminaria bivolt de alto rendimento luminoso para escritorios e galpoes.', 'Eletrica e Iluminacao', 'Luminarias', 'UN', 'Loja Principal - Balcao', 15.0, 75.0, 48.0, 24.00, 42.00, '7894010004047', 'https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=400&auto=format&fit=crop&q=80'),

        # Tintas
        ('TIN-501', 'Tinta Acrilica Fosca Standard Branco Neve Lata 18L Suvinil', 'Tinta lavavel com alto rendimento para acabamento fino.', 'Tintas e Impermeabilizantes', 'Tintas', 'L', 'Deposito Geral - Galpao 01', 10.0, 50.0, 24.0, 245.00, 389.00, '7895010005013', 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&auto=format&fit=crop&q=80'),
        ('TIN-502', 'Impermeabilizante Manta Liquida Branca Balde 18kg Vedacit', 'Protecao elastica contra infiltracoes em lajes e coberturas.', 'Tintas e Impermeabilizantes', 'Impermeabilizantes', 'SC', 'Deposito Geral - Galpao 01', 8.0, 40.0, 15.0, 182.00, 279.00, '7895010005020', 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&auto=format&fit=crop&q=80'),

        # EPIs
        ('EPI-601', 'Capacete de Seguranca Classe B com Jugular Amarelo 3M', 'Capacete para protecao craniana com CA ativo e jugular textil.', 'EPIs e Seguranca do Trabalho', 'Cabeca', 'UN', 'Armario EPIs - Seguranca', 20.0, 100.0, 55.0, 19.50, 34.90, '7896010006010', 'https://images.unsplash.com/photo-1508873696983-2df5293cb32b?w=400&auto=format&fit=crop&q=80'),
        ('EPI-602', 'Oculos de Protecao Ampla Visao Antirrisco Danny', 'Oculos de seguranca para protecao ocular durante perfuracoes.', 'EPIs e Seguranca do Trabalho', 'Olhos', 'UN', 'Armario EPIs - Seguranca', 25.0, 120.0, 12.0, 8.40, 16.50, '7896010006027', 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=400&auto=format&fit=crop&q=80'),
        ('EPI-603', 'Luva de Protecao Mecanica Pigmentada Algodao Par', 'Luva para manuseio de blocos, vergalhoes e materiais abrasivos.', 'EPIs e Seguranca do Trabalho', 'Maos', 'UN', 'Armario EPIs - Seguranca', 50.0, 300.0, 180.0, 3.80, 7.50, '7896010006034', 'https://images.unsplash.com/photo-1584634731339-252c581abfc5?w=400&auto=format&fit=crop&q=80'),

        # Ferramentas
        ('FIX-701', 'Trena Metrica Emborrachada com Trava 8m Lufkin', 'Trena de medicao com estojo emborrachado e fita larga.', 'Ferramentas e Fixacao', 'Medicao', 'UN', 'Loja Principal - Balcao', 10.0, 50.0, 32.0, 28.00, 49.00, '7897010007017', 'https://images.unsplash.com/photo-1508873696983-2df5293cb32b?w=400&auto=format&fit=crop&q=80'),
        ('FIX-702', 'Parafuso Sextavado com Bucha Nylon 8mm Caixa 100un', 'Fixadores zincados de alta resistencia para alvenaria.', 'Ferramentas e Fixacao', 'Fixadores', 'CX', 'Almoxarifado Central - Prat. B2', 15.0, 80.0, 46.0, 22.50, 38.00, '7897010007024', 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&auto=format&fit=crop&q=80'),
        ('FIX-703', 'Broca Videa Concreto SDS Plus 8x160mm Irwin', 'Broca de metal duro para perfuracao de alvenaria e vigas.', 'Ferramentas e Fixacao', 'Brocas', 'UN', 'Loja Principal - Balcao', 10.0, 40.0, 0.0, 14.50, 26.90, '7897010007031', 'https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&auto=format&fit=crop&q=80')
    ]

    product_records = []
    for code, name, desc, cat_n, subcat, unit_c, loc_n, min_s, max_s, init_s, cost_p, sale_p, pdv_c, img_url in products_seed:
        p = Product(
            code=code, name=name, description=desc,
            category_id=cat_map[cat_n], subcategory=subcat,
            unit_id=unit_map[unit_c], location_id=loc_map[loc_n],
            min_stock=min_s, max_stock=max_s,
            image_url=img_url, pdv_code=pdv_c,
            is_active=True, created_at=now - timedelta(days=60)
        )
        db.add(p)
        db.flush()

        st = Stock(product_id=p.id, quantity=init_s, updated_at=now)
        db.add(st)
        pr = Price(product_id=p.id, cost_price=cost_p, sale_price=sale_p, updated_at=now)
        db.add(pr)

        product_records.append((p, init_s, cost_p, sale_p))

    # 5. HISTORICO DE MOVIMENTACOES PREGRESSAS
    roberto = user_map['stockist']
    mariana = user_map['manager']

    for idx, (p, init_s, cost_p, sale_p) in enumerate(product_records):
        # Entrada inicial 25 dias atras
        m1 = StockMovement(
            product_id=p.id,
            movement_type='ENTRADA',
            quantity=init_s + 20.0,
            previous_balance=0.0,
            new_balance=init_s + 20.0,
            unit_price=cost_p,
            total_value=round((init_s + 20.0) * cost_p, 2),
            user_id=roberto.id,
            user_name=roberto.name,
            origin_destination='Fornecedor Oficial Brasil Ltda',
            document_ref=f'NF-e 2026/{1000 + idx}',
            reason_notes='Entrada de estoque inicial e compras programadas.',
            created_at=now - timedelta(days=25)
        )
        db.add(m1)

        # Saida 8 dias atras (se saldo permitir)
        if init_s > 5:
            m2 = StockMovement(
                product_id=p.id,
                movement_type='SAIDA',
                quantity=20.0,
                previous_balance=init_s + 20.0,
                new_balance=init_s,
                unit_price=cost_p,
                total_value=round(20.0 * cost_p, 2),
                user_id=roberto.id,
                user_name=roberto.name,
                origin_destination='Obra Acessibilidade Parque das Arvores',
                document_ref=f'REQ-OBRA-{200 + idx}',
                reason_notes='Atendimento de requisicao de materiais da frente de obras.',
                created_at=now - timedelta(days=8)
            )
            db.add(m2)

    # 6. HISTORICO DE PRECOS
    price_changes = [
        ('INC-101', 38.00, 42.00, 59.90, 68.50, 'Reajuste do fabricante de artefatos podotateis.'),
        ('INC-103', 72.00, 78.90, 115.00, 129.90, 'Variacao na cotacao de aco inoxidavel 304 NBR 9050.'),
        ('ALV-201', 28.90, 31.50, 38.50, 42.90, 'Reajuste nacional da industria de cimento.'),
        ('ELE-401', 118.00, 135.00, 189.00, 219.00, 'Alta no preco de cotacao internacional do cobre.')
    ]
    for code, old_c, new_c, old_s, new_s, reason in price_changes:
        prod = next(p for p, _, _, _ in product_records if p.code == code)
        ph = PriceHistory(
            product_id=prod.id,
            previous_cost_price=old_c,
            new_cost_price=new_c,
            previous_sale_price=old_s,
            new_sale_price=new_s,
            reason=reason,
            user_id=mariana.id,
            user_name=mariana.name,
            created_at=now - timedelta(days=6)
        )
        db.add(ph)

    # 7. INVENTARIO CONCLUIDO COM DIVERGENCIA
    inv = Inventory(
        code='INV-2026-001',
        title='Inventario Trimestral - Materiais de Acessibilidade',
        type='CATEGORIA',
        category_id=cat_map['Materiais de Inclusao e Acessibilidade'],
        status='FINALIZADO',
        notes='Auditoria e contagem fisica de rotina.',
        user_id=mariana.id,
        user_name=mariana.name,
        started_at=now - timedelta(days=12),
        completed_at=now - timedelta(days=11),
        created_at=now - timedelta(days=12)
    )
    db.add(inv)
    db.flush()

    for p, init_s, cost_p, sale_p in product_records[:6]:
        diff = -2.0 if p.code == 'INC-102' else 0.0
        counted = init_s + diff
        inv_item = InventoryItem(
            inventory_id=inv.id,
            product_id=p.id,
            system_quantity=init_s,
            counted_quantity=counted,
            diff_quantity=diff,
            diff_percent=round((diff / init_s * 100) if init_s > 0 else 0.0, 2),
            cost_price=cost_p,
            diff_value=round(diff * cost_p, 2),
            notes='Pecas danificadas em transporte' if diff != 0 else 'Contagem 100% conforme.'
        )
        db.add(inv_item)

    # 8. INTEGRACAO PDV
    pdv = PDVIntegration(
        pdv_system_name='CONTRU PDV - Frente de Caixa',
        status='AGUARDANDO_CONEXAO',
        api_endpoint='/api/pdv/sync',
        webhook_url='https://api.contruestoque.com.br/v1/webhooks/pdv',
        config_json={
            'version': '2.0.4',
            'protocol': 'REST/JSON',
            'auto_deduct_stock': True
        },
        last_sync_at=now - timedelta(hours=4),
        pending_items_count=0,
        pending_movements_count=0
    )
    db.add(pdv)

    # 9. LOG DE AUDITORIA INICIAL
    admin = user_map['admin']
    db.add(AuditLog(
        user_id=admin.id,
        user_name=admin.name,
        action='INICIALIZACAO_SISTEMA',
        entity_type='System',
        entity_id='1',
        description='Base de dados populada com 26 materiais de construcao e inclusao.',
        before_data=None,
        after_data={'total_materiais': len(product_records), 'status': 'ativo'},
        created_at=now - timedelta(days=30)
    ))

    db.commit()
    db.close()
    print('Base de dados demonstrativa populada com sucesso!')

if __name__ == '__main__':
    populate_database()
