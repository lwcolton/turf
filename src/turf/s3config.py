import base64

import botocore
import boto3
import cerberus
import yaml

from .config import BaseConfig
from .errors import ConfigurationNotFoundError


class S3Config(BaseConfig):
    """Provides a class for a configuration manager, with configs stored in S3.

    Normal boto3 options for specifying credentials to S3 apply.

    You are required to provide a schema for your configuration,
    either using :attr:`schema` or :meth:`get_schema`.  This
    should be a `cerberus schema <https://cerberus.readthedocs.org/en/latest/>`_.
    See :meth:`get_schema` for implementation details.

    :attr:`config_dir` should be an S3 path, including the bucket and any
    folders, that points to a directory containing the YAML files for this
    configuration.

    If :attr:`encrypted` is True, turf assumes that the configuration has been
    encrypted using KMS prior to storing in S3.
    """
    encrypted = False


    def get_aws_client(self, service):
        return boto3.client(service)


    def get_s3_bucket(self):
        s3_bucket = self.get_config_dir()
        if "/" in s3_bucket:
            s3_bucket = s3_bucket.split("/")[0]
        return s3_bucket


    def get_s3_path(self, section_name):
        s3_path = self.get_config_dir().split("/")
        if len(s3_path) == 1:
            # Configs are in root of bucket
            s3_path = ""
            s3_filename = "{0}.yml".format(section_name)
            return s3_filename
        else:
            # Configs are in a folder in a bucket
            s3_path = "/".join(s3_path[1:])
        s3_filename = "{0}.yml".format(section_name)
        return "{0}/{1}".format(s3_path, s3_filename)


    def read_section_from_file(self, section_name):
        """Loads a section from S3 and parses the YAML."""
        s3_client = self.get_aws_client("s3")
        bucket = self.get_s3_bucket()
        try:
            s3_response = s3_client.get_object(
                Bucket=bucket,
                Key=self.get_s3_path(section_name)
            )
        except botocore.exceptions.ClientError as client_error:
            if "NoSuchKey" in repr(client_error):
                return {}
            elif "NoSuchBucket" in repr(client_error):
                raise ConfigurationNotFoundError("Unable to get config from bucket: {0}: {1}".format(
                    bucket, repr(client_error)
                    )
                )
            else:
                raise

        try:
            config_file_contents = s3_response["Body"].read(s3_response["ContentLength"])
        except:
            return {}

        if self.encrypted:
            try:
                kms = self.get_aws_client("kms")
                kms_response = kms.decrypt(
                    CiphertextBlob=base64.b64decode(config_file_contents)
                )
                config_file_contents = kms_response["Plaintext"]
            except:
                return {}

        if self.safe_load:
            config_from_file = yaml.safe_load(config_file_contents)
        else:
            config_from_file = yaml.load(config_file_contents)

        if not hasattr(config_from_file, "items"):
            return {}
        return config_from_file

    @classmethod
    def save_config(cls, config_file_contents, section_name, config=None, kms_key=None):
        if config is None:
            config = cls()
        s3_client = config.get_aws_client("s3")

        if config.safe_load:
            config_dict = yaml.safe_load(config_file_contents)
        else:
            config_dict = yaml.load(config_file_contents)

        validator = config.get_validator(config.schema[section_name])
        valid = validator.validate(config_dict)

        if not valid:
            raise cerberus.ValidationError(",".join(["{0}: {1}".format(k, v) for (k, v) in validator.errors.items()]))

        if config.encrypted:
            kms_client = config.get_aws_client("kms")
            response = kms_client.encrypt(
                KeyId=kms_key,
                Plaintext=config_file_contents
            )
            config_file_contents = base64.b64encode(response["CiphertextBlob"])

        s3_client.put_object(
            Bucket=config.get_s3_bucket(),
            Key=config.get_s3_path(section_name),
            Body=config_file_contents
        )

        return config_file_contents

save_config = S3Config.save_config


if __name__ == "__main__":
    import argparse
    import importlib

    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--section", dest="section_name")
    ap.add_argument("-C", "--config-class", dest="config")
    ap.add_argument("-K", "--kms-key", dest="kms_key")
    ap.add_argument("source_file")
    args = ap.parse_args()

    config_parts = args.config.split(".")
    config_module = importlib.import_module(".".join(config_parts[:-1]))
    config = getattr(config_module, config_parts[-1])()

    with open(args.source_file, "rb") as f:
        config_file_contents = f.read()
    save_config(config_file_contents, args.section_name, config=config, kms_key=args.kms_key)
