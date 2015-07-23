
from bottle import post, run, request
from config import config


import bottle
import requests
import logging
import json


@post('/deploy/<app_name>/<app_port:int>')
def deploy_application(app_name, app_port):
    token = authenticate()
    post_data = json.loads(request.body.read())
    if (
        post_data and
        post_data.get('commit') and
        post_data.get('commit').get('branch') == 'master'
    ):
        logging.info(
            'Code commited to master branch for %s, '
            'calling webhook for ansible deployment' % (
                post_data.get('repository').get('name')
            )
        )
        if token:
            url = '%s/api/v1/job_templates/%s/launch/' % (
                config.TOWER_URL,
                config.JOB_TEMPLATE
            )
            data = {
                'extra_vars': {
                    'app_name': app_name,
                    'app_port': app_port
                }
            }
            result = execute_api_request(url, data, token)
            if not result.get('job'):
                logging.error('Job was not returned successfully')
                return
            return result
        else:
            logging.error('Authentication failed so not running deploy')
            return
    else:
        logging.info(
            'Code submitted to %s was to %s branch, '
            'and no callback to ansible made' % (
                post_data.get('repository').get('name'),
                post_data.get('commit').get('branch')
            )
        )


def execute_api_request(url, data=None, token=None):
    result, response = None, None
    headers = {
        'Content-type': 'application/json',
    }
    if token:
        headers['Authorization'] = 'token %s' % token

    try:
        if data:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(data),
                verify=False
            )
        else:
            response = requests.get(
                url,
                headers=headers,
                verify=False
            )

        result = json.loads(response.content)
    except Exception as e:
        logging.error(
            'Ansible API returned an error: %s, exception: %s' % (
                response,
                e
            )
        )

    return result


def authenticate():
    token = None
    url = '%s/api/v1/authtoken/' % config.TOWER_URL
    data = {
        'username': config.TOWER_USERNAME,
        'password': config.TOWER_PASSWORD
    }
    result = execute_api_request(url, data)
    return result.get('token')


if __name__ == '__main__':
    run(host=config.HOST, port=config.PORT)

app = bottle.default_app()
