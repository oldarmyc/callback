# Copyright 2015 Dave Kludt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bottle import post, run, request
from config import config


import bottle
import requests
import logging
import json


@post('/deploy/<app_name>/<app_port:int>/<repo_loc>')
def deploy_application(app_name, app_port, repo_loc):
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
                    'app_port': app_port,
                    'repo_location': repo_loc
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
