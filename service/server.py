import time
import sqlite3
from flask import Flask, jsonify
from flask import make_response, render_template
from flask_restful import Resource, Api, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix

from get_db import get_db, execute_db, init_app

parser = reqparse.RequestParser()
parser.add_argument('n', type=int, help="ERROR: empty length of data")
parser.add_argument('where', type=str, help="ERROR: empty table name")


class SensorData(Resource):
    def get(self):
        args = parser.parse_args()
        n_points = args.get('n')
        location = args.get('where')
        if n_points is None:
            n_points = 1000

        try:
            data = execute_db('''
            SELECT timestamp, temperature, activity
            FROM sensor_data ORDER BY timestamp DESC LIMIT {}
            '''.format(n_points))

            timestamp = [tup[0] for tup in data]
            temperature = [tup[1] for tup in data]
            activity = [tup[2] for tup in data]

        except Exception as e:
            return {"Exception Type": str(type(e)),
                    "Args": str(e.args),
                    "__str__": str(e.__str__)}

        return {'timestamp': timestamp,
                'temperature': temperature,
                'activity': activity}

    def post(self):
        # TODO: Need to change database schema and test this endpoint
        args = parser.parse_args()
        location = args.get('where')
        temperature = args.get('temperature')
        timestamp = int(time.time())

        try:
            with get_db() as connection:
                cursor = connection.cursor()
                cursor.execute('''
                INSERT INTO ?
                VALUES (?,?,?)''', (where, timestamp, temperature))
                cursor.close()
        except Exception as e:
            return {"Exception Type": str(type(e)),
                    "Args": str(e.args),
                    "__str__": str(e.__str__)}


class PiTemp(Resource):
    def get(self):
        data = parser.parse_args()
        n_points = data.get('n')
        if n_points is None:
            n_points = 1000

        try:
            with get_db() as connection:
                cursor = connection.cursor()
                cursor.execute('''
                SELECT name, timestamp, temperature FROM pi_temp
                ORDER BY timestamp DESC LIMIT {}'''.format(n_points))
                data = cursor.fetchall()
                cursor.close()
        except Exception as e:
            return {"Exception Type": str(type(e)),
                    "Args": str(e.args),
                    "__str__": str(e.__str__)}

        names = set(v[0] for v in data)
        res = {}
        for name in names:
            res[name] = []
        for v in data:
            res[v[0]].append({
                'x': v[1],
                'y': v[2]
            })
        return res

    def post(self):
        parser.add_argument('name', type=str)
        parser.add_argument('temperature', type=float)
        args = parser.parse_args()
        name = args["name"]
        temperature = args["temperature"]
        timestamp = int(time.time())

        if name is None or temperature is None:
            return {"error": "Missing arguments"}

        try:
            with get_db() as connection:
                cursor = connection.cursor()
                cursor.execute('''
                INSERT INTO pi_temp
                VALUES (?,?,?)''', (name, timestamp, temperature))
                cursor.close()
        except Exception as e:
            return {"Exception Type": str(type(e)),
                    "Args": str(e.args),
                    "__str__": str(e.__str__)}

        return {
            'status': True,
            'name': args['name'],
            'temperature': args['temperature']
        }


def create_app():

    # Instantiate flask app
    app = Flask(__name__, instance_relative_config=True)
    init_app(app)

    # Proxy support for NGINX
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Configure to see multiple errors in response
    app.config['BUNDLE_ERRORS'] = True

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': "Not found"}), 404)

    # Flask_restful API
    api = Api(app)
    api.add_resource(SensorData, '/home_api/sensor_data')
    api.add_resource(PiTemp, '/home_api/pi_temp')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port="6969", debug=True)
