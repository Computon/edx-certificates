import json
import logging

import requests
from requests.exceptions import ConnectionError, Timeout

log = logging.getLogger(__name__)


class XQueuePullManager:
    """
    XQueuePullManager provides an interface to
    the xqueue server for the pull interface

    Methods for getting the queue length,
    retrieving a single item from the queue
    and posting a response.
    """

    def __init__(self, queue_url, queue_name, queue_auth_user, queue_auth_pass, queue_user, queue_pass):
        self.url = queue_url
        self.queue_name = queue_name
        self.auth_user = queue_auth_user
        self.auth_pass = queue_auth_pass
        self.queue_user = queue_user
        self.queue_pass = queue_pass
        self._login()

    def _login(self):
        """
        Login to the xqueue server
        """

        try:
            self.session = requests.Session()
            self.session.auth = (self.auth_user, self.auth_pass)
            request = self.session.post(f'{self.url}/xqueue/login/',
                                        data={'username': self.queue_user,
                                              'password': self.queue_pass})
            response = json.loads(request.text)
            if response['return_code'] != 0:
                raise Exception("Invalid return code in reply resp:{}".format(
                    str(response)))
        except (Exception, ConnectionError, Timeout) as e:
            log.critical(f"Unable to connect to queue xqueue: {e}")
            raise

    def get_length(self):
        """
        Returns the length of the queue
        """

        try:
            request = self.session.get('{}/xqueue/get_queuelen/'.format(
                self.url), params={'queue_name': self.queue_name})
            response = json.loads(request.text)
            if response['return_code'] != 0:
                raise Exception("Invalid return code in reply")
            length = int(response['content'])
        except (ValueError, Exception, ConnectionError, Timeout) as e:
            log.critical(f"Unable to get queue length: {e}")
            raise

        return length

    def get_submission(self):
        """
        Gets a single submission from the xqueue
        server and returns the payload as a dictionary
        """

        try:
            request = self.session.get('{}/xqueue/get_submission/'.format(
                self.url), params={'queue_name': self.queue_name})
        except (ConnectionError, Timeout) as e:
            log.critical(f"Unable to get submission from queue xqueue: {e}")
            raise

        try:
            response = json.loads(request.text)
            log.debug(f'response from get_submission: {response}')
            if response['return_code'] != 0:
                log.critical(f"response: {request.text}")
                raise Exception("Invalid return code in reply")

            return json.loads(response['content'])

        except (Exception, ValueError, KeyError) as e:
            log.critical(f"Unable to parse xqueue message: {e} response: {request.text}")
            raise

    def respond(self, xqueue_reply):
        """Post xqueue_reply to qserver for posting back to LMS"""

        try:
            request = self.session.post('{}/xqueue/put_result/'.format(
                self.url), data=xqueue_reply)
            log.info(f'Response: {request.text}')

        except (ConnectionError, Timeout) as e:
            log.critical(f"Connection error posting response to the LMS: {e}")
            raise
        response = json.loads(request.text)
        if response['return_code'] != 0:
            log.critical(f"response: {request.text}")
            raise Exception("Invalid return code in reply")

    def __str__(self):
        return self.url
