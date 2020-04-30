import sys
import flask
app = flask.current_app


def get_decision(location, customer_count):
    # TODO: Implement service to get estimated infected number
    #       from location, customer count, etc

    return "For a store in " + location + " with " + str(customer_count) + " customers ==> O]-["


def validate_args(args):
    if args == None:
        return False

    location = args['location']
    customer_count = args['count']

    if location == None or location == "":
        return False

    if customer_count == None or customer_count == "":
        return False

    if not(isinstance(location, str)) or not(customer_count.isdigit()):
        return False

    return True
