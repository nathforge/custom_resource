"""
Handle CloudFormation custom resource requests using Lambda.

AWS docs:
    * Overview: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html
    * Request object: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html
    * Response object: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref.html
"""

import abc
import json
import traceback

import jsonschema
import requests

from expect_status_code import expect_status_code

SUCCESS = "SUCCESS"
FAILED = "FAILED"

CREATE = "Create"
UPDATE = "Update"
DELETE = "Delete"

MAX_PHYSICAL_RESOURCE_ID_LENGTH = 1024

class BaseHandler(object):
    """
    Lambda handler for custom CFN resources.
    """

    __metaclass__ = abc.ABCMeta

    # Optional JSON Schema to validate "ResourceProperties" and
    # "OldResourceProperties".
    # The schema should include {"ServiceToken": {"type": "string"}} in the
    # root properties, as this is always sent by cloudFormation.
    RESOURCE_PROPERTIES_SCHEMA = None

    def __init__(self, debug=False):
        """
        Arguments:
            * `debug`: boolean. If True, includes full traceback on failure.
        """

        self.debug = debug

        self._event_type_handlers = {
            "Create": self.create,
            "Update": self.update,
            "Delete": self.delete
        }

    @abc.abstractmethod
    def create(self, event, context):
        """
        Create handler. Must be implemented in subclasses.

        AWS docs: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-requesttypes-create.html

        Must always return a result. See `Responder._coerce_response_to_dict`
        for a list of possible return types. Can optionally return a `Defer`
        object to signal asynchronous processing, see the `Defer` docstring for
        more info.
        """

    @abc.abstractmethod
    def update(self, event, context):
        """
        Update handler. Must be implemented in subclasses.

        AWS docs: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-requesttypes-update.html

        Must always return a result. See `Responder._coerce_response_to_dict`
        for a list of possible return types. Can optionally return a `Defer`
        object to signal asynchronous processing - see the `Defer` docstring for
        more info.
        """

    @abc.abstractmethod
    def delete(self, event, context):
        """
        Delete handler. Must be implemented in subclasses.

        AWS docs: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-requesttypes-delete.html

        Must always return a result. See `Responder._coerce_response_to_dict`
        for a list of possible return types. Can optionally return a `Defer`
        object to signal asynchronous processing, see the `Defer` docstring for
        more info.
        """

    def __call__(self, event, context):
        """
        Lambda handler. Calls create, update or delete, sends the result back
        to CloudFormation.
        """

        with Responder(event, self.debug) as responder:
            result = self.dispatch(event, context)
            if result is not Defer and not isinstance(result, Defer):
                responder.respond(result)

    def dispatch(self, event, context):
        """
        Dispatch the given event to create, update or delete, depending on the
        "RequestType" value. Returns the result, doesn't send it to
        CloudFormation.
        """

        if self.RESOURCE_PROPERTIES_SCHEMA:
            validator = jsonschema.Draft4Validator(self.RESOURCE_PROPERTIES_SCHEMA)
            for key in "ResourceProperties", "OldResourceProperties":
                if key in event:
                    validator.validate(event[key])

        event_type_handler = self._event_type_handlers[event["RequestType"]]
        return event_type_handler(event, context)

