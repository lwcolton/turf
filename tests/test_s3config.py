import base64
import unittest
from unittest.mock import MagicMock, patch, sentinel, Mock

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

    def setUp(self):
        self.boto3_patch = patch("boto3.client")
        self.boto3_mock = self.boto3_patch.start()

        with patch.object(MyConfig, "read_section_from_file") as mock_read_section:
            self.config = MyConfig()

        with patch.object(MyEncryptedConfig, "read_section_from_file") as mock_read_section:
            self.kms_config = MyEncryptedConfig()


    def tearDown(self):
        patch.stopall()

    def test_s3_bucket(self):
        self.assertEqual(self.config.get_s3_bucket(), str(sentinel.bucket))

    def test_s3_path(self):
        expected_path = "{0}/{1}.yml".format(sentinel.path, sentinel.section)
        self.assertEqual(self.config.get_s3_path(sentinel.section), expected_path)

    def test_get_aws_client(self):    
        self.config.get_aws_client(sentinel.aws_service)
        self.boto3_mock.assert_called_with(sentinel.aws_service)

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_calls_s3(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = self.config.read_section_from_file(sentinel.section)
        aws_mock.assert_called_with("s3")

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_calls_get_object(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = self.config.read_section_from_file(sentinel.section)
        aws_mock.return_value.get_object.assert_called_with(
            Bucket=str(sentinel.bucket),
            Key="{0}/{1}.yml".format(sentinel.path, sentinel.section)
        )

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_reads_response(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = self.config.read_section_from_file(sentinel.section)
        mock_body = aws_mock.return_value.get_object.return_value
        mock_body["Body"].read.assert_called_with(sentinel.content_length)

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_parses_yaml(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = self.config.read_section_from_file(sentinel.section)
        yaml_mock.assert_called_with(raw_yaml_body)

    @patch("base64.b64decode", return_value=raw_yaml_body)
    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_encrypted_s3config_calls_decrypt(self, yaml_mock, base64_mock):
        aws_mock = patch.object(self.kms_config, "get_aws_client", return_value=MockAwsClient).start()
        result = self.kms_config.read_section_from_file(str(sentinel.section))
        aws_mock.return_value.decrypt.assert_called_with(
            CiphertextBlob=raw_yaml_body
        )

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_s3config_returns_config(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = self.config.read_section_from_file(str(sentinel.section))
        self.assertEqual(result, mock_config_dict)

    @patch("yaml.safe_load", return_value=None)
    def test_s3config_parse_failure_returns_empty_dict(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = self.config.read_section_from_file(str(sentinel.section))
        self.assertEqual(result, {})

    @patch("yaml.safe_load", return_value={})
    def test_save_config_parses_config(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = save_config(self.config, raw_yaml_body, str(sentinel.section), None)
        yaml_mock.assert_called_with(raw_yaml_body)

    def test_save_config_validates_config(self):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        validator_mock = patch.object(self.config, "get_validator", return_value=MockAwsClient).start()
        result = save_config(self.config, raw_yaml_body, str(sentinel.section), None)
        self.config.get_validator.assert_called_with(self.config.schema[str(sentinel.section)])
        validator_mock.return_value.validate.assert_called_with(mock_config_dict)

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_save_config_calls_encrypt(self, yaml_mock):
        aws_mock = patch.object(self.kms_config, "get_aws_client", return_value=MockAwsClient).start()
        result = save_config(self.kms_config, raw_yaml_body, str(sentinel.section), str(sentinel.kms_key))
        aws_mock.return_value.encrypt.assert_called_with(
            KeyId=str(sentinel.kms_key),
            Plaintext=raw_yaml_body
        )

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_save_config_calls_put_object(self, yaml_mock):
        aws_mock = patch.object(self.config, "get_aws_client", return_value=MockAwsClient).start()
        result = save_config(self.config, raw_yaml_body, str(sentinel.section), None)
        aws_mock.return_value.put_object.assert_called_with(
            Bucket=self.config.get_s3_bucket(),
            Key=self.config.get_s3_path(str(sentinel.section)),
            Body=raw_yaml_body
        )

    @patch("yaml.safe_load", return_value=mock_config_dict)
    def test_save_config_saves_encrypted_config(self, yaml_mock):
        aws_mock = patch.object(self.kms_config, "get_aws_client", return_value=MockAwsClient).start()
        result = save_config(self.kms_config, raw_yaml_body, str(sentinel.section), str(sentinel.kms_key))
        aws_mock.return_value.put_object.assert_called_with(
            Bucket=self.kms_config.get_s3_bucket(),
            Key=self.kms_config.get_s3_path(str(sentinel.section)),
            Body=base64.b64encode(str(sentinel.ciphertext_blob).encode())
        )

    def test_get_s3_path(self):
        '''
        test for single name in top level dir
        '''
        self.config.get_s3_path = Mock(return_value='file.yml')
        response = self.config.get_s3_path(str(sentinel.section))
        self.assertEqual('file.yml',response)
