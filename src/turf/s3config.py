import base64

import boto3
import yaml

from .config import BaseConfig


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

    @classmethod
    def get_aws_client(cls, service):
        return boto3.client(service)

    @classmethod
    def get_s3_bucket(cls):
        s3_bucket = cls.get_config_dir()
        if "/" in s3_bucket:
            s3_bucket = s3_bucket.split("/")[0]
        return s3_bucket

    @classmethod
    def get_s3_path(cls, section_name):
        s3_path = cls.get_config_dir().split("/")
        if len(s3_path) == 1:
            # Configs are in root of bucket
            s3_path = ""
        else:
            # Configs are in a folder in a bucket
            s3_path = "/".join(s3_path[1:])
        s3_filename = "{0}.yml".format(section_name)
        return "{0}/{1}".format(s3_path, s3_filename)

    @classmethod
    def read_section_from_file(cls, section_name):
        """Loads a section from S3 and parses the YAML."""
        s3_client = cls.get_aws_client("s3")

        s3_response = s3_client.get_object(
            Bucket=cls.get_s3_bucket(),
            Key=cls.get_s3_path(section_name)
        )

        try:
            config_file_contents = s3_response["Body"].read(s3_response["ContentLength"])
        except:
            return {}

        if cls.encrypted:
            try:
                kms = cls.get_aws_client("kms")
                kms_response = kms.decrypt(
                    CiphertextBlob=base64.b64decode(config_file_contents)
                )
                config_file_contents = kms_response["Plaintext"]
            except:
                return {}

        if cls.safe_load:
            config_from_file = yaml.safe_load(config_file_contents)
        else:
            config_from_file = yaml.load(config_file_contents)

        if not hasattr(config_from_file, "items"):
            return {}
        return config_from_file


def save_config(config_class, config_file_contents, section_name, kms_key=None):
    import cerberus

    s3_client = config_class.get_aws_client("s3")

    if config_class.safe_load:
        config_dict = yaml.safe_load(config_file_contents)
    else:
        config_dict = yaml.load(config_file_contents)

    validator = config_class.get_validator(config_class.schema[section_name])
    valid = validator.validate(config_dict)

    if not valid:
        raise cerberus.ValidationError(",".join(["{0}: {1}".format(k, v) for (k, v) in validator.errors.items()]))

    if config_class.encrypted:
        kms_client = config_class.get_aws_client("kms")
        response = kms_client.encrypt(
            KeyId=kms_key,
            Plaintext=config_file_contents
        )
        config_file_contents = base64.b64encode(response["CiphertextBlob"])

    s3_client.put_object(
        Bucket=config_class.get_s3_bucket(),
        Key=config_class.get_s3_path(section_name),
        Body=config_file_contents
    )

    return config_file_contents


if __name__ == "__main__":
    import argparse
    import importlib

    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--section", dest="section_name")
    ap.add_argument("-C", "--config-class", dest="config_class")
    ap.add_argument("-K", "--kms-key", dest="kms_key")
    ap.add_argument("source_file")
    args = ap.parse_args()

    config_class_parts = args.config_class.split(".")
    config_class_module = importlib.import_module(".".join(config_class_parts[:-1]))
    config_class = getattr(config_class_module, config_class_parts[-1])

    with open(args.source_file, "rb") as f:
        config_file_contents = f.read()

    save_config(config_class, config_file_contents, args.section_name, args.kms_key)
