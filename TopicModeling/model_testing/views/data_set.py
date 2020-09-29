from model_testing import db, auth
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
# from model_testing.database import DataSet, DataFormat
from model_testing.model.data_format import DataFormat
from model_testing.model.data_set import DataSet
from model_testing import from_dict

data_set = Blueprint("data_set" , __name__)


@data_set.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_dataset():
    res = {"response": []}
    dss = db.session.query(DataSet).all()

    for ds in dss:
        res["response"].append(ds.to_dict())

    return jsonify(res)


@data_set.route('/get', methods=["GET"])
@auth.login_required()
def get_dataset():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'id' or 'name'."}
    if to_get:
        for g in to_get:
            name = g['name'] if 'name' in g.keys() else None
            id = g['id'] if 'id' in g.keys() else None

            if (id is not None) or (name is not None):
                try:
                    ds = DataSet.get(id, name)
                    res["response"].append(ds.to_dict())
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


@data_set.route('/update', methods=["PATCH"])
@auth.login_required()
def upd_dataset():
    to_update = request.json.get('to_update')
    res = []

    if to_update:
        for u in to_update:
            title = from_dict(u, 'title')
            id = from_dict(u, 'id')

            new_title = from_dict(u, 'new_title')
            new_format_name = from_dict(u, 'new_format_name')
            new_format_id = from_dict(u, 'new_format_id')
            new_uri = from_dict(u, 'new_uri')

            try:
                ds = DataSet.get(id, title)
                ds.update(new_title, new_uri, new_format_id, new_format_name)

                id = ds.Id
                title = ds.Title
                # format = df.format
                # schema = df.schema

                db.session.commit()
                res.append({"id": id, "title": title})#, "format": format, "schema":schema})
            except Exception as e:
                err = {"error": str(e)}
                if id:
                    err['id'] = id
                if title:
                    err['title'] = title
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'id' or 'title' "
                             "and data to update ('new_title', 'new_format_name', 'new_format_id', 'new_uri')."})

    return jsonify({"updated": res})


@data_set.route('/post', methods=["POST"])
@auth.login_required()
def post_dataset():
    to_post = request.json.get('to_post')
    res = []

    if to_post:
        for p in to_post:
            title = from_dict(p, 'title')
            format_name = from_dict(p, 'format_name')
            format_id = from_dict(p, 'format_id')
            uri = from_dict(p, 'uri')

            try:
                ds = DataSet.create(title, uri, format_id, format_name)
                db.session.add(ds)
                db.session.commit()
                id = ds.Id
                title = ds.Title
                res.append({"id": id, "name": title})
            except Exception as e:
                err = {"error": str(e)}
                if title:
                    err['title'] = title
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_post' of objects"
                             " with 'title', 'uri' and 'format_name' (or 'format_id')."})

    return jsonify({"posted": res})


@data_set.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_dataset():
    to_delete = request.json.get('to_delete')
    res = []

    if to_delete:
        for d in to_delete:
            title = d['title'] if 'title' in d.keys() else None
            id = d['id'] if 'id' in d.keys() else None

            try:
                ds = DataSet.get(id, title)

                id = ds.Id
                title = ds.Title

                db.session.delete(ds)
                db.session.commit()
                res.append({"id": id, "title": title})
            except Exception as e:
                err = {"error": str(e)}
                if id:
                    err['id'] = id
                if title:
                    err['title'] = title
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'id' or 'title'."})

    return jsonify({"deleted": res})