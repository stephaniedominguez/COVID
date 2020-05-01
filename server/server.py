from flask import Flask, render_template
import src.model_service as service

app = Flask(__name__)

# Import controller
import src.controller as ctr
import src.ui_controller as ui

# Initiate root url
@app.route("/")
def hello( ): 
    return render_template("index.html", template_folder='template') 

# Bind service url
app.add_url_rule('/decision', view_func=ctr.get_decision)

# Bind ui url
app.add_url_rule('/map/', view_func=ui.map)

# Setup model
service.prepare_model()

# Run application
app.run(host='0.0.0.0', port=8018)