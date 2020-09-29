from model_testing import db, auth
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
# from model_testing.database import DataSet, DataFormat
from model_testing.model.data_format import DataFormat
from model_testing.model.data_set import DataSet
from model_testing.model.processing import Processing
from model_testing import from_dict

# from model_testing.workers import add

processing = Blueprint("processing" , __name__)


@processing.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_processing():
    res = {"response": []}
    ps = db.session.query(Processing).all()

    for p in ps:
        res["response"].append(p.to_dict())

    return jsonify(res)


@processing.route('/get', methods=["GET"])
@auth.login_required()
def get_processing():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error": "Request must provide list 'to_get' of objects with 'id' or 'name'."}
    if to_get:
        for g in to_get:
            name = from_dict(g, 'name')
            id = from_dict(g, 'id')

            if (id is not None) or (name is not None):
                try:
                    proc = Processing.get(id, name)
                    res["response"].append(proc.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if id:
                        err['id'] = id
                    if name:
                        err['username'] = name
                    res["response"].append(err)
            else:
                res['response'].append(incomplete_description)
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@processing.route('/update', methods=["PATCH"])
@auth.login_required()
def upd_processing():
    to_update = request.json.get('to_update')
    res = []

    if to_update:
        for u in to_update:
            name = from_dict(u, 'name')
            id = from_dict(u, 'id')

            new_name = from_dict(u, 'new_name')

            new_input_id = from_dict(u, 'new_input_id')
            new_input_name = from_dict(u, 'new_input_name')

            new_output_id = from_dict(u, 'new_output_id')
            new_output_name = from_dict(u, 'new_output_name')

            new_source_uri = from_dict(u, 'new_source_uri')

            new_lang_name = from_dict(u, 'new_lang_name')
            new_args = from_dict(u, 'new_args')

            try:
                proc = Processing.get(id, name)
                proc.update(new_name, new_input_id, new_input_name, new_output_id, new_output_name,
                            new_source_uri, new_lang_name, new_args)
                db.session.commit()
                res.append(proc.to_dict())
            except Exception as e:
                err = {"error": str(e)}
                if id:
                    err['id'] = id
                if name:
                    err['name'] = name
                res.append(err)
    #
    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'id' or 'name' "
                             "and data to update ('new_name', 'new_input_id', 'new_input_name', 'new_output_id',"
                             " 'new_output_name', 'new_source_uri', 'new_lang_name', 'new_args')."})

    return jsonify({"updated": res})


@processing.route('/post', methods=["POST"])
@auth.login_required()
def post_processing():
    to_post = request.json.get('to_post')
    res = []
    incomplete_description = {"error": "Request must provide list 'to_post' of objects"
                                       " with 'name', 'input_id' ( or 'input_name'), 'output_id'"
                                       " ( or 'output_name'), 'source_uri', 'lang_name', 'args'."}
    if to_post:
        for p in to_post:
            name = from_dict(p, 'name')

            input_id = from_dict(p, 'input_id')
            input_name = from_dict(p, 'input_name')

            output_id = from_dict(p, 'output_id')
            output_name = from_dict(p, 'output_name')

            source_uri = from_dict(p, 'source_uri')

            lang_name = from_dict(p, 'lang_name')
            args = from_dict(p, 'args')

            full = all([x is not None for x in [name, source_uri, lang_name, args]] +
                       [(input_id is not None) or (input_name is not None),
                        (output_id is not None) or (output_name is not None)])

            # from flask import current_app
            # current_app.logger.info(full)

            if full:
                try:
                    proc = Processing.create(name, input_id, input_name, output_id, output_name, source_uri, lang_name, args)
                    db.session.add(proc)
                    db.session.commit()
                    res.append(proc.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if name:
                        err['name'] = name
                    res.append(err)
            else:
                res.append(incomplete_description)
    else:
        res.append(incomplete_description)

    return jsonify({"posted": res})


@processing.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_processing():
    to_delete = request.json.get('to_delete')
    res = []

    if to_delete:
        for d in to_delete:
            name = d['name'] if 'name' in d.keys() else None
            id = d['id'] if 'id' in d.keys() else None

            try:
                p = Processing.get(id, name)
                message = p.to_dict()

                db.session.delete(p)
                db.session.commit()

                res.append(message)
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


@processing.route('/run', methods=["POST"])
@auth.login_required
def run():
    id = request.json.get('id')
    name = request.json.get('name')

    proc = Processing.get(id, name)
    proc.run()

    return jsonify({})