from model_testing import db, auth
from flask import request, jsonify, Blueprint, g
from model_testing.model.processing import Processing
from model_testing import from_dict


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
    incomplete_description = {"error": "Request must provide list 'to_get' of objects with 'processing_id' or 'name'."}
    if to_get:
        for g in to_get:
            name = from_dict(g, 'name')
            processing_id = from_dict(g, 'processing_id')

            if (processing_id is not None) or (name is not None):
                try:
                    proc = Processing.get(processing_id, name)
                    res["response"].append(proc.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if processing_id:
                        err['processing_id'] = processing_id
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
            processing_id = from_dict(u, 'processing_id')

            new_name = from_dict(u, 'new_name')

            new_input_id = from_dict(u, 'new_input_id')
            new_input_name = from_dict(u, 'new_input_name')

            new_output_id = from_dict(u, 'new_output_id')
            new_output_name = from_dict(u, 'new_output_name')

            new_source_uri = from_dict(u, 'new_source_uri')

            new_lang_name = from_dict(u, 'new_lang_name')
            # new_args = from_dict(u, 'new_args')

            new_env_id = from_dict(u, 'new_env_id')
            new_env_name = from_dict(u, 'new_env_name')

            new_status_name = from_dict(u, 'new_status_name')

            try:
                proc = Processing.get(processing_id, name)
                proc.update(new_name, new_input_id, new_input_name, new_output_id, new_output_name,
                            new_source_uri, new_lang_name, new_env_id, new_env_name, new_status_name)
                db.session.commit()
                res.append(proc.to_dict())
            except Exception as e:
                err = {"error": str(e)}
                if processing_id:
                    err['processing_id'] = processing_id
                if name:
                    err['name'] = name
                res.append(err)
    #
    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'processing_id' or 'name' "
                             "and data to update ('new_name', 'new_input_id', 'new_input_name', 'new_output_id',"
                             " 'new_output_name', 'new_source_uri', 'new_lang_name', 'new_status_name')."})

    return jsonify({"updated": res})


@processing.route('/post', methods=["POST"])
@auth.login_required()
def post_processing():
    to_post = request.json.get('to_post')
    res = []
    incomplete_description = {"error": "Request must provide list 'to_post' of objects"
                                       " with 'name', 'input_id' ( or 'input_name'), 'output_id'"
                                       " ( or 'output_name'), 'env_id' ( or 'env_name'),"
                                       " 'source_uri', 'lang_name'."}
    if to_post:
        for p in to_post:
            name = from_dict(p, 'name')

            input_id = from_dict(p, 'input_id')
            input_name = from_dict(p, 'input_name')

            output_id = from_dict(p, 'output_id')
            output_name = from_dict(p, 'output_name')

            source_uri = from_dict(p, 'source_uri')

            lang_name = from_dict(p, 'lang_name')
            # args_info = from_dict(p, 'args_info')

            env_id = from_dict(p, 'env_id')
            env_name = from_dict(p, 'env_name')

            status_name = from_dict(p, 'status_name')

            full = all([x is not None for x in [name, source_uri, lang_name, status_name]] +
                       [(input_id is not None) or (input_name is not None),
                        (output_id is not None) or (output_name is not None),
                        (env_id is not None) or (env_name is not None)])
            from flask import current_app

            if full:
                try:
                    proc = Processing.create(name, input_id, input_name, output_id, output_name,
                                             source_uri, lang_name, env_id, env_name, status_name, g.user)
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
            name = from_dict(d, 'name')
            processing_id = from_dict(d, 'processing_id')

            try:
                p = Processing.get(processing_id, name)
                message = Processing.delete(p)
                # message = p.to_dict()
                #
                # db.session.delete(p)
                # db.session.commit()

                res.append(message)
            except Exception as e:
                err = {"error": str(e)}
                if processing_id:
                    err['processing_id'] = processing_id
                if name:
                    err['name'] = name
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'processing_id' or 'name'."})

    return jsonify({"deleted": res})


@processing.route('/run', methods=["POST"])
@auth.login_required
def run():
    processing_id = request.json.get('processing_id')
    name = request.json.get('name')

    proc = Processing.get(processing_id, name)
    proc.run()

    return jsonify({})