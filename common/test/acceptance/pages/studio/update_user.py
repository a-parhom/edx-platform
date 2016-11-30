"""
Update page (used to update user).
"""

import re
import urllib
from bok_choy.page_object import PageObject
from common.test.acceptance.pages.studio import BASE_URL


class UpdateUser(PageObject):
    """
    The update page.
    When allowed via the django settings file i.e
    settings.FEATURES['AUTOMATIC_AUTH_FOR_TESTING'] is true,
    visiting this url will update the user.
    """

    def __init__(self, browser, username, is_active=None):
        """
        UpdateUser is an end-point for HTTP GET requests.
        Using querystring parameters, values to update a user
        are provided.

        `username` is send along querystring parameter in order to
        fetch which user needs to be updated.

        Following are other querystring parameters which are used
        as values to update user:
            1. `is_active`: status of user whether he/she is active or inactive (string)
        """
        super(UpdateUser, self).__init__(browser)

        # Create query string parameters
        self._params = {'username': username}

        if is_active is not None:
            self._params['is_active'] = "true" if is_active else "false"

    @property
    def url(self):
        """
        Construct the URL.
        """
        url = BASE_URL + "/update_user"
        query_str = urllib.urlencode(self._params)

        if query_str:
            url += "?" + query_str

        return url

    def is_browser_on_page(self):
        """
        check if browser is showing expected page
        """
        message = self.q(css='BODY').text[0]
        match = re.search(r'user with username ([^$]+) is updated$', message)
        return True if match else False
