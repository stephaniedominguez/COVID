import flask
import src.service as service

def get_decision():
    # Prepare response
    data = {"success": False}

    # Retrieve input arguments
    args = flask.request.args

    # Validate input
    if not service.validate_args(args):
        return flask.jsonify(data)
        
    location = args['location']
    customer_count = int(args['count'])

    # Get decision based on the arguments
    decision = service.get_decision(location, customer_count)

    # Create success response
    data["decision"] = decision
    data["success"] = True

    return flask.jsonify(data)