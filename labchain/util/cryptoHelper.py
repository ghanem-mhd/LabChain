from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256
from base64 import b64encode, b64decode

from labchain.util.singleton import Singleton
from labchain.util.utility import Utility

import json
import logging


@Singleton
class CryptoHelper:
    """
    In order to use the CryptoHelper, please use CryptoHelper.instance() """

    def __init__(self):
        pass

    def sign(self, private_key, payload):
        """
        Hashes and signs the given payload with given private key.
        :param private_key: Private key of the signer in the string format.
        :param payload: JSON of the data to be signed.
        :return signature: signature in binary string format."""

        private_key = b64decode(private_key).decode()
        h = self.__hash(payload)  # Hash the payload
        signer = DSS.new(ECC.import_key(private_key), 'fips-186-3')  # Get the signature object
        signature = signer.sign(h)  # Sign the hash
        signature = b64encode(signature).decode('utf-8')
        logging.debug('Cryptohelper signed.')
        return signature

    def validate(self, pub_key, payload, signature):
        """
        Validates the signature and data pair with the signer's public key.
        :param pub_key: Public key of the signer in the string format.
        :param payload: JSON of the data that was signed.
        :param signature: Signature in binary string that was produced for the given data.
        :return result: True if signature and data pair matches, false otherwise."""

        pub_key = b64decode(pub_key).decode()
        h = self.__hash(payload)  # Hash the payload
        public_key = ECC.import_key(pub_key)  # Get the public key object using public key string
        verifier = DSS.new(public_key, 'fips-186-3')  # Create a signature object
        signature = b64decode(signature.encode('utf-8'))

        try:
            verifier.verify(h, signature)  # Check if the signature is verified
            result = True
            logging.debug('Cryptohelper verified.')

        except ValueError:
            result = False
            logging.debug('Cryptohelper failed to verify.')

        return result

    def generate_key_pair(self):
        """
        Generates a public and private ECC key pair.
        :return private_key: Private key in string format.
        :return public_key: Corresponding public key in string format."""

        key = ECC.generate(curve='P-256')  # Create ECC key object
        private_key = key.export_key(format='PEM')  # Get the string of private key
        public_key = key.public_key().export_key(format='PEM')  # Get the string of public key
        logging.debug('Cryptohelper created a new key pair.')
        return b64encode(private_key.encode()).decode(), b64encode(public_key.encode()).decode()

    def __hash(self, payload):
        try:
            real_payload = self.__unpack_payload(payload)  # Get the real payload to be hashed
        except ValueError:
            raise ValueError('Payload is not json')
        message = real_payload.encode()  # Encode string for hashing
        message_hash = SHA256.new(message)  # Hash using SHA256 scheme
        # logging.debug('Cryptohelper hashed.')
        return message_hash

    def hash(self, payload):
        """
        Hashes the given data.
        :param payload: Data to be hashed in JSON format.
        :return hash: SHA256 hash of the given data in hex representation. """
        hash_object = self.__hash(payload)  # Hash the payload
        return hash_object.hexdigest()  # Return hex representation of the hash

    def __unpack_payload(self, payload):

        if not Utility.is_json(payload):
            raise ValueError('Payload is not json')

        payload_dict = json.loads(payload)  # Get JSON string
        sorted_payload = sorted(payload_dict)  # Get the sorted list of keys

        real_payload = ""

        for i in sorted_payload:
            real_payload += str(payload_dict[i])  # Concatenate all values according to sorted keys

        return real_payload
