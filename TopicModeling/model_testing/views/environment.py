from model_testing import db, auth
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
# from database import session as s
# from model_testing.database import DataFormat
from model_testing.model.environment import Environment
from model_testing.model.data_set import DataSet
from model_testing import from_dict

from model_testing.model.environment import get_cuda_version, get_free_ram, get_free_vram, get_gpus, get_packages


environment = Blueprint("environment" , __name__)


@environment.route('/info', methods=["GET"])
@auth.login_required()
def get_node_environment():
    res = {
        "free_ram_gb" : get_free_ram(),
        "free_vram_gb" : get_free_vram(),
        "py_packages" : get_packages(),
        "gpus" : get_gpus(),
        "cuda_version" : get_cuda_version()
    }
    return jsonify(res)


@environment.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_environment():
    res = {"response": []}
    dfs = db.session.query(Environment).all()
    for df in dfs:
        res["response"].append(df.to_dict())
    return jsonify(res)


@environment.route('/get', methods=["GET"])
@auth.login_required()
def get_environment():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'id' or 'name'."}
    if to_get:
        for g in to_get:
            name = g['name'] if 'name' in g.keys() else None
            id = g['id'] if 'id' in g.keys() else None

            if (id is not None) or (name is not None):
                try:
                    df = Environment.get(id, name)
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


@environment.route('/update', methods=["PATCH"])
@auth.login_required()
def upd_environment():
    to_update = request.json.get('to_update')
    res = []

    if to_update:
        for u in to_update:
            name = from_dict(u, 'name')
            id = from_dict(u, 'id')

            new_name = from_dict(u, 'new_name')
            new_cuda_version = from_dict(u, 'new_cuda_version')
            new_gpu_required = from_dict(u, 'new_gpu_required')
            new_py_dependencies = from_dict(u, 'new_py_dependencies')

            try:
                env = Environment.get(id, name)

                env.update(new_name, new_cuda_version, new_gpu_required, new_py_dependencies)

                id = env.Id
                name = env.name

                db.session.commit()
                res.append(env.to_dict())

            except Exception as e:
                err = {"error": str(e)}
                if id:
                    err['id'] = id
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'id' or 'name' "
                             "and data to update ('new_name', 'new_cuda_version', 'new_gpu_required',"
                             " 'new_py_dependencies')."})

    return jsonify({"updated": res})


@environment.route('/post', methods=["POST"])
@auth.login_required()
def post_environment():
    to_post = request.json.get('to_post')
    res = []

    if to_post:
        for p in to_post:
            name = from_dict(p, 'name')
            cuda_version = from_dict(p, 'cuda_version')
            gpu_required = from_dict(p, 'gpu_required')
            py_dependencies = from_dict(p, 'py_dependencies')

            try:
                env = Environment.create(name, cuda_version, gpu_required, py_dependencies, g.user)
                db.session.add(env)
                db.session.commit()
                res.append(env.to_dict())
            except Exception as e:
                err = {"error": str(e)}
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_post' of objects"
                             " with 'name', 'cuda_version', 'gpu_required' and 'py_dependencies'."})

    return jsonify({"posted": res})


@environment.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_environment():
    to_delete = request.json.get('to_delete')
    res = []

    if to_delete:
        for d in to_delete:
            name = from_dict(d, 'name')
            id = from_dict(d, 'id')

            try:
                env = Environment.get(id, name)

                id = env.Id
                name = env.name

                db.session.delete(env)
                db.session.commit()
                res.append(env.to_dict())
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