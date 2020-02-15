import logging
import re
from logging import Logger
from uuid import uuid4

import requests

from pyfinnotech.exceptions import FinnotechException

URL_SANDBOX = 'https://sandboxapi.finnotech.ir/'
URL_MAINNET = 'https://sandboxapi.finnotech.ir/'


class FinnotechApiClient:
    def __init__(
            self,
            is_sandbox=False,
            client_id=False,
            logger: Logger = None,
            requests_extra_kwargs: dict = None
    ):
        self.bse_url = URL_SANDBOX if is_sandbox is True else URL_MAINNET
        self.logger = logger or logging.getLogger('pyfinnotech')
        self.client_id = ''
        self.requests_extra_kwargs = requests_extra_kwargs or {}

    @classmethod
    def _generate_track_id(cls):
        return uuid4().hex

    @property
    def _client_credential(self):
        return ''

    def _execute(self, uri, params, error_mapper=None):
        params = params or dict()
        track_id = self._generate_track_id()
        params.setdefault('trackId', track_id)
        self.logger.debug(f"Requesting"
                          f" on {uri} with id:{track_id}"
                          f" with parameters: {'.'.join(str(params))}")

        try:
            response = requests.get(
                self.server_url,
                params=params,
                headers={
                    'Authorization': f'Bearer {self.client_id}'
                },
                **self.requests_extra_kwargs
            ).json()
        except Exception as e:
            raise FinnotechException(f"Request error: {str(e)}")

        return response

    def _get_authorization_code(self):
        """
        https://sandboxbeta.finnotech.ir/v2/boomrang-get-authorizationCode-token.html?sandbox=true
        :return:
        """
        url = f'{self.base_url}/dev/v2/oauth2/token'

    def deposit_owner_verification(self):
        url = f'/facility/v2/clients/{self.client_id}/' \
              f'depositOwnerVerification?deposit={deposit}&bank={bank}&nationalCode={nid}'

        params = {
            ''
        }

    def iban_inquiry(self, iban):
        """
        https://devbeta.finnotech.ir/oak-ibanInquiry.html

        شرح: سرویس اطلاعات شبا

        اسکوپ: oak:iban-inquiry:get

        رویکرد: Client-Credential

        {address}/oak/v2/clients/{clientId}/ibanInquiry?trackId={trackId}&iban={iban}
        https://apibeta.finnotech.ir :address
        Headers
        مقادیر زیر باید در هدر قرار بگیرد

        Authorization : Bearer {Token}
        برای فراخوانی این سرویس باید از توکن CLIENT_CREDENTIAL استفاده نمایید.
        URI Parameters
        clientId : (اجباری) شناسه کلاینت
        Query Parameters
        trackId: اختیاری (string) ‫ کد پیگیری، رشته ای اختیاری با طول حداکثر ۴۰ کاراکتر شامل حرف و عدد. در صورت ارسال trackId، فراخوانی سرویس خود را با همین مقدار استعلام و پیگیری کنید.(در گزارش فراخوانی سرویس ها با همین رشته نتیجه را ببینید). در صورتیکه که این فیلد را ارسال نکنید یک رشته UUID برای این فراخوانی در نظر گرفته میشود و در پاسخ فراخوانی برگردانده میشود.
        example: get-iban-inquiry-029
        iban: شماره شبای معتبر که باید یک رشته به طول ۲۶ کاراکتر باشد
        example: IR910800005000115426432001

        :param iban: Example: IR910800005000115426432001
        :return:

          {
            "result": {
              "IBAN": "IR910800005000115426432001"
            , "bankName": "قرض الحسنه رسالت"
            , "deposit": "10.6423499.1"
            , "depositStatus": "02"
            , "depositDescription": "حساب فعال است"
            , "depositComment": "سپرده حقيقي قرض الحسنه پس انداز حقيقي ريالی شیما کیایی"
            , "depositOwners": [
                  {
                    "firstName": "شیما"
                  , "lastName": "کیایی"
                  }
              ],
              "alertCode": "00"
          },
          , "status": "DONE"
          , "trackId": "get-iban-inquiry-029"
          }


        result: آبجکتی از پاسخ سرویس شامل:
            IBAN: شماره شبا
            bankName: نام بانک
            deposit: شماره حساب
            depositStatus: میتواند مقادیر زیر را بگیرد
                ‌02 : حساب فعال است
                ‌03 : حساب مسدود با قابلیت واریز
                ‌04 : حساب مسدود بدون قابلیت واریز
                ‌05 : حساب راکد است
                ‌06 : بروز خطادر پاسخ دهی , شرح خطا در فیلد توضیحات است
                ‌07 : سایر موارد
            depositDescription: شرح حساب
            depositComment:
            depositOwners: آرایه ای از صاحبان حساب
                firstName: نام
                lastName: نام خانوادگی
            alertCode: میتواند مقادیر زیر را بگیرد
                ‌00 : بدون خطا
                ‌01 : Invalid IBAN
                ‌02 : Invalid Request
                ‌03 : Message Authentication Failed
                ‌04 : Invalid Bank Bic Code
                ‌05 : Destination Time Out
                ‌06 : Destination Not Found
        status: وضعیت فراخوانی سرویس
            DONE: فراخوانی موفق سرویس
            FAILED: فراخوانی ناموفق سرویس
            error: جزییات خطا (در صورت بروز خطا)
        trackId: ‌ کد پیگیری، اگر ارسال شده باشد همان مقدار و در غیر اینصورت یک رشته تصادفی تولید و برگردانده میشود

        """

        if iban is None or re.match('^IR(0-9){26}$', iban):
            raise ValueError(f'Bad iban: {iban}')

        url = f'/oak/v2/clients/{self.client_id}/ibanInquiry'
        return self._execute(url, {'iban': iban})
