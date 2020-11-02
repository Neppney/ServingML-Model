from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def outline():
    return render_template('outline.html')


@app.route('/team')
def showTeam():
    return render_template('team.html')


@app.route('/inference')
def infer():
    return render_template('inference.html')


@app.route('/sqlFunctionality')
def sqlFunctionality():
    return render_template('sqlStoreRetrieve.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port="8080", debug=True)
