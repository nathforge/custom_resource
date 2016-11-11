# Custom resource example: S3 objects

This example adds an S3 Object custom resource, uploading and deletes object
data on behalf of a CloudFormation stack.

There are two templates:

  * resource.yml: Provides the custom resource.
  * consumer.yml: Example use of the resource.

## Deploy

To deploy the stacks:

```shell
$ bin/deploy
[...]
```

And to tear-down:

```shell
$ bin/destroy
```
