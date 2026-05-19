import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()

with app.app_context():
    from models import db, Material, Supplier, Category

    allcap = Supplier.query.filter_by(name='Allcap').first()
    cat = Category.query.filter_by(name='Ironmongery and Fixings').first()

    items = [
        # Quote 83352 - S/S screws
        ('30SPCM05006',        'M5 X 6 S/S Pozi CSK Screws A2',              0.0235),
        ('30SPPM050008',       'M5 X 8 S/S Pozi Pan Screws',                 0.0330),
        ('30SPCM05008',        'M5 X 8 S/S Pozi CSK Screws A2',              0.0240),
        ('30SPCM05010',        'M5 X 10 S/S Pozi CSK Screws',                0.0225),
        ('30SPCM05020',        'M5 X 20 S/S Pozi CSK Machine Screw A2',      0.0350),
        ('30SPCM05025',        'M5 X 25 S/S Pozi CSK Screws A2',             0.0370),
        ('30SPCM05030',        'M5 X 30 S/S Pozi CSK Screws',                0.0494),
        ('30SPCM05035',        'M5 X 35 S/S Pozi CSK Screws',                0.0555),
        ('30SPPM060016',       'M6 X 16 S/S Pozi Pan Screws',                0.0543),
        ('30SPCM06030',        'M6 X 30 S/S Pozi CSK Screws',                0.0906),
        # Quote 83401 - BZP machine screws, nuts, washers
        ('05ZM05SQ-562',       'M5 Square Nuts BZP DIN562',                  0.0180),
        ('05ZM05',             'M5 Full Nuts BZP',                           0.0074),
        ('05ZM06',             'M6 Full Nuts BZP',                           0.0105),
        ('05ZM06W',            'M6 Wing Nuts BZP',                           0.0830),
        ('05ZM08',             'M8 Full Nuts BZP',                           0.0168),
        ('06ZM06C',            'M6 Form C Washers BZP',                      0.0142),
        ('06ZM06SS',           'M6 Square Section Spring Washers BZP',       0.0070),
        ('10M06016',           'M6 X 16 Socket Cap Screws',                  0.0305),
        ('12M06030',           'M6 X 30 CSK Socket Screws',                  0.0528),
        ('12SM06025',          'M6 X 25 CSK Socket Screws S/S A2',           0.0629),
        ('12ZM05010',          'M5 X 10 CSK Socket Screws BZP',              0.0300),
        ('12ZM05025',          'M5 X 25 CSK Socket Screws BZP',              0.0428),
        ('13SM05014',          'M5 X 14 S/S Socket Button Screws',           0.0387),
        ('13ZM05008',          'M5 X 8 Socket Buttonhead Screws BZP',        0.0372),
        ('30ZPCKM05006',       'M5 X 6 Pozi CSK Machine Screws BZP',         0.0235),
        ('30ZPCKM05008',       'M5 X 8 Pozi CSK Machine Screws BZP',         0.0240),
        ('30ZPCKM05010',       'M5 X 10 Pozi CSK Machine Screws BZP',        0.0209),
        ('30ZPCKM05020',       'M5 X 20 Pozi CSK Machine Screws BZP',        0.0215),
        ('30ZPCKM05025',       'M5 X 25 Pozi CSK Machine Screws BZP',        0.0238),
        ('30ZPCKM05030',       'M5 X 30 Pozi CSK Machine Screws BZP',        0.0286),
        ('30ZPCKM05035',       'M5 X 35 Pozi CSK Machine Screws BZP',        0.0376),
        ('30ZPCKM06030',       'M6 X 30 Pozi CSK Machine Screws BZP',        0.0321),
        ('30ZPCKM06040',       'M6 X 40 Pozi CSK Machine Screws BZP',        0.0413),
        ('30ZPPM05008',        'M5 X 8 Pozi Pan Machine Screws BZP',         0.0173),
        ('30ZPPM06016',        'M6 X 16 Pozi Pan Machine Screws BZP',        0.0297),
        ('30ZSCKM05010',       'M5 X 10 Slotted CSK Machine Screws BZP',     0.0168),
        ('31ZPCK03.5016',      '3.5 X 16mm Pozi CSK Vortex Woodscrews',      0.0196),
        ('31ZPCK03.5035',      '3.5 X 35mm Pozi CSK Velocity Woodscrews',    0.0144),
        ('32ZPF06075',         '6 X 3/4" Pozi Flange Self Tapping Screws BZP', 0.0091),
        ('32ZPF08100',         '8 X 1" Pozi Flange Self Tapping Screws BZP', 0.0138),
        ('32ZPCK06037',        '6 X 3/8" Pozi CSK Self Tapping Screws BZP',  0.0145),
        ('32ZPP10075',         '10 X 3/4" Pozi Pan Self Tapping Screws BZP', 0.0275),
    ]

    added = 0
    skipped = 0
    for code, name, price in items:
        if Material.query.filter_by(code=code).first():
            print(f'  Skip (exists): {code}')
            skipped += 1
        else:
            m = Material(code=code, name=name, cost_price=price, unit='pcs',
                         supplier_id=allcap.id, category_id=cat.id,
                         stock_qty=0, reorder_point=0, reorder_qty=0)
            db.session.add(m)
            print(f'  Added: {code} — {name} @ £{price}')
            added += 1

    db.session.commit()
    print(f'\nDone. Added {added}, skipped {skipped}.')
