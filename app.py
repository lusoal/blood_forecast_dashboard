#!/usr/bin/python

from flask import (
    Flask,
    render_template,
    # jsonify,
    request,
    # Response,
    redirect,
    url_for,
    session,
)
import logging
import os
import requests
import datetime
import json
import sys

from congito import cognito_auth

app = Flask(__name__)
app.secret_key = "eipohgoo4rai0uf5ie1oshahmaeF"

# Constants
USER_POOL_ID = os.getenv("USER_POOL_ID", "")

APP_CLIENT_ID = os.getenv("APP_CLIENT_ID", "")
APP_CLIENT_SECRET = os.getenv("APP_CLIENT_SECRET", "")

API_GATEWAY_URL_ENDPOINT = os.getenv("API_GATEWAY_URL_ENDPOINT", "")
COGNITO_URL = os.getenv("COGNITO_URL", "")


# Routes of my application
@app.route("/")
def index():
    if not session.get("app_client_id"):
        return redirect(COGNITO_URL, code=302)
    return redirect(url_for("menu"))


@app.route("/login_callback", methods=["GET"])
def login_callback():
    code = request.args.get("code")
    endpoint = (
        "https://blood-analysis-test.auth.us-east-1.amazoncognito.com/oauth2/token"
    )

    headers = {}
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    data = {}
    data["grant_type"] = "authorization_code"
    data["client_id"] = APP_CLIENT_ID
    data["code"] = code
    data["redirect_uri"] = "https://dashboard.lucasduarte.club/login_callback"

    response = requests.post(
        endpoint, headers=headers, data=data, auth=(APP_CLIENT_ID, APP_CLIENT_SECRET)
    )

    # Todo tratar os erros
    response_dict = json.loads(response.text)

    logging.warning(f"Autenticacao retorno {response_dict}")

    session["app_client_id"] = response_dict.get("id_token")
    session["access_token"] = response_dict.get("access_token")
    session[
        "user_id"
    ] = (
        1
    )  # TODO: pegar user_id do cognito, criar atributo obrigatorio chamado device_id

    return redirect(url_for("menu"))


@app.route("/login", methods=["POST"])
def login():
    # session['user_id'] = usuario.id Set Session attribute
    username = request.form["username"]
    password = request.form["password"]
    try:
        app_client_id = cognito_auth.authenticate_and_get_token(
            username, password, USER_POOL_ID, APP_CLIENT_ID
        )

        session["app_client_id"] = app_client_id["IdToken"]
        session["user_id"] = 1

        return redirect(url_for("menu"))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/menu", methods=["GET"])
def menu():
    return render_template("menu.html")


@app.route("/realizar_forecast", methods=["GET"])
def realizar_forecast():
    # TODO: validate response if contains error message
    try:
        headers = {"X-COG-ID": session["app_client_id"]}
        payload = {"user_id": session["user_id"]}
        response = requests.get(
            f"{API_GATEWAY_URL_ENDPOINT}/get_blood_forecast",
            params=payload,
            headers=headers,
        )

        forecast = response.text
        logging.warning(f"Forecast Retorno {forecast}")
        return redirect(url_for("exibir_grafico_forecast", forecast=forecast))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return redirect(url_for("menu"))


@app.route("/exibir_grafico_forecast", methods=["GET", "POST"])
def exibir_grafico_forecast():
    forecast = json.loads(request.args["forecast"])
    list_glicose = []

    time = forecast["time"][1].replace("T", " ")
    time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    day_of_analysis = f"{time.day}/{time.month}/{time.year}"

    for time, glicose in zip(forecast["time"], forecast["glicose"]):
        new_dict = {}

        time = time.replace("T", " ")
        time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        timestamp = int(time.timestamp() * 1000)
        new_dict["x"] = timestamp
        new_dict["y"] = glicose
        list_glicose.append(new_dict)

    glic = list(item["y"] for item in list_glicose)

    glic_min = min(glic)
    glic_max = max(glic)

    return render_template(
        "grafico_forecast.html",
        list_glicose=list_glicose,
        day_of_analysis=day_of_analysis,
        glic_min=glic_min,
        glic_max=glic_max,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
