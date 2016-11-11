Custom Resource (AWS)
=====================

Implement `custom CloudFormation resources`_ with Python Lambda functions.

This let you reference non-AWS resources within CloudFormation - for instance,
let’s put a StatusCake alert in our stack:

.. code:: yaml

    Type: Custom::StatusCakeTest
    Version: 1.0
    Properties:
      WebsiteName: vitalwebsite.com
      WebsiteURL: http://vitalwebsite.com
      CheckRate: 300
      TestType: HTTP

(Implementation left as an exercise for the reader)

See also
--------

- Sample code in the ``examples`` directory.
-  `AWS docs`_

Lambda Handler
--------------

Here’s a simple resource:

.. code:: python

    from custom_resource import BaseHandler

    class Handler(BaseHandler):
        def create(self, event, context):
            return "CreatedId", {"AndSome": "MetaData"}

        def update(self, event, context):
            return "UpdatedId", {"AndSome": "MetaData"}

        def delete(self, event, context):
            return "DeletedId", {"AndSome": "MetaData"}

    handler = Handler()

We extend the ``BaseHandler`` class, and implement ``create``,
``update`` and ``delete`` methods. All of these methods are required.

The methods must either:

-  Return a string representing a resource ID. This can be used within
   your CFN template via the `Ref function`_.
-  Return a resource ID string, and a dict containing strings for keys
   and values. These key/value pairs can be used with the `GetAtt
   function`_.
-  Return a ``custom_resource.Success`` or ``custom_resource.Failed``
   object.
-  Return a ``custom_resource.Defer`` object, signifying you’ll process
   this asynchronously. See `async responses`_ below.
-  Raise an exception.

``BaseHandler`` will respond to CloudFormation unless ``Defer`` is
returned.

Async responses
----------------

Your ``Handler`` method can return ``Defer`` to signal asynchronous
processing.

To later respond, you need a copy of the original ``event`` object. This
will be passed to the ``Responder`` class, e.g:

.. code:: python

    with Responder(event) as responder:
        responder.success(physical_resource_id="123", data={"Meta": "Data"})
        # or
        responder.failure(physical_resource_id="456", reason="Something went wrong")

Using ``with``, your resource will always respond to CloudFormation even
on exception - ensuring your stack doesn’t stall and eventually timeout.

.. _custom CloudFormation resources: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-responses.html
.. _Ref function: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html
.. _GetAtt function: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html
.. _async responses: #async-responses
.. _AWS docs: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-responses.html
