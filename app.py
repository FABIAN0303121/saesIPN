import os
import base64
import requests
from flask import Flask, render_template, request, session
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = os.urandom(24)

UNIDADES_SAES = {
    "upiih": "https://www.saes.upiih.ipn.mx/",
    "escom": "https://www.saes.escom.ipn.mx/",
    "esfm": "https://www.saes.esfm.ipn.mx/",
    "esit": "https://www.saes.esit.ipn.mx/",
    "enba": "https://www.saes.enba.ipn.mx/"
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def get_asp_tags(html):
    soup = BeautifulSoup(html, 'html.parser')
    tags = {tag: soup.find('input', {'id': tag})['value'] for tag in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION'] if soup.find('input', {'id': tag})}
    return tags

@app.route('/')
def index():
    return render_template('index.html', unidades=UNIDADES_SAES.keys())

@app.route('/prepare_login', methods=['POST'])
def prepare_login():
    unidad = request.form.get('unidad')
    url_base = UNIDADES_SAES.get(unidad)
    s = requests.Session()
    try:
        res = s.get(f"{url_base}default.aspx", headers=HEADERS, verify=False, timeout=10)
        session['unidad_url'] = url_base
        session['tokens'] = get_asp_tags(res.text)
        session['cookies'] = s.cookies.get_dict()
        captcha_res = s.get(f"{url_base}Captcha.aspx", headers=HEADERS, verify=False, timeout=10)
        return {"captcha_img": base64.b64encode(captcha_res.content).decode('utf-8'), "unidad": unidad}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/login', methods=['POST'])
def login():
    url_base = session.get('unidad_url')
    s = requests.Session()
    s.cookies.update(session.get('cookies', {}))
    payload = {**session.get('tokens', {}), 'txtUser': request.form.get('usuario'), 'txtPass': request.form.get('password'), 'txtCaptcha': request.form.get('captcha'), 'btnIngresar': 'Ingresar'}
    res = s.post(f"{url_base}default.aspx", data=payload, headers=HEADERS, verify=False)
    return "Login Exitoso" if "Bienvenido" in res.text else ("Error", 401)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)