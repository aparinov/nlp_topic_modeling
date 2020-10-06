from model_testing import db, auth
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
# from model_testing.database import DataSet, DataFormat
from model_testing.model.data_format import DataFormat
from model_testing.model.data_set import DataSet
from model_testing.model.processing import Processing
from model_testing.model.experiment import Experiment
from model_testing import from_dict
from model_testing.model.exp_result import ExpResult
from model_testing.model.exp_execution import ExpExecution
from model_testing.model.experiment import Experiment
from model_testing.model.enums import ExecutionStatus
from model_testing.model.user import User

result = Blueprint("result", __name__)


@result.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_result():
    res = {"response": []}
    all_exp_res = db.session.query(ExpResult).all()

    for exp_res in all_exp_res:
        res["response"].append(exp_res.to_dict_light())

    return jsonify(res)


@result.route('/get', methods=["GET"])
@auth.login_required()
def get_result():
    to_get = request.json.get('to_get')

    res = {"response": []}

    incomplete_description = {"error": "Request must provide list 'to_get' of objects with 'id'."}
    if to_get:
        for g in to_get:
            id = g['id'] if 'id' in g.keys() else None

            if id is not None:
                try:
                    exp_res = ExpResult.get(id)
                    res["response"].append(exp_res.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if id:
                        err['id'] = id
                    res["response"].append(err)
            else:
                res['response'].append(incomplete_description)
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@result.route('/get_by_user', methods=["GET"])
@auth.login_required()
def get_result_by_user():
    to_get = request.json.get('to_get')
    res = {"response": []}

    incomplete_description = {"error": "Request must provide list 'to_get' of objects with 'user_id' or 'username'."}
    if to_get:
        for g in to_get:
            username = g['username'] if 'username' in g.keys() else None
            user_id = g['user_id'] if 'user_id' in g.keys() else None

            # if (id is not None) or (title is not None):
            try:
                user = User.get(user_id, username)
                user_id = user.id
                exps = db.session.query(Experiment).filter(Experiment.Author == user_id).all()
                local_res = {
                    "user": user.to_dict(),
                    "experiments": []
                }
                for exp in exps:
                    local_res["experiments"].append(exp.to_dict())
                res["response"].append(local_res)
            except Exception as e:
                err = {"error": str(e)}
                if user_id:
                    err['user_id'] = user_id
                if username:
                    err['username'] = username
                res["response"].append(err)
            # else:
            #     res['response'].append(incomplete_description)
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@result.route('/post', methods=["POST"])
@auth.login_required()
def post_result():
    to_post = request.json.get('to_post')
    res = []
    incomplete_description = {"error": "Request must provide list 'to_post' of objects with 'exe_id', 'result'."}

    if to_post:
        for p in to_post:
            exe_id = from_dict(p, 'execution_id')
            result = from_dict(p, 'result')

            try:
                exp_exe = ExpExecution.get(exe_id)
                exp_exe.set_status(ExecutionStatus.finished)

                exp = exp_exe.get_experiment() #Experiment.get(exp_id, None)

                exp_res = ExpResult()
                exp_res.set_experiment(exp)
                exp_res.set_result(result)
                exp_res.set_author(exp_exe.get_author())

                db.session.add(exp_res)
                db.session.commit()
            except Exception as e:
                res.append({"error" : str(e)})
    else:
        res.append(incomplete_description)

    return jsonify({"posted": res})


@result.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_result():
    to_delete = request.json.get('to_delete')
    res = []

    if to_delete:
        for d in to_delete:
            id = from_dict(d, 'id')

            try:
                exp_res = ExpResult.get(id)
                message = exp_res.to_dict_light()
                #
                db.session.delete(exp_res)
                db.session.commit()
                #
                res.append(message)
            except Exception as e:
                err = {"error": str(e)}
                if id:
                    err['id'] = id
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'id'."})

    return jsonify({"deleted": res})
