from model_testing import db, auth
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
# from database import session as s
# from model_testing.database import DataFormat
from model_testing.model.data_format import DataFormat
from model_testing.model.data_set import DataSet
from model_testing import from_dict

data_format = Blueprint("data_format" , __name__)


@data_format.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_dataformat():
    res = {"response": []}
    dfs = db.session.query(DataFormat).all()
    # from model_testing.database import DataFormats
    for df in dfs:
        res["response"].append(df.to_dict())
    return jsonify(res)


@data_format.route('/get', methods=["GET"])
@auth.login_required()
def get_dataformat():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'id' or 'name'."}
    if to_get:
        for g in to_get:
            name = g['name'] if 'name' in g.keys() else None
            id = g['id'] if 'id' in g.keys() else None

            if (id is not None) or (name is not None):
                try:
                    df = DataFormat.get(id, name)
                    res["response"].append(df.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if id:
                        err['id'] = id
                    if name:
                        err['name'] = name
                    res["response"].append(err)
            else:
                res['response'].append(incomplete_description)
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@data_format.route('/update', methods=["PATCH"])
@auth.login_required()
def upd_dataformat():
    to_update = request.json.get('to_update')
    res = []

    if to_update:
        for u in to_update:
            name = from_dict(u, 'name')
            id = from_dict(u, 'id')
            new_name = from_dict(u, 'new_name')
            new_format = from_dict(u, 'new_file_format')
            new_schema_uri = from_dict(u, 'new_schema_uri')
            try:
                df = DataFormat.get(id, name)

                df.update_dataformat(new_name, new_format, new_schema_uri)

                id = df.Id
                name = df.name
                format = df.format
                schema = df.schema

                db.session.commit()
                res.append({"id": id, "name": name, "format": format, "schema":schema})

            except Exception as e:
                err = {"error": str(e)}
                if id:
                    err['id'] = id
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'id' or 'name' "
                             "and data to update ('new_name','new_file_format','new_schema_uri')."})

    return jsonify({"updated": res})


@data_format.route('/post', methods=["POST"])
@auth.login_required()
def post_dataformat():
    to_post = request.json.get('to_post')
    res = []

    if to_post:
        for p in to_post:
            name = from_dict(p, 'name')
            format = from_dict(p, 'file_format')
            schema_uri = from_dict(p, 'schema_uri')

            try:
                df = DataFormat.create(name, format, schema_uri)
                db.session.add(df)
                db.session.commit()
                id = df.Id
                name = df.name
                res.append({"id": id, "name": name})
            except Exception as e:
                err = {"error": str(e)}
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_post' of objects"
                             " with 'name', 'file_format' and 'schema_uri'."})

    return jsonify({"posted": res})


@data_format.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_dataformat():
    to_delete = request.json.get('to_delete')
    res = []

    if to_delete:
        for d in to_delete:
            name = from_dict(d, 'name')
            id = from_dict(d, 'id')

            try:
                df = DataFormat.get(id, name)

                id = df.Id
                name = df.name

                db.session.delete(df)
                db.session.commit()
                res.append({"id": id, "name": name})
            except Exception as e:
                err = {"error": str(e)}
                if id:
                    err['id'] = id
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'id' or 'name'."})

    return jsonify({"deleted": res})