class Responder(object):
    """
    Respond to a custom resource request. Takes the Lambda event object and
    an optional debug flag. If debug=True, shows full traceback upon exception.

    Can be used as a context manager to catch exceptions and send a failure
    response.

    Responses can be:
        * A string representing a PhysicalResourceId.
        * A tuple of (PhysicalResourceId, Data)
        * A Success or Failed object.
    """

    def __init__(self, event, debug=False):
        """
        Arguments:
            * `event`: a Lambda event object.
            * `debug`: boolean. If True, includes full traceback on failure.
        """

        self.event = event
        self.debug = debug
        self.responded = False

    def success(self, *args, **kwargs):
        """
        Send a "SUCCESS" response to CloudFormation.
        """

        self.respond(Success(*args, **kwargs))

    def failed(self, *args, **kwargs):
        """
        Send a "FAILED" response to CloudFormation.
        """

        self.response(Failed(*args, **kwargs))

    def respond(self, response):
        """
        Send a response to CloudFormation by uploading to the given S3 URL.
        """

        self.responded = True

        if result is Defer or isinstance(result, Defer):
            return

        response_dict = self._get_response_as_dict(response)
        self._upload_response_data(self.event["ResponseURL"], json.dumps(response_dict))

    def __enter__(self):
        """
        Context manager to send "FAILED" responses upon exception.
        """

        return self

    def __exit__(self, type, exc, tb):
        """
        Context manager to send "FAILED" responses upon exception.
        """

        # Physical resource ID is always required, even on failure.
        # We'll take the previous ID if available, else use "n/a"
        physical_resource_id = self.event.get("PhysicalResourceId", "n/a")

        if not exc:
            if not self.responded:
                self.respond(Failed(physical_resource_id, "No response sent"))

        if exc:
            if self.debug:
                reason = traceback.format_exc()
            else:
                reason = unicode(value)

            self.respond(Failed(physical_resource_id, reason))

    def _get_response_as_dict(self, response):
        """
        Given a response (see Responder docstring), return a dict that can
        be sent to CloudFormation. Includes the source event's StackId,
        RequestId and LogicalResourceId.
        """

        response_dict = self._coerce_response_to_dict(response)
        response_dict.update({
            key: self.event[key]
            for key in ("StackId", "RequestId", "LogicalResourceId")
        })
        return response_dict

    def _coerce_response_to_dict(self, response):
        """
        Given a response (see Responder docstring), return a dict.
        """

        if isinstance(response, basestring):
            physical_resource_id = response
            return Success(physical_resource_id).as_dict()

        if isinstance(response, tuple) and len(response) == 2:
            physical_resource_id, data = response
            return Success(physical_resource_id, data).as_dict()

        if isinstance(response, (Success, Failed)):
            return response.as_dict()

        raise TypeError("Unexpected response {!r}".format(response))

    def _upload_response_data(self, url, data):
        expect_status_code(200, requests.put(url, data=data))

class Success(object):
    """
    Successful response. Takes a physical resource ID, and an optional data
    dict.

    See <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-responses.html>
    """

    def __init__(self, physical_resource_id, data={}):
        if not isinstance(physical_resource_id, basestring) or not 1 <= len(physical_resource_id) <= 1024:
            raise TypeError("physical_resource_id must be a string between 1 and 1024 characters")

        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        for key, value in data.iteritems():
            if not isinstance(key, basestring) or not isinstance(value, basestring):
                raise TypeError("{!r}={!r} must be strings".format(key, value))

        self._physical_resource_id = unicode(physical_resource_id)
        self._data = {unicode(key): unicode(value) for key, value in data.iteritems()}

    def as_dict(self):
        return {
            "Status": SUCCESS,
            "PhysicalResourceId": self._physical_resource_id,
            "Data": self._data
        }

class Failed(object):
    """
    Failed response. Takes the physical resource ID, and the reason for failure
    as a string.

    Physical resource ID is required by CloudFromation. This may not make sense
    when you're dealing with a failed creation. Couple of options:
      * If your resource lets you dictate an ID, generate it before creation.
        On failure, send the intended ID in the Failed response.
      * Respond with a nonsense value, e.g "n/a"

    See <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-responses.html>
    """

    def __init__(self, physical_resource_id, reason):
        if not isinstance(physical_resource_id, basestring) or not 1 <= len(physical_resource_id) <= MAX_PHYSICAL_RESOURCE_ID_LENGTH:
            raise TypeError("physical_resource_id must be a string between 1 and {} characters".format(MAX_PHYSICAL_RESOURCE_ID_LENGTH))

        if not isinstance(reason, basestring):
            raise TypeError("reason must be a unicode object")

        self._physical_resource_id = unicode(physical_resource_id)
        self._reason = unicode(reason)

    def as_dict(self):
        return {
            "Status": FAILED,
            "PhysicalResourceId": self._physical_resource_id,
            "Reason": self._reason
        }

class Defer(object):
    """
    A deferred response. Represents to Handler that you're working
    asynchronously.

    You need a copy of the event object when later sending an asynchronous
    response - for example:

        Responder(event).success(physical_resource_id="123", data={"other": "data"})
        Responder(event).failed(physical_resource_id="n/a", reason="Oh no")
    """
