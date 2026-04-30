#!/usr/bin/env python3

import connexion
from flask import jsonify

from openapi_server import encoder


def main():
    app = connexion.App(__name__, specification_dir='./openapi/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('openapi.yaml',
                arguments={'title': 'Swagger Petstore'},
                pythonic_params=True)

    @app.app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    app.run(port=8080)


if __name__ == '__main__':
    main()
