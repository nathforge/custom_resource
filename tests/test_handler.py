import json
import unittest

import mock

from custom_resource import BaseHandler, Defer, Failed, Responder, Success

class TestCase(unittest.TestCase):
    def setUp(self):
        self.upload_response_data_mock = mock.patch.object(Responder, "_upload_response_data")
        self.upload_response_data_mock.start()

    def tearDown(self):
        self.upload_response_data_mock.stop()

    def test_create_update_delete_required(self):
        class Handler(BaseHandler):
            pass

        with self.assertRaisesRegexp(TypeError, "Can't instantiate abstract class Handler with abstract methods create, delete, update"):
            Handler()

    def test_create(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(create=lambda self, *args: Success("PhysicalResourceId", {"Meta": "Data"}))
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "PhysicalResourceId",
            "Data": {
                "Meta": "Data"
            }
        })
        self.assertEqual(kwargs, {})

    def test_update(self):
        event = {
            "RequestType": "Update",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(update=lambda self, *args: Success("PhysicalResourceId", {"Meta": "Data"}))
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "PhysicalResourceId",
            "Data": {
                "Meta": "Data"
            }
        })
        self.assertEqual(kwargs, {})

    def test_delete(self):
        event = {
            "RequestType": "Delete",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(delete=lambda self, *args: Success("PhysicalResourceId", {"Meta": "Data"}))
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "PhysicalResourceId",
            "Data": {
                "Meta": "Data"
            }
        })
        self.assertEqual(kwargs, {})

    def test_success(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(create=lambda self, *args: Success("PhysicalResourceId", {"Meta": "Data"}))
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "PhysicalResourceId",
            "Data": {
                "Meta": "Data"
            }
        })
        self.assertEqual(kwargs, {})

    def test_failed(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(create=lambda self, *args: Failed("PhysicalResourceId", "Broken"))
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "PhysicalResourceId",
            "Reason": "Broken"
        })
        self.assertEqual(kwargs, {})

    def test_defer(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(create=lambda self, *args: Defer())
        handler(event, context=None)

        Responder._upload_response_data.assert_not_called()

    def test_exception(self):
        def raise_exc(exc):
            raise exc

        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(create=lambda self, *args: raise_exc(Exception("Couldn't create")))

        with self.assertRaisesRegexp(Exception, "Couldn't create"):
            handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "n/a",
            "Reason": "Couldn't create"
        })
        self.assertEqual(kwargs, {})

    def test_no_response(self):
        class Handler(BaseHandler):
            def create(self, event, context):
                pass

            update = None
            delete = None

        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        context = None
        with self.assertRaisesRegexp(TypeError, "No response returned"):
            Handler()(event, context)

    def test_physical_resource_id_result(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(create=lambda self, *args: "PhysicalResourceId")
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "PhysicalResourceId",
            "Data": {}
        })
        self.assertEqual(kwargs, {})

    def test_physical_resource_id_and_data_result(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        handler = self.handler(create=lambda self, *args: ("PhysicalResourceId", {"Meta": "Data"}))
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "PhysicalResourceId",
            "Data": {
                "Meta": "Data"
            }
        })
        self.assertEqual(kwargs, {})

    def test_unknown_return_type(self):
        class Handler(BaseHandler):
            def create(self, event, context):
                return object()

            update = None
            delete = None

        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        context = None
        with self.assertRaisesRegexp(TypeError, "Unexpected response .*"):
            Handler()(event, context)

    def test_schema_validation_pass(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response",
            "ResourceProperties": {},
            "OldResourceProperties": {}
        }
        handler = self.handler(
            create=lambda self, *args: Success("PhysicalResourceId", {"Meta": "Data"}),
            schema={}
        )
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "PhysicalResourceId",
            "Data": {
                "Meta": "Data"
            }
        })
        self.assertEqual(kwargs, {})

    def test_schema_validation_resource_properties_fail(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response",
            "ResourceProperties": {},
            "OldResourceProperties": {
                "Validating": True
            }
        }
        handler = self.handler(
            create=lambda self, *args: Success("PhysicalResourceId", {"Meta": "Data"}),
            schema={
                "required": ["Validating"],
                "properties": {
                    "Validating": {
                        "enum": [True]
                    }
                }
            }
        )
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "n/a",
            "Reason": (
                "'Validating' is a required property\n"
                "\n"
                "Failed validating 'required' in schema:\n"
                "    {'properties': {'Validating': {'enum': [True]}},\n"
                "     'required': ['Validating']}\n"
                "\n"
                "On instance:\n"
                "    {}"
            )
        })
        self.assertEqual(kwargs, {})

    def test_schema_validation_old_resource_properties_fail(self):
        event = {
            "RequestType": "Create",
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response",
            "ResourceProperties": {
                "Validating": True
            },
            "OldResourceProperties": {}
        }
        handler = self.handler(
            create=lambda self, *args: Success("PhysicalResourceId", {"Meta": "Data"}),
            schema={
                "required": ["Validating"],
                "properties": {
                    "Validating": {
                        "enum": [True]
                    }
                }
            }
        )
        handler(event, context=None)

        (_, (url, data), kwargs), = Responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "n/a",
            "Reason": (
                "'Validating' is a required property\n"
                "\n"
                "Failed validating 'required' in schema:\n"
                "    {'properties': {'Validating': {'enum': [True]}},\n"
                "     'required': ['Validating']}\n"
                "\n"
                "On instance:\n"
                "    {}"
            )
        })
        self.assertEqual(kwargs, {})

    def handler(self, create=None, update=None, delete=None, schema=None):
        Handler = type("Handler", (BaseHandler,), {
            "create": create,
            "update": update,
            "delete": delete,
            "RESOURCE_PROPERTIES_SCHEMA": schema
        })
        return Handler()
