import sys
import flask
app = flask.current_app


def get_decision(fips):
    # TODO: Implement service to get estimated infected number
    #       from location, customer count, etc

    return "For a store in " + fips + " ==> O]-["


def validate_args(args):
    if args == None:
        return False

    fips = args['fips']

    if fips == None or fips == "":
        return False

    if not(isinstance(fips, str)):
        return False

    return True
