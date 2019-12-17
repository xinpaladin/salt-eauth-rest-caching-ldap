#!/usr/bin/env python3
# pylint: disable=R,C
import werkzeug
from flask import Flask
from flask_apscheduler import APScheduler

from caching_ldap.v1 import api as api_v1

app = Flask(__name__)
app.register_blueprint(api_v1)

scheduler = APScheduler()
scheduler.api_enabled = False
scheduler.init_app(app)
scheduler.start()

app.cached_users = {}

# TODO:
# * configure
#   * ldap
#     * server/url
#     * ldap-credentials
#     * search_base
#     * search_filter
#   * salt acl config file
#   * logging levels
# * cron which:
#   * finds all driftansvariga-*-groups and add them to cached_users[uid]
# * On /login
#   * Get all groups from cached_users[uid]
#   * Read the yaml config
#   * Create list returned_acl
#   * iterate over each group key e.g.
#     'driftansvariga-configurationmanagement%':
#     * if it exists in cached_users[uid]:
#       * add it to a returned_acl
#   * return returned_acl


def get_groups(*, search_base, search_filter):
    _, _ = search_base, search_filter
    return {
        "frkj4220": ["driftansvariga-configurationmanagement"],
        "simlu": ["driftansvariga-configurationmanagement"],
    }


@scheduler.task('cron', minute='*/5')
def update_groups():
    app.cached_users = get_groups(
        search_base='ou=driftansvariga,ou=Groups,dc=it,dc=su,dc=se',
        search_filter='cn=driftansvariga-*')
    app.logger.info('Updated %s users from LDAP', len(app.cached_users))


@app.errorhandler(werkzeug.exceptions.HTTPException)
def handle_http_errors(e):
    return {"description": e.description, "code": e.code}, e.code


@app.errorhandler(Exception)
def handle_exceptions(e):
    app.logger.exception(e)
    return {"description": "Internal Server Error", "code": 500}, 500


@app.route('/status')
def status():
    return {'status': 'OK'}, 200
