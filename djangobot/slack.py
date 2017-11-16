import logging
import os

import requests


logger = logging.getLogger('slackapi')


class SlackAPI(object):
    """
    Yet Another Slack Client
    """
    url = 'https://slack.com/api/{method}'

    def __init__(self, token=None, auth_test=False, verify=True, lazy=False):
        """
        Instantiation an instance of the Slack API

        Args:
            token: {str} (required) API token, read from SLACK_TOKEN env var
            auth_test: {bool} verify this token
            verify: {bool} verify all API calls return with a True 'ok'
            lazy: {bool} Don't populate properties until called
        """

        try:
            self.token = token if token else os.environ['SLACK_TOKEN']
        except KeyError:
            raise ValueError('If not providing a token, must set SLACK_TOKEN envvar')
        self.verify = verify
        if auth_test:
            response = self.auth_test()
            if not response['ok']:
                raise ValueError('Authentication Failed with response: {}'.format(response))

        # Attributes backing properties
        self._channels = []
        self._users = []

        if not lazy:
            _ = self.channels
            _ = self.users

    def _call_api(self, method, params=None):
        """
        Low-level method to call the Slack API via GET.

        Args:
            method: {str} method name to call
            params: {dict} GET parameters
                The token will always be added
        """
        if not params:
            params = {'token': self.token}
        else:
            params['token'] = self.token
        return self._api_call(method, 'get', {'params': params})

    def _post_api(self, method, params=None):
        """
        Low-level method to call the Slack API via POST.

        Args:
            method: {str} method name to call
            params: {dict} GET parameters
                The token will always be added
        """
        headers = {
            'Authorization': 'Bearer {}'.format(self.token),
        }
        return self._api_call(method, 'post', {
            'headers': headers,
            'json': params,
        })

    def _api_call(self, method, request_method, request_kwargs):
        """
        Low-level method to call the Slack API.

        Args:
            method: {str} method name to call
            params: {dict} GET parameters
                The token will always be added
        """
        url = self.url.format(method=method)
        logger.debug('Send request to %s', url)
        response = getattr(requests, request_method)(url, **request_kwargs).json()

        if self.verify:
            if not response['ok']:
                msg = 'For {url} API returned this bad response {response}'
                raise Exception(msg.format(url=url, response=response))
        return response

    @property
    def channels(self):
        """
        List of channels of this slack team
        """
        if not self._channels:
            self._channels = self._call_api('channels.list')['channels']
        return self._channels

    @property
    def users(self):
        """
        List of users of this slack team
        """
        if not self._users:
            self._users = self._call_api('users.list')['members']
        return self._users

    # API Methods
    def auth_test(self):
        """
        Call auth.test
        """
        return self._call_api('auth.test') and self._post_api('auth.test')

    def rtm_start(self):
        """
        Call rtm.start
        """
        return self._call_api('rtm.start')

    def chat_post_message(self, **params):
        """
        Post to chat.postMessage

        :param params: arguments to pass
        :return:
        """
        self._post_api('chat.postMessage', params)

    # Translation
    def channel_from_name(self, name):
        """
        Return the channel dict given by human-readable {name}
        """
        try:
            channel = [channel for channel in self.channels
                       if channel['name'] == name][0]
        except IndexError:
            raise ValueError('Unknown channel for name: "{}"'.format(name))
        return channel

    def user_from_id(self, user_id):
        try:
            user = [user for user in self.users
                    if user['id'] == user_id][0]
        except IndexError:
            raise ValueError('Unknown user for id: "{}"'.format(user_id))
        return user

    def channel_from_id(self, channel_id):
        try:
            channel = [channel for channel in self.channels
                       if channel['id'] == channel_id][0]
        except IndexError:
            raise ValueError('Unknown channel for id: "{}"'.format(channel_id))
        else:
            return channel

    def reload_channels(self):
        self._channels = None
