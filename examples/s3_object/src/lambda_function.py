from custom_resource import BaseHandler
import boto3

class Handler(BaseHandler):
    """
    Example custom resource: manage S3 object contents.
    """

    # Optional JSON schema - validates ResourceProperties and
    # OldResourceProperties. Must account for ServiceToken as that's always
    # present.
    RESOURCE_PROPERTIES = {
        "additionalProperties": False,
        "required": ["Bucket", "Key", "Body", "ContentType"],
        "properties": {
            "Bucket": {"type": "string"},
            "Key": {"type": "string"},
            "Body": {"type": "string"},
            "ContentType": {"type": "string"}
        }
    }

    def __init__(self):
        super(Handler, self).__init__()
        self.client = boto3.client("s3")

    def create(self, event, context):
        bucket = event["ResourceProperties"]["Bucket"]
        key = event["ResourceProperties"]["Key"]
        body = event["ResourceProperties"]["Body"]
        content_type = event["ResourceProperties"]["ContentType"]

        self.client.put_object(
            ACL="public-read",
            Body=body,
            Bucket=bucket,
            ContentType=content_type,
            Key=key
        )

        return key

    def update(self, event, context):
        # Create/update is essentially the same thing for S3 objects.
        return self.create(event, context)

    def delete(self, event, context):
        bucket = event["ResourceProperties"]["Bucket"]
        key = event["ResourceProperties"]["Key"]

        self.client.delete_object(
            Bucket=bucket,
            Key=key
        )

        return key

lambda_handler = Handler()
