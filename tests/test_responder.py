import json
import unittest

import mock

from custom_resource import Responder

class TestCase(unittest.TestCase):
    def setUp(self):
        self.upload_response_data_mock = mock.patch.object(Responder, "_upload_response_data")
        self.upload_response_data_mock.start()

    def tearDown(self):
        self.upload_response_data_mock.start()

    def test_success(self):
        event = {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        responder = Responder(event)
        responder.success(physical_resource_id="123", data={
            "a": "1",
            "b": "2"
        })

        responder._upload_response_data.assert_called_once()
        (_, (url, data), kwargs), = responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "SUCCESS",
            "PhysicalResourceId": "123",
            "Data": {
                "a": "1",
                "b": "2"
            }
        })
        self.assertEqual(kwargs, {})

    def test_failed(self):
        event = {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        responder = Responder(event)
        responder.failed(physical_resource_id="123", reason="It broke")

        responder._upload_response_data.assert_called_once()
        (_, (url, data), kwargs), = responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "123",
            "Reason": "It broke"
        })
        self.assertEqual(kwargs, {})

    def test_defer(self):
        event = {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        responder = Responder(event)
        responder.defer()

        responder._upload_response_data.assert_not_called()

    def test_context_handler_requires_response(self):
        event = {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        with Responder(event) as responder:
            pass

        responder._upload_response_data.assert_called_once()
        (_, (url, data), kwargs), = responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "n/a",
            "Reason": "No response sent"
        })
        self.assertEqual(kwargs, {})

    def test_context_handler_sends_fail_response_on_exception(self):
        event = {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response"
        }
        with self.assertRaisesRegexp(Exception, "Something happened"):
            with Responder(event) as responder:
                raise Exception("Something happened")

        responder._upload_response_data.assert_called_once()
        (_, (url, data), kwargs), = responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "n/a",
            "Reason": "Something happened"
        })
        self.assertEqual(kwargs, {})

    def test_context_handler_forwards_physical_resource_id_in_failure_if_missing_response(self):
        event = {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response",
            "PhysicalResourceId": "PreviousResourceId"
        }
        with Responder(event) as responder:
            pass

        responder._upload_response_data.assert_called_once()
        (_, (url, data), kwargs), = responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "PreviousResourceId",
            "Reason": "No response sent"
        })
        self.assertEqual(kwargs, {})

    def test_context_handler_forwards_physical_resource_id_in_failure_on_exception(self):
        event = {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "ResponseURL": "http://response",
            "PhysicalResourceId": "PreviousResourceId"
        }
        with self.assertRaisesRegexp(Exception, "Something happened"):
            with Responder(event) as responder:
                raise Exception("Something happened")

        responder._upload_response_data.assert_called_once()
        (_, (url, data), kwargs), = responder._upload_response_data.mock_calls
        self.assertEqual(url, "http://response")
        self.assertEqual(json.loads(data), {
            "StackId": "1",
            "RequestId": "2",
            "LogicalResourceId": "3",
            "Status": "FAILED",
            "PhysicalResourceId": "PreviousResourceId",
            "Reason": "Something happened"
        })
        self.assertEqual(kwargs, {})
