from flask import Flask, render_template

from model import load

app = Flask(__name__)

model_api = load()

@app.route('/')
def outline():
    return render_template('outline.html')


@app.route('/team')
def show_team():
    return render_template('team.html')


@app.route('/inference')
def infer():
    return render_template('inference.html')


@app.route('/sqlFunctionality')
def sql_functionality():
    return render_template('sqlStoreRetrieve.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port="8080", debug=True)
