import base64
import unittest
from unittest.mock import MagicMock, patch, sentinel

import yaml
from turf.s3config import S3Config, save_config


class MyConfig(S3Config):
    config_dir = "{0}/{1}".format(sentinel.bucket, sentinel.path)
    schema = {
        str(sentinel.section): {
            str(sentinel.key): {"type": "string"}
        }
    }


class MyEncryptedConfig(MyConfig):
    encrypted = True


mock_config_dict = {
    str(sentinel.key): str(sentinel.value)
}

raw_yaml_body = yaml.dump(mock_config_dict)


MockValidator = MagicMock()
MockValidator.validate = MagicMock(return_value=True)


MockStreamingBody = MagicMock()
MockStreamingBody.read = MagicMock(return_value=raw_yaml_body)

MockAwsClient = MagicMock()
MockAwsClient.get_object = MagicMock(return_value={
    "Body": MockStreamingBody,
    "ContentLength": sentinel.content_length
})
MockAwsClient.put_object = MagicMock()
MockAwsClient.decrypt = MagicMock(return_value={
    "Plaintext": raw_yaml_body
})
MockAwsClient.encrypt = MagicMock(return_value={
    "CiphertextBlob": str(sentinel.ciphertext_blob).encode()
})


class TestS3Config(unittest.TestCase):

    def test_s3_bucket(self):
        self.assertEqual(MyConfig.get_s3_bucket(), str(sentinel.bucket))

    def test_s3_path(self):
        expected_path = "{0}/{1}.yml".format(sentinel.path, sentinel.section)
        self.assertEqual(MyConfig.get_s3_path(sentinel.section), expected_path)

    def test_get_aws_client(self):
        with patch("boto3.client") as boto3_client:
            MyConfig.get_aws_client(sentinel.aws_service)
            boto3_client.assert_called_with(sentinel.aws_service)

    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_calls_s3(self, yaml_mock, aws_mock):
        result = MyConfig.read_section_from_file(sentinel.section)
        aws_mock.assert_called_with("s3")

    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_calls_get_object(self, yaml_mock, aws_mock):
        result = MyConfig.read_section_from_file(sentinel.section)
        aws_mock.return_value.get_object.assert_called_with(
            Bucket=str(sentinel.bucket),
            Key="{0}/{1}.yml".format(sentinel.path, sentinel.section)
        )

    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_reads_response(self, yaml_mock, aws_mock):
        result = MyConfig.read_section_from_file(sentinel.section)
        mock_body = aws_mock.return_value.get_object.return_value
        mock_body["Body"].read.assert_called_with(sentinel.content_length)

    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_parses_yaml(self, yaml_mock, aws_mock):
        result = MyConfig.read_section_from_file(sentinel.section)
        yaml_mock.assert_called_with(raw_yaml_body)

    @patch("base64.b64decode", return_value=raw_yaml_body)
    @patch.object(MyEncryptedConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_encrypted_s3config_calls_decrypt(self, yaml_mock, aws_mock, base64_mock):
        result = MyEncryptedConfig.read_section_from_file(str(sentinel.section))
        aws_mock.return_value.decrypt.assert_called_with(
            CiphertextBlob=raw_yaml_body
        )

    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_returns_config(self, yaml_mock, aws_mock):
        result = MyConfig.read_section_from_file(str(sentinel.section))
        self.assertEqual(result, mock_config_dict)

    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=None)
    def test_s3config_parse_failure_returns_empty_dict(self, yaml_mock, aws_mock):
        result = MyConfig.read_section_from_file(str(sentinel.section))
        self.assertEqual(result, {})


class TestSaveConfig(unittest.TestCase):
    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value={})
    def test_save_config_parses_config(self, yaml_mock, aws_mock):
        result = save_config(MyConfig, raw_yaml_body, str(sentinel.section), None)
        yaml_mock.assert_called_with(raw_yaml_body)

    @patch.object(MyConfig, "get_validator", return_value=MockValidator)
    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    def test_save_config_validates_config(self, aws_mock, validator_mock):
        result = save_config(MyConfig, raw_yaml_body, str(sentinel.section), None)
        MyConfig.get_validator.assert_called_with(MyConfig.schema[str(sentinel.section)])
        validator_mock.return_value.validate.assert_called_with(mock_config_dict)

    @patch.object(MyEncryptedConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_save_config_calls_encrypt(self, yaml_mock, aws_mock):
        result = save_config(MyEncryptedConfig, raw_yaml_body, str(sentinel.section), str(sentinel.kms_key))
        aws_mock.return_value.encrypt.assert_called_with(
            KeyId=str(sentinel.kms_key),
            Plaintext=raw_yaml_body
        )

    @patch.object(MyConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_save_config_calls_put_object(self, yaml_mock, aws_mock):
        result = save_config(MyConfig, raw_yaml_body, str(sentinel.section), None)
        aws_mock.return_value.put_object.assert_called_with(
            Bucket=MyConfig.get_s3_bucket(),
            Key=MyConfig.get_s3_path(str(sentinel.section)),
            Body=raw_yaml_body
        )

    @patch.object(MyEncryptedConfig, "get_aws_client", return_value=MockAwsClient)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_save_config_saves_encrypted_config(self, yaml_mock, aws_mock):
        result = save_config(MyEncryptedConfig, raw_yaml_body, str(sentinel.section), str(sentinel.kms_key))
        aws_mock.return_value.put_object.assert_called_with(
            Bucket=MyConfig.get_s3_bucket(),
            Key=MyConfig.get_s3_path(str(sentinel.section)),
            Body=base64.b64encode(str(sentinel.ciphertext_blob).encode())
        )
