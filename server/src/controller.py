from flask import request
import src.model_service as service

def get_decision():
    # Retrieve input arguments
    args = request.args
    location = args['location']
    customer_count = args['count']

    # TODO: Validate input

    # Get decision based on the arguments
    decision = service.get_decision(location, customer_count)

    return decision