# -*- coding: utf-8 -*-
import json
import binascii
from .base import MyTestCase
from privacyidea.lib.tokens.HMAC import HmacOtp


class TwoStepInitTestCase(MyTestCase):
    """
    test the 2stepinit process.
    
    Here we enroll an HOTP token. One part of the secret key is generated by 
    privacyIDEA and the second part is generated by the client.
    
    A successful authentication with the new key is performed.
    """

    def test_01_init_token(self):
        with self.app.test_request_context('/token/init',
                                           method='POST',
                                           data={"type": "hotp",
                                                 "genkey": "1",
                                                 "2stepinit": "1"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is True, result)
            detail = json.loads(res.data).get("detail")
            serial = detail.get("serial")
            otpkey_url = detail.get("otpkey", {}).get("value")
            server_component = otpkey_url.split("/")[2]

        client_component = "AAAAAAAA"
        with self.app.test_request_context('/token/init',
                                           method='POST',
                                           data={"type": "hotp",
                                                 "serial": serial,
                                                 "otpkey": client_component},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status") is True, result)
            self.assertTrue(result.get("value") is True, result)
            detail = json.loads(res.data).get("detail")
            otpkey_url = detail.get("otpkey", {}).get("value")
            otpkey = otpkey_url.split("/")[2]

        # Now try to authenticate
        otpkey_bin = binascii.unhexlify(otpkey)
        otp_value = HmacOtp().generate(key=otpkey_bin, counter=1)
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"serial": serial,
                                                 "pass": otp_value}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertEqual(result.get("status"), True)
            self.assertEqual(result.get("value"), True)

        with self.app.test_request_context('/token/'+ serial,
                                           method='DELETE',
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
