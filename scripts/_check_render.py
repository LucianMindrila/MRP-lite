import sys
sys.path.insert(0, '.')
from app import create_app
from models import User

app = create_app()
with app.test_client() as c:
    with app.app_context():
        u = User.query.filter_by(username='admin').first()
        with c.session_transaction() as sess:
            sess['_user_id'] = str(u.id)
            sess['_fresh'] = True
    r = c.get('/inventory/materials/68/edit')
    html = r.data.decode('utf-8')
    idx = html.find('bom_status')
    if idx == -1:
        print('bom_status NOT FOUND in rendered HTML')
    else:
        print('FOUND. Surrounding HTML:')
        print(html[max(0, idx-100):idx+500])
