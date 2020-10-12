from model_testing import db, auth
from flask import request, jsonify, Blueprint, g
from model_testing.model.environment import Environment
from model_testing import from_dict

from model_testing.model.environment import get_cuda_version, \
    get_free_ram, get_free_vram, get_gpus, get_packages, get_architecture


environment = Blueprint("environment" , __name__)


@environment.route('/info', methods=["GET"])
@auth.login_required()
def get_node_environment():
    res = {
        "free_ram_gb" : get_free_ram(),
        "free_vram_gb" : get_free_vram(),
        "py_packages" : get_packages(),
        "gpus" : get_gpus(),
        "cuda_version" : get_cuda_version(),
        "architecture" : get_architecture()
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
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'env_id' or 'name'."}
    if to_get:
        for g in to_get:
            name = from_dict(g, 'name')
            env_id = from_dict(g, 'env_id')

            if (env_id is not None) or (name is not None):
                try:
                    df = Environment.get(env_id, name)
                    res["response"].append(df.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if env_id:
                        err['env_id'] = env_id
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
            env_id = from_dict(u, 'env_id')

            new_name = from_dict(u, 'new_name')
            new_cuda_version = from_dict(u, 'new_cuda_version')
            new_gpu_required = from_dict(u, 'new_gpu_required')
            new_py_dependencies = from_dict(u, 'new_py_dependencies')
            new_architecture = from_dict(u, 'new_architecture')

            try:
                env = Environment.get(env_id, name)

                env.update(new_name, new_cuda_version, new_gpu_required, new_py_dependencies, new_architecture)

                env_id = env.Id
                name = env.name

                db.session.commit()
                res.append(env.to_dict())

            except Exception as e:
                err = {"error": str(e)}
                if env_id:
                    err['env_id'] = env_id
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'env_id' or 'name' "
                             "and data to update ('new_name', 'new_cuda_version', 'new_gpu_required',"
                             " 'new_architecture', 'new_py_dependencies')."})

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
            architecture = from_dict(p, 'architecture')

            try:
                env = Environment.create(name, cuda_version, gpu_required, py_dependencies, architecture, g.user)
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
                             " with 'name', 'cuda_version', 'gpu_required', 'architecture' and 'py_dependencies'."})

    return jsonify({"posted": res})


@environment.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_environment():
    to_delete = request.json.get('to_delete')
    res = []

    if to_delete:
        for d in to_delete:
            name = from_dict(d, 'name')
            env_id = from_dict(d, 'env_id')

            try:
                env = Environment.get(env_id, name)

                env_id = env.id
                name = env.name

                message = Environment.delete(env)
                # db.session.delete(env)
                # db.session.commit()
                # message = env.to_dict()
                res.append(message)
            except Exception as e:
                err = {"error": str(e)}
                if env_id:
                    err['env_id'] = env_id
                if name:
                    err['name'] = name
                res.append(err)

    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'env_id' or 'name'."})

    return jsonify({"deleted": res})