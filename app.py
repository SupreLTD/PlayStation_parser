from flask import Flask, send_file

app = Flask(__name__)


@app.route('/get_csv_ps')
def get_csv_ps():
    return send_file('data/ps.csv', as_attachment=True)


app.run(host="localhost")
