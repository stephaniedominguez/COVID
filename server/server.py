from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "COVID-19 Hackaton"

@app.route("/get/decision")
def getDecision():
    return "decision"

app.run(host='0.0.0.0', port=8018)