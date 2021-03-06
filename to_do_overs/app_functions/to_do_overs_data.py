"""Application controller code - Habitica To Do Over tool

App controller functions for the Habitica To Do Over tool.
For functions that don't fit in the model or views.
"""
from __future__ import absolute_import

from builtins import str
from builtins import object
__author__ = "Katie Patterson kirska.com"
__license__ = "MIT"

from datetime import datetime, timedelta
import requests
from to_do_overs.models import Users, Tags
from .cipher_functions import encrypt_text, decrypt_text, CIPHER_FILE


class ToDoOversData(object):
    """Session data and application functions that don't fall in models or views.

    This class will be stored in a cookie for a login session.

    Attributes:
        username (str): Username from Habitica.
        hab_user_id (str): User ID from Habitica.
        api_token (str): API token from Habitica.
        logged_in (bool): Goes to true once user has successfully logged in.
        task_name (str): The name/title of the task being created.
        task_days (int): The number of days that a task should last
            before expiring for the task being created.
        task_id (str): The created task ID from Habitica.
        priority (str): Difficulty of the task being created.
            See models.py for choices.
        notes (str): The description/notes of the task being created.
        tags (list): The user's tags.
    """
    def __init__(self):
        self.username = ''
        self.hab_user_id = ''
        self.api_token = ''
        self.logged_in = False
        self.tags = []

        self.task_name = ''
        self.task_days = 0
        self.task_delay = 0
        self.task_id = ''
        self.priority = ''
        self.notes = ''

        self.return_code = 0

    def login(self, password):
        """Login with a username and password to Habitica.

        Args:
            password: The password.

        Returns:
            True for success, False for failure.
        """
        req = requests.post(
            'https://habitica.com/api/v3/user/auth/local/login',
            data={'username': self.username, 'password': password}
        )
        self.return_code = req.status_code
        if req.status_code == 200:
            req_json = req.json()
            self.hab_user_id = req_json['data']['id']
            self.api_token = encrypt_text(
                req_json['data']['apiToken'].encode('utf-8')
            )
            self.username = req_json['data']['username']

            Users.objects.update_or_create(user_id=self.hab_user_id, defaults={
                'api_key': self.api_token,
                'username': self.username,
            })

            self.logged_in = True

            return True
        else:
            return False

    def login_api_key(self):
        """Login with user ID and API token to Habitica.

        Returns:
            True for success, False for failure.
        """
        headers = {
            'x-api-user': self.hab_user_id.encode('utf-8'),
            'x-api-key': decrypt_text(self.api_token),
            'Content-Type': 'application/json'
        }

        req = requests.get('https://habitica.com/api/v3/user', headers=headers)
        self.return_code = req.status_code
        if req.status_code == 200:
            req_json = req.json()
            self.username = req_json['data']['profile']['name']

            Users.objects.update_or_create(user_id=self.hab_user_id, defaults={
                'api_key': self.api_token,
                'username': self.username,
            })

            self.logged_in = True

            return True
        return False

    def create_task(self, cipher_file_path=CIPHER_FILE):
        """Create a task on Habitica.

        Returns:
            True for success, False for failure.
        """
        headers = {
            'x-api-user': self.hab_user_id.encode('utf-8'),
            'x-api-key': decrypt_text(
                self.api_token.encode('utf-8'),
                cipher_file_path
            )
        }

        if int(self.task_days) > 0:
            due_date = datetime.now() + timedelta(days=int(self.task_days))
            due_date = due_date.isoformat()

            req = requests.post(
                'https://habitica.com/api/v3/tasks/user',
                headers=headers,
                data={
                    'text': self.task_name,
                    'type': 'todo',
                    'notes': self.notes,
                    'date': due_date,
                    'priority': self.priority,
                    'tags': self.tags,
                }
            )
            self.return_code = req.status_code
            if req.status_code == 201:
                req_json = req.json()
                self.task_id = req_json['data']['id']
                return True
            return False
        else:
            req = requests.post(
                'https://habitica.com/api/v3/tasks/user',
                headers=headers,
                data={
                    'text': self.task_name,
                    'type': 'todo',
                    'notes': self.notes,
                    'priority': self.priority,
                    'tags': self.tags,
                }
            )
            self.return_code = req.status_code
            if req.status_code == 201:
                req_json = req.json()
                self.task_id = req_json['data']['id']
                return True
            return False

    def edit_task(self):
        """Edit a task on Habitica.

        Returns:
            True for success, False for failure.
        """
        headers = {'x-api-user': self.hab_user_id.encode('utf-8'),
                   'x-api-key': decrypt_text(self.api_token.encode('utf-8'))}
        url = 'https://habitica.com/api/v3/tasks/' + str(self.task_id)

        if int(self.task_days) > 0:
            due_date = datetime.now() + timedelta(days=int(self.task_days))
            due_date = due_date.isoformat()

            req = requests.put(url, headers=headers, data={
                'text': self.task_name,
                'notes': self.notes,
                'date': due_date,
                'priority': self.priority,
                'tags': self.tags,
            })
            self.return_code = req.status_code
            if req.status_code == 200:
                req_json = req.json()
                self.task_id = req_json['data']['id']
                return True
            return False
        else:
            req = requests.put(url, headers=headers, data={
                'text': self.task_name,
                'notes': self.notes,
                'priority': self.priority,
                'tags': self.tags,
            })
            self.return_code = req.status_code
            if req.status_code == 200:
                req_json = req.json()
                self.task_id = req_json['data']['id']
                return True
            else:
                return False

    def get_user_tags(self, cipher_file_path=CIPHER_FILE):
        """Get the list of a user's tags.

        Returns:
            Dict of tags for success, False for failure.
        """
        headers = {
            'x-api-user': self.hab_user_id.encode('utf-8'),
            'x-api-key': decrypt_text(
                self.api_token.encode('utf-8'),
                cipher_file_path,
            )
        }

        req = requests.get(
            'https://habitica.com/api/v3/tags',
            headers=headers,
            data={}
        )
        self.return_code = req.status_code
        if req.status_code == 200:
            req_json = req.json()

            user = Users.objects.get(user_id=self.hab_user_id)

            current_tags = Tags.objects.filter(tag_owner=user)
            current_tag_ids = []
            for tag in current_tags:
                current_tag_ids.append(tag.tag_id)

            if req_json['data']:
                # Add/update tags in database
                for tag_json in req_json['data']:
                    tag_text = tag_json['name']
                    tag_text = tag_text.encode('unicode_escape')

                    Tags.objects.update_or_create(
                        tag_id=tag_json['id'].encode('utf-8'),
                        defaults={
                            'tag_owner': user,
                            'tag_text': tag_text.encode('utf-8')
                        },
                    )
                    if tag_json['id'] in current_tag_ids:
                        current_tag_ids.remove(tag_json['id'])

                for leftover_tag in current_tag_ids:
                    print('deleting tag ' + leftover_tag)
                    Tags.objects.filter(tag_id=leftover_tag).delete()

                return req_json['data']
            return False
        return False
