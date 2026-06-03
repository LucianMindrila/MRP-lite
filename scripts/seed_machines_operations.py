"""seed_machines_operations.py — Populate machines and operations tables.

Run once after the schema migration. Safe to re-run — skips records that
already exist rather than duplicating them.

Usage:
    python scripts/seed_machines_operations.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app import create_app
from models import db, Machine, Operation

MACHINES = [
    {'name': 'Selco SK4',     'machine_type': 'Beamsaw',         'unit': 'U4'},
    {'name': 'Raptor U4',     'machine_type': 'CNC Router',      'unit': 'U4'},
    {'name': 'Felder',        'machine_type': 'CNC Router',      'unit': 'U4'},
    {'name': 'Raptor U3',     'machine_type': 'CNC Router',      'unit': 'U3'},
    {'name': 'Thermwood 1',   'machine_type': 'CNC Router',      'unit': 'U7'},
    {'name': 'Thermwood 2',   'machine_type': 'CNC Router',      'unit': 'U7'},
    {'name': 'Thermwood 3',   'machine_type': 'CNC Router',      'unit': 'U7'},
    {'name': 'Thermwood 4',   'machine_type': 'CNC Router',      'unit': 'U7'},
    {'name': 'Multicam',      'machine_type': 'CNC Router',      'unit': 'U7'},
    {'name': 'Thermwood 5',   'machine_type': 'CNC Router',      'unit': 'U16'},
    {'name': 'Thermwood 6',   'machine_type': 'CNC Router',      'unit': 'U16'},
    {'name': 'Hurco VMC U4',  'machine_type': 'CNC Milling',     'unit': 'U4'},
    {'name': 'Hurco VMC U7',  'machine_type': 'CNC Milling',     'unit': 'U7'},
    {'name': 'Hurco VMC U16', 'machine_type': 'CNC Milling',     'unit': 'U16'},
    {'name': 'Hurco Lathe',   'machine_type': 'CNC Lathe',       'unit': 'U16'},
    {'name': 'Lotus 1',       'machine_type': 'Laser Engraving', 'unit': 'U7'},
    {'name': 'Lotus 2',       'machine_type': 'Laser Engraving', 'unit': 'U7'},
    {'name': 'Lotus 3',       'machine_type': 'Laser Engraving', 'unit': 'U7'},
    {'name': 'Edgebander',    'machine_type': 'Edgebanding',     'unit': 'U3'},
]

CNC_ROUTERS = [
    'Raptor U4', 'Felder', 'Raptor U3',
    'Thermwood 1', 'Thermwood 2', 'Thermwood 3', 'Thermwood 4',
    'Multicam', 'Thermwood 5', 'Thermwood 6',
]
HURCO_VMC = ['Hurco VMC U4', 'Hurco VMC U7', 'Hurco VMC U16']

OPERATIONS = [
    {
        'name': 'Beamsaw',
        'requires_machine': True,
        'machines': ['Selco SK4'],
    },
    {
        'name': 'Sheet Cutting',
        'requires_machine': True,
        'machines': CNC_ROUTERS,
    },
    {
        'name': 'Face 1',
        'requires_machine': True,
        'machines': CNC_ROUTERS,
    },
    {
        'name': 'Face 2',
        'requires_machine': True,
        'machines': CNC_ROUTERS + HURCO_VMC,  # some products use Hurco for F2
    },
    {
        'name': 'Milling',
        'requires_machine': True,
        'machines': HURCO_VMC,
    },
    {
        'name': 'Lathe',
        'requires_machine': True,
        'machines': ['Hurco Lathe'],
    },
    {
        'name': 'Laser Engraving',
        'requires_machine': True,
        'machines': ['Lotus 1', 'Lotus 2', 'Lotus 3'],
    },
    {
        'name': 'Edgebanding',
        'requires_machine': True,
        'machines': ['Edgebander'],
    },
    {
        'name': 'Assembly',
        'requires_machine': False,
        'machines': [],
    },
    {
        'name': 'Packing',
        'requires_machine': False,
        'machines': [],
    },
    {
        'name': 'Quality Check',
        'requires_machine': False,
        'machines': [],
    },
]


def run():
    app = create_app()
    with app.app_context():
        machine_map = {}

        # Machines
        added_m = 0
        for m in MACHINES:
            existing = Machine.query.filter_by(name=m['name']).first()
            if existing:
                machine_map[m['name']] = existing
            else:
                obj = Machine(name=m['name'], machine_type=m['machine_type'],
                              unit=m['unit'], is_active=True)
                db.session.add(obj)
                db.session.flush()
                machine_map[m['name']] = obj
                added_m += 1

        # Operations + machine links
        added_o = 0
        for o in OPERATIONS:
            existing = Operation.query.filter_by(name=o['name']).first()
            if existing:
                op_obj = existing
            else:
                op_obj = Operation(name=o['name'], requires_machine=o['requires_machine'])
                db.session.add(op_obj)
                db.session.flush()
                added_o += 1

            for mname in o['machines']:
                m_obj = machine_map.get(mname)
                if m_obj and m_obj not in op_obj.eligible_machines:
                    op_obj.eligible_machines.append(m_obj)

        db.session.commit()

        print(f"Machines added : {added_m} (skipped {len(MACHINES) - added_m} already present)")
        print(f"Operations added: {added_o} (skipped {len(OPERATIONS) - added_o} already present)")
        print("Done.")


if __name__ == '__main__':
    run()
