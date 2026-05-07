from models import db, User, Supplier, Material, Product, BOMItem, Customer

def register_seed_command(app):
    @app.cli.command()
    def seed():
        db.drop_all()
        db.create_all()

        # Users
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        op = User(username='operator', email='operator@example.com', role='operator')
        op.set_password('operator123')
        db.session.add(op)

        # Suppliers
        s1 = Supplier(name='Egger UK', contact='Sales', email='sales@egger.com', phone='01234 567890', lead_time_days=5)
        s2 = Supplier(name='Hafele', contact='Trade Counter', email='trade@hafele.co.uk', phone='01788 123456', lead_time_days=3)
        s3 = Supplier(name='Titus Fixing', contact='Sales', email='sales@titus.com', phone='01234 000000', lead_time_days=7)
        db.session.add_all([s1, s2, s3])
        db.session.flush()

        # Materials
        m1 = Material(code='EG-18-OAK', name='Egger 18mm Oak MFC Sheet', unit='sheet',
                      stock_qty=20, reorder_point=5, reorder_qty=10, cost_price=45.00,
                      supplier_id=s1.id, location='Bay A1')
        m2 = Material(code='EG-18-WHT', name='Egger 18mm White MFC Sheet', unit='sheet',
                      stock_qty=15, reorder_point=5, reorder_qty=10, cost_price=38.00,
                      supplier_id=s1.id, location='Bay A2')
        m3 = Material(code='HF-HINGE', name='Hafele Soft-Close Hinge (pair)', unit='pcs',
                      stock_qty=100, reorder_point=20, reorder_qty=50, cost_price=3.50,
                      supplier_id=s2.id, location='Bay B1')
        m4 = Material(code='HF-RUNNER', name='Hafele Drawer Runner 500mm (pair)', unit='pcs',
                      stock_qty=40, reorder_point=10, reorder_qty=20, cost_price=8.00,
                      supplier_id=s2.id, location='Bay B2')
        m5 = Material(code='TT-CAM', name='Titus Cam & Bolt Connector', unit='pcs',
                      stock_qty=200, reorder_point=50, reorder_qty=100, cost_price=0.40,
                      supplier_id=s3.id, location='Bay C1')
        db.session.add_all([m1, m2, m3, m4, m5])
        db.session.flush()

        # Products
        p1 = Product(code='CAB-BASE-600', name='600mm Base Cabinet', unit='pcs',
                     sale_price=180.00, lead_time_days=3)
        p2 = Product(code='CAB-WALL-600', name='600mm Wall Cabinet', unit='pcs',
                     sale_price=140.00, lead_time_days=2)
        db.session.add_all([p1, p2])
        db.session.flush()

        # BOM
        db.session.add_all([
            BOMItem(product_id=p1.id, material_id=m1.id, qty_per_unit=2.0),
            BOMItem(product_id=p1.id, material_id=m3.id, qty_per_unit=2.0),
            BOMItem(product_id=p1.id, material_id=m4.id, qty_per_unit=1.0),
            BOMItem(product_id=p1.id, material_id=m5.id, qty_per_unit=8.0),
            BOMItem(product_id=p2.id, material_id=m2.id, qty_per_unit=1.5),
            BOMItem(product_id=p2.id, material_id=m3.id, qty_per_unit=2.0),
            BOMItem(product_id=p2.id, material_id=m5.id, qty_per_unit=6.0),
        ])

        # Customers
        c1 = Customer(name='Smith Joinery Ltd', contact='John Smith',
                      email='john@smithjoinery.co.uk', phone='07700 000001',
                      address='10 Industrial Estate, Birmingham, B1 1AA')
        c2 = Customer(name='Green Kitchens', contact='Sarah Green',
                      email='sarah@greenkitchens.co.uk', phone='07700 000002',
                      address='5 Trade Park, Manchester, M1 1BB')
        db.session.add_all([c1, c2])

        db.session.commit()
        print('Database seeded successfully.')
        print('Admin login: admin / admin123')
        print('Operator login: operator / operator123')
