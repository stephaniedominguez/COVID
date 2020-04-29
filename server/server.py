from flask import Flask
app = Flask(__name__)

# Import controller
import src.controller as ctr

# Initiate root url
@app.route("/")
def hello(): 
    return "Lumiata COVID-19 Global Hackaton"

# Bind other url
app.add_url_rule('/decision', view_func=ctr.get_decision)

# TODO: Probably start scheduling here??

# Run application
app.run(host='0.0.0.0', port=8018)