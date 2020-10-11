from model_testing import db, auth
from flask import request, jsonify, Blueprint, g
from model_testing.model.experiment import Experiment
from model_testing.model.exp_execution import ExpExecution
from model_testing import from_dict
from model_testing.model.user import User


experiment = Blueprint("experiment" , __name__)


@experiment.route('/get_all', methods=["GET"])
@auth.login_required()
def get_all_experiment():
    res = {"response": []}
    exps = db.session.query(Experiment).all()

    for exp in exps:
        res["response"].append(exp.to_dict())

    return jsonify(res)


@experiment.route('/get', methods=["GET"])
@auth.login_required()
def get_experiment():
    to_get = request.json.get('to_get')

    res = {"response": []}

    incomplete_description = {"error": "Request must provide list 'to_get' of objects with 'exp_id' or 'title'."}
    if to_get:
        for g in to_get:
            title = from_dict(g, 'title')
            exp_id = from_dict(g, 'exp_id')

            if (exp_id is not None) or (title is not None):
                try:
                    exp = Experiment.get(exp_id, title)
                    res["response"].append(exp.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if exp_id:
                        err['exp_id'] = exp_id
                    if title:
                        err['title'] = title
                    res["response"].append(err)
            else:
                res['response'].append(incomplete_description)
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@experiment.route('/get_by_user', methods=["GET"])
@auth.login_required()
def get_experiment_by_user():
    to_get = request.json.get('to_get')
    res = {"response": []}

    incomplete_description = {"error": "Request must provide list 'to_get' of objects with 'user_id' or 'username'."}
    if to_get:
        for g in to_get:
            username = from_dict(g, 'username')
            user_id = from_dict(g, 'user_id')

            try:
                user = User.get(user_id, username)
                user_id = user.id
                exps = db.session.query(Experiment).filter(Experiment.author == user_id).all()
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
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@experiment.route('/update', methods=["PATCH"])
@auth.login_required()
def upd_experiment():
    to_update = request.json.get('to_update')
    res = []

    if to_update:
        for u in to_update:
            title = from_dict(u, 'title')
            exp_id = from_dict(u, 'exp_id')

            new_title = from_dict(u, 'new_title')
            short_title = from_dict(u, 'new_short_title')
            comment = from_dict(u, 'new_comment')
            baseline = from_dict(u, 'new_baseline')

            processing_arr = from_dict(u, 'new_processing_arr')
            res_format_id = from_dict(u, 'new_res_format_id')
            res_format_name = from_dict(u, 'new_res_format_name')
            dataset_id = from_dict(u, 'new_dataset_id')
            dataset_title = from_dict(u, 'new_dataset_title')

            try:
                exp = Experiment.get(exp_id, title)
                exp.update(new_title, short_title, comment, processing_arr, baseline, res_format_id, res_format_name,
                           dataset_id, dataset_title)
                db.session.commit()
                res.append(exp.to_dict())
            except Exception as e:
                err = {"error": str(e)}
                if exp_id:
                    err['exp_id'] = exp_id
                if title:
                    err['title'] = title
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_update' of objects with 'exp_id' or 'title' "
                             "and data to update ('new_title', 'new_short_title', 'new_comment', 'new_baseline', "
                             "'processing_arr', 'new_format_id', 'new_format_name',"
                             " 'new_dataset_id', 'new_dataset_title')."})

    return jsonify({"updated": res})


