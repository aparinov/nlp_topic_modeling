from model_testing import db, auth

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from flask import current_app


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column("id" ,db.Integer, primary_key = True, autoincrement=True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))
    admin_rights = db.Column(db.Boolean, default=False)
    exp_admin_rights = db.Column(db.Boolean, default=False)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'user_id': self.id })

    @staticmethod
    def create(username, password, admin_rights, exp_admin_rights):
        user = User()
        user.set_username(username)
        user.set_password(password)
        user.set_admin_rights(admin_rights)
        user.set_exp_admin_rights(exp_admin_rights)
        return user

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['user_id'])
        return user

    @staticmethod
    def get(user_id, username):
        err = "The request must provide 'user_id' or 'username' of the sole Data Format record."
        us = []

        if username:
            us.append(db.session.query(User).filter(User.username == username).first())
        if user_id:
            us.append(db.session.query(User).filter(User.id == user_id).first())
        us = list(filter(lambda x: x is not None, us))

        if len(us) == 0:
            raise Exception("No such User.")
        elif len(us) == 1:
            if us[0]:
                return us[0]
            else:
                raise Exception(err)
        else:
            if us[0] == us[1]:
                return us[0]
            else:
                raise Exception(err)

    @staticmethod
    def delete(user):
        from model_testing.model.base_entity import BaseEntity

        if user is None:
            return None
        user = db.session.query(User).filter(User.id == user.id).first()
        if not user:
            return None

        res = { "user_id": user.id }
        dependent = db.session.query(BaseEntity).filter(BaseEntity.author == user.id).all()
        if dependent:
            res["dependent"] = []
            for dep in dependent:
                dep_res = BaseEntity.delete(dep)
                if dep_res:
                    res["dependent"].append(dep_res)

        db.session.delete(user)
        db.session.commit()
        return res

    def set_username(self, username):
        if not username:
            raise Exception("No username provided.")
        if type(username) != str:
            raise Exception("Username must be string.")
        if len(username) == 0:
            raise Exception("Username cannot be empty string.")
        user = db.session.query(User).filter(User.username == username).first()
        if user:
            raise Exception("Username must be unique.")
        self.username = username

    def set_password(self, password):
        if password is None:
            raise Exception("No password provided.")
        if type(password) != str:
            raise Exception("Password must be string.")
        if len(password) == 0:
            raise Exception("Password cannot be empty string.")
        self.hash_password(password)

    def set_admin_rights(self, admin_rights):
        if admin_rights is None:
            raise Exception("No 'admin_rights' flag provided provided.")
        if type(admin_rights) != bool:
            raise Exception("'admin_rights' flag must be boolean.")
        self.admin_rights = admin_rights

    def set_exp_admin_rights(self, exp_admin_rights):
        if exp_admin_rights is None:
            raise Exception("No 'exp_admin_rights' flag provided provided.")
        if type(exp_admin_rights) != bool:
            raise Exception("'exp_admin_rights' flag must be boolean.")
        self.exp_admin_rights = exp_admin_rights

    def update(self, username, password, admin_rights, exp_admin_rights):
        if self.username != username:
            self.set_username(username)
        if password:
            self.set_password()
        if admin_rights:
            self.set_admin_rights(admin_rights)
        if exp_admin_rights:
            self.set_exp_admin_rights(exp_admin_rights)

    def hash_password(self, password):
        self.password_hash = custom_app_context.encrypt(password)

    def verify_password(self, password):
        return custom_app_context.verify(password, self.password_hash)

    def to_dict(self):
        return {
           "user_id" : self.id,
           "username": self.username,
           "admin_rights": self.admin_rights,
           "exp_admin_rights": self.exp_admin_rights
       }