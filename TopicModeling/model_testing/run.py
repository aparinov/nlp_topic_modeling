import os.path
import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from model_testing import create_app, db
from model_testing import celery, init_celery
from model_testing.config import ADMIN_NAME, ADMIN_PASS


app = create_app()
init_celery(app, celery)

with app.app_context():
    from model_testing.model.user import User
    if User.query.filter_by(username = ADMIN_NAME).first() is None:
        u = User(username = ADMIN_NAME, admin_rights=True, exp_admin_rights=True)
        u.hash_password(ADMIN_PASS)
        db.session.add(u)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)