from flask import request, jsonify, Blueprint, g
from model_testing import from_dict
from model_testing import db, auth
from model_testing.model.user import User


user_bp = Blueprint("user", __name__)


@user_bp.route('/get_all', methods=["GET"])
def get_all_user():
    users = []
    for u in User.query.all():
        users.append(u.to_dict())

    return {"response":users}


@user_bp.route('/get', methods=["GET"])
def get_user():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'user_id' or 'username'."}
    if to_get:
        for g in to_get:
            username = from_dict(g, 'username')
            user_id = from_dict(g, 'user_id')

            try:
                us = User.get(user_id, username)
                res["response"].append(us.to_dict())
            except Exception as e:
                err = {"error": str(e)}
                if user_id:
                    err['user_id'] = user_id
                if username:
                    err['username'] = username
                    res["response"].append(err)
                else:
                    res['response'].append(incomplete_description)
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@user_bp.route('/post', methods=["POST"])
@auth.login_required
def create_user():
    to_post = request.json.get('to_post')
    res = {"posted" : []}

    if not g.user.admin_rights:
        res["posted"].append({"error" : "Permission required! Only administrator can create users."})
    elif to_post:
        for c in to_post:
            try:
                username = from_dict(c, 'username')
                password = from_dict(c, 'password')
                admin_rights = from_dict(c, 'admin_rights')
                exp_admin_rights = from_dict(c, 'exp_admin_rights')

                user = User.create(username, password, admin_rights, exp_admin_rights)

                db.session.add(user)
                db.session.commit()
                message = user.to_dict()
            except Exception as e:
                message = {"error" : str(e)}
            res["posted"].append(message)
    else:
        res["posted"].append({"error" : "Request must provide 'to_post' array of objects with 'username', "
                                        "'password', 'admin_rights', 'exp_admin_rights' fields."})
    return jsonify(res)


@user_bp.route('/update', methods=["PATCH"])
@auth.login_required
def update_user():
    to_update = request.json.get('to_update')
    res = {"updated" : []}

    if not g.user.admin_rights:
        res["updated"].append({"error" : "Permission required! Only administrator can update users."})
    elif to_update:
        for u in to_update:
            try:
                user_id = from_dict(u, 'user_id')
                username = from_dict(u, 'username')
                new_username = from_dict(u, 'new_username')
                new_password = from_dict(u, 'new_password')
                new_admin_rights = from_dict(u, 'new_admin_rights')
                new_exp_admin_rights = from_dict(u, 'new_exp_admin_rights')

                user = User.get(user_id, username)
                user.update(new_username, new_password, new_admin_rights, new_exp_admin_rights)

                db.session.commit()
                message = user.to_dict()
                res["updated"].append(message)
            except Exception as e:
                res["updated"].append({"error": str(e)})

    else:
        res["updated"].append({"error" : "Request must provide 'to_update' array of objects with 'username' "
                                         "(or 'user_id'), 'new_password', 'new_admin_rights',"
                                         " 'new_exp_admin_rights' fields."})
    return jsonify(res)


@user_bp.route('/delete', methods=["DELETE"])
@auth.login_required
def delete_user():
    to_delete = request.json.get('to_delete')
    res = {"deleted":[]}

    if not g.user.admin_rights:
        res["deleted"].append({"error" : "Permission required! Only administrator can delete users."})
    elif to_delete:
        for d in to_delete:
            try:
                username = from_dict(d, 'username')
                user_id = from_dict(d, 'user_id')

                user = User.get(user_id, username)
                message = User.delete(user)
                # db.session.delete(user)
                # db.session.commit()
                #
                # message = user.to_dict()
            except Exception as e:
                message = {"error" : str(e)}
            res["deleted"].append(message)
    else:
        res["deleted"].append({"error" : "Request must provide to_delete array of objects with 'username' field."})

    return jsonify(res)


@user_bp.route('/get_token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })