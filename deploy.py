#!/usr/bin/python3
#
# Copyright (C) 2019 Oleg Shnaydman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import os
import requests
import re
from gdrive import *

DROPBOX_ERROR_CODE = 1
SENDGRID_ERROR_CODE = 2
TEMPLATE_ERROR_CODE = 3
CHANGES_ERROR_CODE = 4
OUTPUT_FILE_PARSING_ERROR = 5

SENDGRID_EMAIL_DATA = {
    "personalizations": [
        {
            "to": [
                {
                    "email": None
                }
            ]
        }
    ],
    "from": {
        "email": None
    },
    "subject": None,
    "content": [
        {
            "type": "text/plain",
            "value": None
        }
    ]
}

def send_email(sendgrid_hook, sendgrid_auth_prefix, sendgrid_auth, emailFrom, emailTo, subject, body):
    '''Send email with sendgrid hook

    Args:
        sendgrid_hook (str): sendgrid hook url.
        to (str): Email recipients separated by comma.
        subject (str): Email subject.
        body (str): Email body.

    Returns:
        bool: Send success/fail.
    '''
    SENDGRID_EMAIL_DATA['from']['email'] = emailFrom
    SENDGRID_EMAIL_DATA['personalizations'][0]['to'] = emailTo
    SENDGRID_EMAIL_DATA['subject'] = subject
    SENDGRID_EMAIL_DATA['content'][0]['value'] = body

    print(SENDGRID_EMAIL_DATA)

    auth = sendgrid_auth_prefix + " " + sendgrid_auth
    headers = {'Authorization': auth, 'Content-Type': 'application/json'}

    r = requests.post(sendgrid_hook, data=json.dumps(SENDGRID_EMAIL_DATA), headers=headers)
    print(r.status_code)
    return r.status_code == 202 #requests.codes.ok


def get_app(release_dir):
    '''Extract app data

    Args:
        release_dir (str): Path to release directory.

    Returns:
        (str, str): App version and path to release apk file.
    '''
    output_path = os.path.join(release_dir, 'output.json')

    with(open(output_path)) as app_output:
        json_data = json.load(app_output)

    apk_details_key = ''
    if 'apkInfo' in json_data[0]:
        apk_details_key = 'apkInfo'
    elif 'apkData' in json_data[0]:
        apk_details_key = 'apkData'
    else:
        print("Failed: parsing json in output file")
        return None, None

    app_version = json_data[0][apk_details_key]['versionName']
    app_file = os.path.join(release_dir, json_data[0][apk_details_key]['outputFile'])
    return app_version, app_file


def get_target_file_name(app_name, app_version):
    '''Generate file name for released apk, using app name and version:
    app_name - MyApp
    version - 1.03
    result: myapp_1_03.apk

    Args:
        app_name (str): App name.
        app_version (str): App version.

    Returns:
        str: App file name.
    '''
    app_name = app_name.lower()
    app_version = app_version.replace('.', '_')
    return '{name}_{version}.apk'.format(name=app_name, version=app_version).replace(' ','')


def get_changes(change_log_path):
    '''Extract latest changes from changelog file.
    Changes are separated by ##

    Args:
        change_log_path (str): Path to changelog file.

    Returns:
        str: Latest changes.
    '''
    with(open(change_log_path)) as change_log_file:
        change_log = change_log_file.read()

    # Split by '##' and remove lines starting with '#'
    latest_version_changes = change_log.split('##')[0][:-1]
    latest_version_changes = re.sub('^#.*\n?', '', latest_version_changes, flags=re.MULTILINE)

    return latest_version_changes


def get_email(app_name, app_version, app_url, changes, template_file_path):
    '''Use template file to create release email subject and title.

    Args:
        app_name (str): App name.
        app_version (str): App version.
        app_url (str): Url for app download.
        changes (str): Lastest app changelog.
        template_file_path (str): Path to template file.

    Returns:
        (str, str): Email subject and email body.
    '''
    target_subject = 1
    target_body = 2
    target = 0

    subject = ''
    body = ''

    template = ''

    with(open(template_file_path)) as template_file:
        # Open template file and replace placeholders with data
        template = template_file.read().format(
            app_download_url=app_url,
            change_log=changes,
            app_name=app_name,
            app_version=app_version
        )

    # Iterate over each line and collect lines marked for subject/body
    for line in template.splitlines():
        if line.startswith('#'):
            if line.startswith('#subject'):
                target = target_subject
            elif line.startswith('#body'):
                target = target_body
        else:
            if target == target_subject:
                subject += line + '\n'
            elif target == target_body:
                body += line + '\n'

    return subject.rstrip(), body.rstrip()

def upload_gdrive(jsonEmail):
    drive_service = getDriveService(options.client_secrets_file)
    file_id = upload(drive_service, target_app_file, app_file)
    shareFile(drive_service, file_id, jsonEmail)
    fileUploaded = getListAll(drive_service)
    file_url = fileUploaded['webContentLink']
    print("url download " + file_url)
    return file_url

if __name__ == '__main__':
    # Command line arguments
    print("1==============")
    parser = argparse.ArgumentParser()
    parser.add_argument('--release.dir', dest='release_dir', help='path to release folder', required=True)
    parser.add_argument('--app.name', dest='app_name', help='app name that will be used as file name', required=True)
    parser.add_argument('--changelog.file', dest='changelog_file', help='path to changelog file', required=True)
    parser.add_argument('--template.file', dest='template_file', help='path to email template file', required=True)
    parser.add_argument('--sendgrid.hook', dest='sendgrid_hook', help='sendgrid email web hook', required=True)
    parser.add_argument('--sendgrid.authprefix', dest='sendgrid_auth_prefix', help='sendgrid email web hook prefix', required=True)
    parser.add_argument('--sendgrid.auth', dest='sendgrid_auth', help='sendgrid email web hook key', required=True)
    parser.add_argument('--email.from', dest='email_from', help='email recipients', required=True)
    parser.add_argument('--email.to', dest='email_to', help='email recipients', required=True)
    parser.add_argument('--client_secrets.file', dest='client_secrets_file', help='account_client gdrive secret file', required=True)

    options = parser.parse_args()
    print("2==============")

    jsonEmail = json.loads(options.email_to)

    # Extract app version and file
    app_version, app_file = get_app(options.release_dir)
    if app_version == None or app_file == None:
        exit(OUTPUT_FILE_PARSING_ERROR)
    print("3==============")
    target_app_file = get_target_file_name(options.app_name, app_version)
    print("4==============")
    # Upload app file and get shared url
    file_url = upload_gdrive(jsonEmail)
    if file_url == None:
        exit(DROPBOX_ERROR_CODE)
    print("5==============")
    # Extract latest changes
    latest_changes = get_changes(options.changelog_file)
    if latest_changes == None:
        exit(CHANGES_ERROR_CODE)
    print("6==============")
    subject, body = get_email(options.app_name, app_version, file_url, latest_changes, options.template_file)
    if subject == None or body == None:
        exit(TEMPLATE_ERROR_CODE)
    print("7==============")
    # print(options.sendgrid_hook + "\n" + options.sendgrid_auth_prefix + "\n" + options.sendgrid_auth + "\n" + options.email_to + "\n" + subject + "\n" + body)

    # Send email with release data
    if not send_email(options.sendgrid_hook, options.sendgrid_auth_prefix, options.sendgrid_auth, "", jsonEmail, subject, body):
        exit(SENDGRID_ERROR_CODE)
    print("8==============")