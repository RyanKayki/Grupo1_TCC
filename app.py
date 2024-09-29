import subprocess
import sys
from flask import Flask
import os

from adm.adm import adm_blueprint
from connection.connection import connection_blueprint
from func.func import func_blueprint
from tec.tec import tec_blueprint
from session.session import session_blueprint

app = Flask(__name__)
app.secret_key = "TCC"

# Registering the blueprints
app.register_blueprint(adm_blueprint)
app.register_blueprint(connection_blueprint)
app.register_blueprint(func_blueprint)
app.register_blueprint(tec_blueprint)
app.register_blueprint(session_blueprint)

if __name__ == "__main__":
    app.run(debug=True)