@experiment.route('/post', methods=["POST"])
@auth.login_required()
def post_experiment():
    to_post = request.json.get('to_post')
    res = []
    incomplete_description = {"error": "Request must provide list 'to_post' of objects"
                                       " with 'title', 'res_format_id' ( or 'res_format_name'), 'dataset_id'"
                                       " ( or 'dataset_title'), 'short_title', 'comment', 'baseline', 'processing_arr'."}
    if to_post:
        for p in to_post:
            title = from_dict(p, 'title')

            short_title = from_dict(p, 'short_title')
            comment = from_dict(p, 'comment')
            baseline = from_dict(p, 'baseline')
            processing_arr = from_dict(p, 'processing_arr')

            res_format_id = from_dict(p, 'res_format_id')
            res_format_name = from_dict(p, 'res_format_name')

            dataset_id = from_dict(p, 'dataset_id')
            dataset_title = from_dict(p, 'dataset_title')

            full = all([x is not None for x in [title, short_title, comment, baseline, processing_arr]] +
                       [(res_format_id is not None) or (res_format_name is not None),
                        (dataset_id is not None) or (dataset_title is not None)])

            if full:
                try:
                    exp = Experiment.create(title, short_title, comment, processing_arr, baseline,
                                            res_format_id, res_format_name, dataset_id, dataset_title, g.user)
                    db.session.add(exp)
                    db.session.commit()
                    res.append(exp.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if title:
                        err['title'] = title
                    res.append(err)
            else:
                res.append(incomplete_description)
    else:
        res.append(incomplete_description)

    return jsonify({"posted": res})


@experiment.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_experiment():
    to_delete = request.json.get('to_delete')
    res = []

    if to_delete:
        for d in to_delete:
            title = from_dict(d, 'title')
            exp_id = from_dict(d, 'exp_id')

            try:
                exp = Experiment.get(id, title)
                message = Experiment.delete(exp)
                # message = exp.to_dict()
                #
                # db.session.delete(exp)
                # db.session.commit()

                res.append(message)
            except Exception as e:
                err = {"error": str(e)}
                if exp_id:
                    err['exp_id'] = exp_id
                if title:
                    err['title'] = title
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_delete' of objects with 'exp_id' or 'title'."})

    return jsonify({"deleted": res})


@experiment.route('/run', methods=["POST"])
@auth.login_required
def run():
    to_run = request.json.get('to_run')
    res = []
    args_message = "'args' (optional) is an array of strings of arguments to" \
                           " corresponding preprocessing stages."

    if to_run:
        for r in to_run:
            title = from_dict(r, 'title')
            exp_id = from_dict(r, 'exp_id')
            delayed = from_dict(r, 'delayed')
            args = from_dict(r, 'args')

            try:
                exp = Experiment.get(exp_id, title)
                # TODO: Test
                if g.user.exp_admin_rights or (exp.Author == g.user):

                    if args and (type(args) is list):
                        for a in args:
                            if type(a) is not str:
                                raise Exception(args_message)
                    elif args and (type(args) is not list):
                        raise Exception(args_message)

                    message = exp.run(delayed, args, g.user)
                else:
                    raise Exception("Only Experiment Admin can run someone else's experiment.")
                res.append(message)
            except Exception as e:
                err = {"error": str(e)}
                if exp_id:
                    err['exp_id'] = exp_id
                if title:
                    err['title'] = title
                res.append(err)
    else:
        res.append({"error": "Request must provide list 'to_run' of objects with 'exp_id' or 'title'. "
                             "'delayed' and 'args' are optional. "
                             "The time of delayed task start should be a string in the format: "
                             "'Year-Month-Day Hour:Minute:Second'. "
                             "'args' is an array of strings of arguments to corresponding preprocessing stages."})

    return jsonify({"started": res})


@experiment.route('/monitoring', methods=["GET"])
@auth.login_required
def monitoring():
    res = []
    to_monitor = request.json.get('to_monitor')

    if to_monitor:
        for m in to_monitor:
            exe_id = from_dict(m, 'exe_id')
            try:
                exp_exe = ExpExecution.get(exe_id)
                res.append(exp_exe.to_dict())
            except Exception as e:
                res.append({"error": str(e)})
    else:
        res.append({"error": "Request must provide list 'to_monitor' of objects with 'exe_id'."})

    return jsonify({"started": res})


@experiment.route('/cancel', methods=["DELETE"])
@auth.login_required
def cancel():
    res = []
    to_cancel = request.json.get('to_cancel')

    if to_cancel:
        for c in to_cancel:
            exe_id = from_dict(c, 'exe_id')
            try:
                exp_exe = ExpExecution.get(exe_id)
                exp_exe.cancel()
                res.append(exp_exe.to_dict())
            except Exception as e:
                res.append({"error": str(e)})
    else:
        res.append({"error": "Request must provide list 'to_monitor' of objects with 'exe_id'."})

    return jsonify({"canceled": res})