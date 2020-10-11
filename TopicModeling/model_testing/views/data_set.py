from model_testing import db, auth
from flask import request, jsonify, Blueprint, g
from model_testing.model.data_set import DataSet
from model_testing import from_dict


data_set = Blueprint("data_set" , __name__)


@data_set.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_dataset():
    res = {"response": []}
    dss = db.session.query(DataSet).all()

    for ds in dss:
        res["response"].append(ds.to_dict_light())

    return jsonify(res)


@data_set.route('/get', methods=["GET"])
@auth.login_required()
def get_dataset():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'id' or 'name'."}
    if to_get:
        for g in to_get:
            name = from_dict(g, 'name')
            id = from_dict(g, 'id')

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
            dataset_id = from_dict(u, 'dataset_id')

            new_title = from_dict(u, 'new_title')
            new_format_name = from_dict(u, 'new_format_name')
            new_format_id = from_dict(u, 'new_format_id')
            new_uri = from_dict(u, 'new_uri')

            try:
                ds = DataSet.get(dataset_id, title)
                ds.update(new_title, new_uri, new_format_id, new_format_name)

                dataset_id = ds.Id
                title = ds.Title

                db.session.commit()
                res.append(ds.to_dict_light())
            except Exception as e:
                err = {"error": str(e)}
                if dataset_id:
                    err['dataset_id'] = dataset_id
                if title:
                    err['title'] = title
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'dataset_id' or 'title' "
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
                ds = DataSet.create(title, uri, format_id, format_name, g.user)
                db.session.add(ds)
                db.session.commit()

                res.append(ds.to_dict_light())
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
            title = from_dict(d, 'title')
            dataset_id = from_dict(d, 'dataset_id')

            try:
                ds = DataSet.get(dataset_id, title)

                dataset_id = ds.Id
                title = ds.Title

                db.session.delete(ds)
                db.session.commit()
                res.append(ds.to_dict_light())
            except Exception as e:
                err = {"error": str(e)}
                if dataset_id:
                    err['dataset_id'] = dataset_id
                if title:
                    err['title'] = title
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'dataset_id' or 'title'."})

    return jsonify({"deleted": res})