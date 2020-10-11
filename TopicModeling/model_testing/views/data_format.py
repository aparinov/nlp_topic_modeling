from model_testing import db, auth
from flask import request, jsonify, Blueprint, g
from model_testing.model.data_format import DataFormat
from model_testing import from_dict


data_format = Blueprint("data_format" , __name__)


@data_format.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_dataformat():
    res = {"response": []}
    dfs = db.session.query(DataFormat).all()
    for df in dfs:
        res["response"].append(df.to_dict())
    return jsonify(res)


@data_format.route('/get', methods=["GET"])
@auth.login_required()
def get_dataformat():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'dataformat_id' or 'name'."}
    if to_get:
        for g in to_get:
            name = from_dict(g, 'name')
            dataformat_id = from_dict(g, 'dataformat_id')

            if (dataformat_id is not None) or (name is not None):
                try:
                    df = DataFormat.get(dataformat_id, name)
                    res["response"].append(df.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if dataformat_id:
                        err['dataformat_id'] = dataformat_id
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
            dataformat_id = from_dict(u, 'dataformat_id')
            new_name = from_dict(u, 'new_name')
            new_format = from_dict(u, 'new_file_format')
            new_schema_uri = from_dict(u, 'new_schema_uri')
            try:
                df = DataFormat.get(dataformat_id, name)

                df.update(new_name, new_format, new_schema_uri)

                dataformat_id = df.id
                name = df.name

                db.session.commit()
                res.append(df.to_dict())

            except Exception as e:
                err = {"error": str(e)}
                if dataformat_id:
                    err['dataformat_id'] = dataformat_id
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'dataformat_id' or 'name' "
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
                df = DataFormat.create(name, format, schema_uri, g.user)
                db.session.add(df)
                db.session.commit()
                res.append(df.to_dict())
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
            dataformat_id = from_dict(d, 'dataformat_id')

            try:
                df = DataFormat.get(dataformat_id, name)

                dataformat_id = df.id
                name = df.name
                message = DataFormat.delete(df)

                # db.session.delete(df)
                # db.session.commit()
                # message = df.to_dict()
                res.append(message)
            except Exception as e:
                err = {"error": str(e)}
                if dataformat_id:
                    err['dataformat_id'] = dataformat_id
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'dataformat_id' or 'name'."})

    return jsonify({"deleted": res})