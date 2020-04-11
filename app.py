from flask import Flask, render_template, jsonify, \
    request, Response, redirect, url_for, session
import os
import requests
import datetime
import json

from congito import cognito_auth

app = Flask(__name__)
app.secret_key = 'eipohgoo4rai0uf5ie1oshahmaeF'

# Constants
USER_POOL_ID = "us-east-1_QStEStwkt"
APP_CLIENT_ID = "4mo24hht37mvcfo0go8t3bn1qa"
API_GATEWAY_URL_ENDPOINT = "https://1t27fdgq0j.execute-api.us-east-1.amazonaws.com/prd"

# Routes of my application
@app.route('/')
def index():
    # session['user_id'] = usuario.id Set Session attribute
    if not session.get('app_client_id'):
        return render_template("login.html")
    return redirect(url_for("menu"))


@app.route('/login', methods=["POST"])
def login():
    # session['user_id'] = usuario.id Set Session attribute
    username = request.form['username']
    password = request.form['password']
    try:
        app_client_id = cognito_auth.authenticate_and_get_token(username, password, USER_POOL_ID, APP_CLIENT_ID)

        session['app_client_id'] = app_client_id['IdToken']
        session['user_id'] = 1

        return redirect(url_for("menu"))
    except Exception as e:
        return redirect(url_for("index"))


@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route('/menu', methods=["GET"])
def menu():
    return render_template("menu.html")


@app.route('/realizar_forecast', methods=["GET"])
def realizar_forecast():
    # TODO: validate response if contains error message
    try:
        headers = {'X-COG-ID': session['app_client_id']}
        payload = {'user_id': session['user_id']}
        response = requests.get(f"{API_GATEWAY_URL_ENDPOINT}/get_blood_forecast", params=payload, headers=headers)

        forecast = response.text
        return redirect(url_for("exibir_grafico_forecast", forecast=forecast))
    except Exception as e:
        return redirect(url_for("menu"))


@app.route('/exibir_grafico_forecast', methods=["GET", "POST"])
def exibir_grafico_forecast():
    forecast = json.loads(request.args['forecast'])
    list_glicose = []
    day_of_analysis = None

    for time, glicose in zip(forecast['time'], forecast['glicose']):
        new_dict = {}

        time = time.replace("T", " ")
        time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        timestamp = int(time.timestamp() * 1000)
        new_dict['x'] = timestamp
        new_dict['y'] = glicose
        list_glicose.append(new_dict)
        day_of_analysis = f"{time.day}/{time.month}/{time.year}"
    
    glic = list(item['y'] for item in list_glicose)

    glic_min = min(glic)
    glic_max = max(glic)

    return render_template("grafico_forecast.html", list_glicose=list_glicose, 
        day_of_analysis=day_of_analysis, glic_min=glic_min, glic_max=glic_max)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)


# TODO: Create user authentication
# cognito_auth.create_user("lucasduarte", "V@itomanocu1", USER_POOL_ID, APP_CLIENT_ID, "lucasdu@amazon.com")