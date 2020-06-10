import logging
import re
from logging import Logger
from uuid import uuid4

import requests

from pyfinnotech.const import URL_SANDBOX, URL_MAINNET, ALL_SCOPE_CLIENT_CREDENTIALS, ALL_SCOPE_AUTHORIZATION_TOKEN
from pyfinnotech.responses import IbanInquiryResponse, CardInquiryResponse, StandardReliabilitySms, \
    NationalIdVerification, CardToIbanResponse
from pyfinnotech.token import ClientCredentialToken, Token, FacilitySmsAccessTokenToken
from pyfinnotech.exceptions import FinnotechException


class FinnotechApiClient:
    def __init__(
            self,
            client_id,
            client_secret=None,
            client_national_id=None,
            scopes=None,
            is_sandbox=False,
            logger: Logger = None,
            requests_extra_kwargs: dict = None,
            client_credential_token=None,
            client_credential_refresh_token=None,
            authorization_token=None,
            base_url=None
    ):
        self.server_url = base_url or (URL_SANDBOX if is_sandbox is True else URL_MAINNET)
        self.logger = logger or logging.getLogger('pyfinnotech')
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_national_id = client_national_id
        self.scopes = scopes or ALL_SCOPE_CLIENT_CREDENTIALS + ALL_SCOPE_AUTHORIZATION_TOKEN
        self.requests_extra_kwargs = requests_extra_kwargs or {}
        self._client_credential_token = None
        if client_credential_token is not None:
            self._client_credential_token = ClientCredentialToken.load(
                raw_token=client_credential_token,
                refresh_token=client_credential_refresh_token
            )

    @classmethod
    def _generate_track_id(cls):
        return uuid4().__str__()

    @property
    def client_credential(self) -> ClientCredentialToken:
        if self._client_credential_token is not None and self._client_credential_token.is_valid is True:
            pass
        else:
            self._client_credential_token = ClientCredentialToken.fetch(self)
        return self._client_credential_token

    def _execute(self, uri, method='get', params=None, headers=None, body=None, token: Token = None,
                 error_mapper=None, no_track_id=False):
        params = params or dict()
        headers = headers or dict()
        track_id = self._generate_track_id() if no_track_id is False else None
        if track_id is not None:
            params.setdefault('trackId', track_id)
        self.logger.debug(f"Requesting"
                          f" on {uri} with id:{track_id}"
                          f" with parameters: {'.'.join(str(params))}")

        if token is not None:
            headers = {**headers, **token.generate_authorization_header()}

        try:
            response = requests.request(
                method,
                ''.join([self.server_url, uri]),
                params=params,
                headers=headers,
                json=body,
                **self.requests_extra_kwargs
            )

            if response.status_code == 403:
                self.logger.info('Trying to refresh token')
                token.refresh(self)

                response = requests.request(
                    method,
                    ''.join([self.server_url, uri]),
                    params=params,
                    headers=headers,
                    json=body,
                    **self.requests_extra_kwargs
                )

            if response.status_code != 200:
                raise FinnotechException(response.content.decode(), self.logger)

            return response.json()

        except Exception as e:
            raise FinnotechException(f"Request error: {str(e)}", logger=self.logger)

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

        if iban is None or not re.match('^IR[0-9]{24}$', iban):
            raise ValueError(f'Bad iban: {iban}')

        url = f'/oak/v2/clients/{self.client_id}/ibanInquiry'
        return IbanInquiryResponse(self._execute(
            uri=url,
            token=self.client_credential,
            params={'iban': iban}
        ).get('result'))

    def card_inquiry(self, card):
        """
        https://devbeta.finnotech.ir/card-information.html

        شرح: برای استعلام شماره کارت های عضو شتاب از این سرویس استفاده کنید.

        اسکوپ: card:information:get

        رویکرد: Client_Credential

        {address}/mpg/v2/clients/{clientId}/cards/{card}?trackId={trackId}
        https://apibeta.finnotech.ir :address
        URI Parameters
        clientId: شناسه کلاینت
        card: شماره کارت ۱۶ رقمی
        Headers
        مقادیر زیر باید در هدر قرار بگیرد

        Authorization : Bearer {Token}
        Query Parameters
        trackId: کد پیگیری، رشته ای اختیاری با طول حداکثر ۴۰ کاراکتر شامل حرف و عدد. در صورت ارسال trackId، فراخوانی سرویس خود را با همین مقدار استعلام و پیگیری کنید.(در گزارش فراخوانی سرویس ها با همین رشته نتیجه را ببینید). در صورتیکه که این فیلد را ارسال نکنید یک رشته UUID برای این فراخوانی در نظر گرفته میشود و در پاسخ فراخوانی برگردانده میشود.

        example: get-cardInfo-0232
        Results Format
        Successful result format (status code 200)
          {
            "result": {
                "destCard":"xxxx-xxxx-xxxx-3899"
              , "name":"علی آقایی"
              , "result":"0"
              , "description":"موفق"
              , "doTime":"1396/06/15 12:32:04"
              }
          , "status": "DONE"
          , "trackId": "get-cardInfo-0232"
          }
        result: آبجکتی از پاسخ سرویس شامل:
        destCard: شماره کارت به صورت xxxx-xxxx-xxxx-{چهار رقم آخر شماره کارت}
        name: نام صاحب کارت
        result: نتیجه فراخوانی سرویس، برای اطلاع از مقادیر این فیلد به اینجا مراجعه کنید
        description: توضیحات تکمیلی در مورد نتیجه
        doTime: زمان انجام تراکنش
        status: وضعیت فراخوانی سرویس
        DONE: فراخوانی موفق سرویس
        FAILED: فراخوانی ناموفق سرویس
        error: جزییات خطا (در صورت بروز خطا)
        trackId: کد پیگیری، اگر ارسال شده باشد همان مقدار برگردانده میشود و در غیر اینصورت یک رشته تصادفی تولید و برگردانده میشود

        """

        # TODO: Add luhn check to reduce api call rate

        if card is None or not re.match('^[0-9]{16}$', card):
            raise ValueError(f'Bad card: {card}')

        url = f'/mpg/v2/clients/{self.client_id}/cards/{card}'
        return CardInquiryResponse(self._execute(
            uri=url,
            token=self.client_credential,
        ).get('result'))

    def standard_reliability(self, national_id, phone_number, otp):
        """
        https://sandboxbeta.finnotech.ir/v2/credit-standard-v3.html
        شرح: سرویس اعتبارسنجی استاندارد با گرفتن کد ملی، اطلاعات اعتبار صاحب کد ملی میدهد.

        اسکوپ: credit:cc-standard-reliability:get

        رویکرد: Client_Credential

        {address}/credit/v2/clients/{clientId}/users/{user}/standardReliability?otp={otp}&phoneNumber={phoneNumber}&trackId={trackId}
        https://sandboxapi.finnotech.ir :address
        Headers
        مقادیر زیر باید در هدر قرار بگیرد

        CLIENT-CREDENTIAL : Bearer {Token}
        برای فراخوانی این سرویس لازم است با توکن CLIENT CREDENTIAL سرویس را فراخوانی نمایید.
        URI Parameters
        clientId:شناسه کلاینت
        user : (اجباری) کد ملی کاربر که میخواهید اطلاعات آن را دریافت کنید و باید رشته عددی به طول ۱۰ رقم باشد
        Query Parameters
        trackId: اختیاری (string) ‫ کد پیگیری، رشته ای اختیاری با طول حداکثر ۴۰ کاراکتر شامل حرف و عدد. در صورت ارسال trackId، فراخوانی سرویس خود را با همین مقدار استعلام و پیگیری کنید.(در گزارش فراخوانی سرویس ها با همین رشته نتیجه را ببینید). در صورتیکه که این فیلد را ارسال نکنید یک رشته UUID برای این فراخوانی در نظر گرفته میشود و در پاسخ فراخوانی برگردانده میشود.

        example: getUserinfo876543
        phoneNumber: اجباری (string) ‫ شماره ی موبایلی که کد یکبار مصرف به آن ارسال شده و توجه شود که این شماره باید به نام کسی که کد ملی مورد اعتبارسنجی برای اوست ثبت شده باشد

        example: 09192589756
        otp: اجباری (string) ‫ کد چهار رقمی ارسال شده به شماره موبایل

        example: 1234
        Results Format
        Successful result format (status code 200)
               {
               "trackId": "4a12a4ce-10ab-49fe-b542-9bc00501c8f6",
               "result": {
               "result": {
               "result": {
               "State": 1,
               "Valid": true,
               "Score": {
               "Commands": {
               "Command": {
               "_identifier": "1",
               "Cis.CB4.Projects.IR.IranCreditScoring.Reports.Body.Products.ScoringIndividualReport.Response": {
               "Reports.PersonalInformation": {
               "PersonalCode": "0011001100",
               "FathersName": "اصغر",
               "FirstName": "فاطمه",
               "Surname": "تستی",
               "Lookups.Gender": "Gender.Female",
               "DateOfBirth": "1982-09-02T19:30:00Z"
               },
               "Reports.Lookups.ReportStatus": "ReportStatus.OK",
               "Reports.ScoringInformation": {
               "ICSScore": "556",
               "RiskGrade": "RiskGrade.C2",
               "ReasonCodes": {
               "ReasonCodeList": [
               {
               "_key": "0",
               "ReasonCode": "CIPSReasonCodes.AGE1"
               },
               {
               "_key": "1",
               "ReasonCode": "CIPSReasonCodes.NMN2"
               },
               {
               "_key": "2",
               "ReasonCode": "CIPSReasonCodes.AMN2"
               },
               {
               "_key": "3",
               "ReasonCode": "CIPSReasonCodes.INQ3"
               }
               ]
               },
               "ScoreRange": "540 - 559",
               "ScoreDescription": "ScoreDescription.AverageRisk"
               },
               "ScoringReportComments": [],
               "ReportDate": "2019-09-22T10:23:08.9727303Z"
               }
               }
               }
               },
               "Report": {
               "Commands": {
               "Command": {
               "_identifier": "1",
               "Cis.CB4.Projects.IR.IranCreditScoring.Reports.Body.Products.StandardIndividualReport.Response": {
               "Reports.EmptyIndividualData": {
               "Types.Subject.Individual.PersonalCode": "0011001100"
               },
               "Reports.BasicIndividualData": {
               "Relations.Subjects.PersonalData": {
               "Types.Subject.Individual.FarthersName": "اصغر",
               "Types.Subject.Individual.FirstName": "فاطمه",
               "Types.Subject.Individual.Surname": "تستی",
               "Lookups.Gender": "Gender.Female",
               "Lookups.MaritalStatus": "MaritalStatus.Single",
               "Lookups.BorrowerClassification": "BorrowerClassification.Individual"
               },
               "Relations.Subjects.BirthData": {
               "Types.Subject.BirthData.BirthSurname": "تستی",
               "Types.Subject.BirthData.DateOfBirth": "1982-09-02T19:30:00Z",
               "Types.Subject.BirthData.PlaceOfBirth": "54002",
               "Lookups.CountryOfBirth": "CountryCodes.IR"
               },
               "Reports.SubjectData.Current.NegativeSubjectStatus": [
               {
               "_key": "00",
               "Reports.LastUpdate": "2017-03-19T19:30:00Z",
               "Lookups.NegativeSubjectStatus": "NegativeStatusOfSubject.NoNegativeStatus",
               "Reports.Creditor": "بانک ملی"
               },
               {
               "_key": "01",
               "Reports.LastUpdate": "2018-07-10T19:30:00Z",
               "Lookups.NegativeSubjectStatus": "NegativeStatusOfSubject.NoNegativeStatus",
               "Reports.Creditor": "صندوق علوم"
               }
               ]
               },
               "Reports.SubjectData.AddressesIndividual": {
               "Reports.Addresses.PermanentAddress": {
               "_key": "1",
               "Relations.Addresses.AddressTypeChoice": {
               "Relations.Addresses.TextAddress": {
               "Types.Subject.Address.TextAddress": "اطلاعات هدف مندي"
               }
               }
               }
               },
               "Reports.SubjectData.Contacts": {
               "Reports.Contacts.Cellular": {
               "_key": "0",
               "Types.Subject.Communication.ContactNumber": "09192760754"
               },
               "Reports.Contacts.Phone": {
               "_key": "0",
               "Types.Subject.Communication.ContactNumber": "-"
               }
               },
               "Reports.Inquiries": {
               "Reports.Inquiries.LastMonth": "16",
               "Reports.Inquiries.ThreeMonths": "16",
               "Reports.Inquiries.SixMonths": "16",
               "Reports.Inquiries.TwelveMonths": "16"
               },
               "Reports.Summary": {
               "Reports.Summary.TotalDebtOverdue": {
               "_key": "IRR",
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.Summary.TotalNumberOfUnpaidInstalments": "0",
               "Reports.Summary.TotalOutstandingAmount": {
               "_key": "IRR",
               "Types.Amount": "39583333.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.Summary.NumberOfExistingOperations": "2",
               "Reports.Summary.NumberOfTerminatedOperations": "0",
               "Reports.Summary.NegativeStatusReported": {
               "_key": "00",
               "Lookups.NegativeContractStatus": "NegativeContractStatus.DoubtfulDebt",
               "Reports.LastUpdate": "2018-07-10T19:30:00Z",
               "Reports.Creditor": "صندوق علوم"
               }
               },
               "Reports.SummaryCreditors": {
               "Reports.SummaryCreditor": [
               {
               "_key": "11",
               "Reports.Creditor": "بانک ملی",
               "Reports.Summary.TotalDebtOverdue": {
               "_key": "IRR",
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.Summary.TotalNumberOfUnpaidInstalments": "0",
               "Reports.Summary.TotalOutstandingAmount": {
               "_key": "IRR",
               "Types.Amount": "39583333.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.Summary.NumberOfExistingOperations": "1",
               "Reports.Summary.NumberOfTerminatedOperations": "0"
               },
               {
               "_key": "55",
               "Reports.Creditor": "صندوق علوم",
               "Reports.Summary.TotalDebtOverdue": {
               "_key": "IRR",
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.Summary.TotalNumberOfUnpaidInstalments": "0",
               "Reports.Summary.TotalOutstandingAmount": {
               "_key": "IRR",
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.Summary.NumberOfExistingOperations": "1",
               "Reports.Summary.NumberOfTerminatedOperations": "0",
               "Reports.Summary.NegativeStatusReported": {
               "_key": "00",
               "Lookups.NegativeContractStatus": "NegativeContractStatus.DoubtfulDebt",
               "Reports.LastUpdate": "2018-07-10T19:30:00Z"
               }
               }
               ]
               },
               "Reports.BaseDataOperations": {
               "Reports.ContractData.ExistingOperationsDebtor": {
               "Reports.ContractData.Instalments": {
               "Reports.ContractData.Instalment": {
               "_key": "0",
               "Relations.Contracts.InstalmentDetails": {
               "Lookups.TypeOfFinancingInstalments": "TypeOfFinancingInstalments.QarzAlHassaneh",
               "Lookups.TypeOfInstalments": "TypeOfInstalments.Fixed",
               "Lookups.PeriodicityOfPayments": "PeriodicityOfPayments.AtTheFinalDayOfThePeriodOfContract",
               "Lookups.MethodOfPayment": "MethodOfPayment.DirectRemittance",
               "Relations.Amounts.TotalCredit": {
               "Types.Amount": "100000000.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Types.Contract.NumberOfInstalments": "48",
               "Relations.Amounts.StandardPeriodicalInstalment": {
               "Types.Amount": "2083333.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Relations.Amounts.Overdue": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Types.Contract.OutstandingInstalments": "19",
               "Relations.Amounts.Outstanding": {
               "Types.Amount": "39583333.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               }
               },
               "Reports.HistoricalCalendar.Instalment": {
               "Reports.HistoricalCalendar.InstalmentRecord": [
               {
               "_key": "139706",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "6000.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "6",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139707",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "6333.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "7",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139708",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "6667.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "8",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139709",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "7000.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "9",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139710",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "7333.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "10",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139711",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "7667.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "11",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139712",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "12",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139801",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "2091333.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "1",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139802",
               "Types.Contract.OverdueInstalments": "1",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "2091667.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "2",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139803",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "3",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139804",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "4",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139805",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "5",
               "Reports.HistoricalCalendar.Year": "1398"
               }
               ]
               },
               "Reports.ContractData.GeneralInformation": {
               "Lookups.NegativeContractStatus": "NegativeContractStatus.NoNegativeStatus",
               "Relations.Contracts.Dates": {
               "Types.Contract.Dates.Start": "2017-02-24T20:30:00Z",
               "Types.Contract.Dates.ExpectedEnd": "2021-02-24T20:30:00Z"
               },
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR",
               "Lookups.PurposeOfTheCredit": "PurposeOfTheCredit.Others",
               "Lookups.RoleOfConnectedSubject": "RoleOfConnectedSubject.DebtorMainApplicant",
               "Reports.ContractData.Creditor": "بانک ملی",
               "Reports.LastUpdate": "2019-08-21T00:00:00Z",
               "Lookups.PhaseOfOperation": "PhaseOfOperation.Existing"
               },
               "Reports.ContractData.ConnectedSubjects": [],
               "Reports.ContractData.Collaterals": {
               "Reports.ContractData.Collateral": {
               "_key": "0",
               "Lookups.TypeOfGuarantee": "GuaranteeType.CollateralToBeProvidedInFuture",
               "Relations.Amounts.Guarantee": {
               "Types.Amount": "120000000.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               }
               }
               }
               }
               }
               },
               "Reports.ContractData.TerminatedOperationsDebtor": {
               "Reports.ContractData.Instalments": {
               "Reports.ContractData.Instalment": {
               "_key": "0",
               "Relations.Contracts.InstalmentDetails": {
               "Lookups.TypeOfFinancingInstalments": "TypeOfFinancingInstalments.QarzAlHassaneh",
               "Lookups.TypeOfInstalments": "TypeOfInstalments.Fixed",
               "Lookups.PeriodicityOfPayments": "PeriodicityOfPayments.MonthlyInstalments30Days",
               "Lookups.MethodOfPayment": "MethodOfPayment.DirectRemittance",
               "Relations.Amounts.TotalCredit": {
               "Types.Amount": "15975000.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Types.Contract.NumberOfInstalments": "60",
               "Relations.Amounts.StandardPeriodicalInstalment": {
               "Types.Amount": "266250.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Relations.Amounts.Overdue": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Relations.Amounts.Outstanding": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               }
               },
               "Reports.HistoricalCalendar.Instalment": {
               "Reports.HistoricalCalendar.InstalmentRecord": [
               {
               "_key": "139706",
               "Relations.Amounts.Overdue": {
               "Types.Amount": "0.0000",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR"
               },
               "Reports.HistoricalCalendar.Month": "6",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139707",
               "Reports.HistoricalCalendar.Month": "7",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139708",
               "Reports.HistoricalCalendar.Month": "8",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139709",
               "Reports.HistoricalCalendar.Month": "9",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139710",
               "Reports.HistoricalCalendar.Month": "10",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139711",
               "Reports.HistoricalCalendar.Month": "11",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139712",
               "Reports.HistoricalCalendar.Month": "12",
               "Reports.HistoricalCalendar.Year": "1397"
               },
               {
               "_key": "139801",
               "Reports.HistoricalCalendar.Month": "1",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139802",
               "Reports.HistoricalCalendar.Month": "2",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139803",
               "Reports.HistoricalCalendar.Month": "3",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139804",
               "Reports.HistoricalCalendar.Month": "4",
               "Reports.HistoricalCalendar.Year": "1398"
               },
               {
               "_key": "139805",
               "Reports.HistoricalCalendar.Month": "5",
               "Reports.HistoricalCalendar.Year": "1398"
               }
               ]
               },
               "Reports.ContractData.GeneralInformation": {
               "Lookups.NegativeContractStatus": "NegativeContractStatus.NoNegativeStatus",
               "Relations.Contracts.Dates": {
               "Types.Contract.Dates.Start": "2018-01-09T20:30:00Z",
               "Types.Contract.Dates.ExpectedEnd": "2022-12-14T20:30:00Z",
               "Types.Contract.Dates.RealEnd": "2018-09-04T19:30:00Z"
               },
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR",
               "Lookups.PurposeOfTheCredit": "PurposeOfTheCredit.Others",
               "Lookups.RoleOfConnectedSubject": "RoleOfConnectedSubject.DebtorMainApplicant",
               "Reports.ContractData.Creditor": "صندوق علوم",
               "Reports.LastUpdate": "2018-09-04T00:00:00Z",
               "Lookups.PhaseOfOperation": "PhaseOfOperation.TerminatedAccordingTheContract"
               },
               "Reports.ContractData.ConnectedSubjects": []
               }
               }
               }
               },
               "Reports.SubjectData.IDs": [],
               "Reports.Lookups.ReportStatus": "ReportStatus.OK",
               "Reports.SummaryReport": {
               "Reports.Lookups.ReportStatus": "ReportStatus.OK",
               "NegativeStatusesAndInquiries": {
               "NumberOfInquiries": {
               "NumberOfInquiriesRecord": [
               {
               "_key": "Bank",
               "Lookups.SubscriberType": "SubscriberType.Bank",
               "Last1Month": "0",
               "Last1Year": "0"
               },
               {
               "_key": "CreditUnion",
               "Lookups.SubscriberType": "SubscriberType.CreditUnion",
               "Last1Month": "0",
               "Last1Year": "0"
               },
               {
               "_key": "InsuranceCompany",
               "Lookups.SubscriberType": "SubscriberType.InsuranceCompany",
               "Last1Month": "0",
               "Last1Year": "0"
               },
               {
               "_key": "Leasing",
               "Lookups.SubscriberType": "SubscriberType.Leasing",
               "Last1Month": "0",
               "Last1Year": "0"
               },
               {
               "_key": "Other",
               "Lookups.SubscriberType": "SubscriberType.Other",
               "Last1Month": "16",
               "Last1Year": "16"
               }
               ]
               }
               },
               "PersonalInformation": {
               "PersonalCode": "0011001100",
               "FirstName": "فاطمه",
               "Surname": "تستی",
               "FathersName": "اصغر",
               "DateOfBirth": "1987-09-02T19:30:00Z",
               "PlaceOfBirth": "54002",
               "Lookups.Gender": "Gender.Female",
               "Lookups.MaritalStatus": "MaritalStatus.Single"
               },
               "AddressAndContactInformation": {
               "HomeAddress": "اطلاعات هدف مندي",
               "MobilePhones": {
               "MobilePhone": {
               "_key": "0",
               "ContactValue": "09190000754"
               }
               },
               "HomePhones": {
               "HomePhone": {
               "_key": "0",
               "ContactValue": "-"
               }
               }
               },
               "ContractsSummary": {
               "Contracts": {
               "ContractRecord": [
               {
               "_key": "0",
               "Lookups.TypeOfContract": "TypeOfContract.Instalment",
               "Products.Types.Subscriber": "Melli",
               "Products.Types.SubscriberLocalName": "بانک ملی",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR",
               "NumberOfOpenContracts": "1",
               "NumberOfTerminatedContracts": "0",
               "OutstandingAmount": "39583333.0000",
               "OverdueAmount": "0.0000"
               },
               {
               "_key": "1",
               "Lookups.TypeOfContract": "TypeOfContract.Instalment",
               "Products.Types.Subscriber": "Sandogh Refah",
               "Products.Types.SubscriberLocalName": "صندوق علوم",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR",
               "NumberOfOpenContracts": "0",
               "NumberOfTerminatedContracts": "1",
               "OutstandingAmount": "0",
               "OverdueAmount": "0"
               }
               ],
               "TotalRecord": {
               "_key": "2",
               "Lookups.CurrencyCodes": "CurrencyCodes.IRR",
               "NumberOfOpenContracts": "1",
               "NumberOfTerminatedContracts": "1",
               "OutstandingAmount": "39583333.0000",
               "OverdueAmount": "0.0000"
               }
               }
               },
               "SubjectRoles": {
               "SubjectRoleRecord": [
               {
               "_key": "0",
               "Lookups.RoleOfConnectedSubject": "RoleOfConnectedSubject.DebtorMainApplicant",
               "NumberOfContracts": "1"
               },
               {
               "_key": "1",
               "Lookups.RoleOfConnectedSubject": "RoleOfConnectedSubject.Guarantor",
               "NumberOfContracts": "0"
               }
               ]
               },
               "ReportDate": "2019-09-22T10:23:07.7213052Z"
               }
               }
               }
               }
               },
               "Errors": ""
               }
               }
               },
               "status": "DONE"
               }
        result: آبجکتی از پاسخ سرویس شامل:
        nationalCode: شماره مشتری کاربر
        name: نام کاربر
        score: آرایه‌ای از رتبه‌بندی کاربر
        status: وضعیت فراخوانی سرویس
        DONE: فراخوانی موفق سرویس
        FAILED: فراخوانی ناموفق سرویس
        trackId: کد پیگیری، اگر ارسال شده باشد همان مقدار و در غیر اینصورت یک رشته تصادفی تولید و برگردانده میشود
        error: جزییات خطا (در صورت بروز خطا)

        """

        if national_id is None or not re.match('^[0-9]{10}$', national_id):
            raise ValueError(f'Bad national id: {national_id}')

        if phone_number is None or not re.match('^[0-9]{11}$', phone_number):
            raise ValueError(f'Bad phone number: {phone_number}')

        if otp is None or not re.match('^[0-9]{4}$', otp):
            raise ValueError(f'Bad otp: {otp}')

        url = f'/oak/v2/clients/{self.client_id}/users/{national_id}/standardReliability'

        return self._execute(
            uri=url,
            params={'phoneNumber': phone_number, 'otp': otp},
            token=self.client_credential,
        ).get('result')

    def national_id_verification(self, access_token: FacilitySmsAccessTokenToken,
                                 national_id,
                                 birth_date: str,
                                 first_name=None, last_name=None, full_name=None,
                                 father_name=None, gender=None) -> NationalIdVerification:

        if national_id is None or not re.match('^[0-9]{10}$', national_id):
            raise ValueError(f'Bad national id: {national_id}')

        if birth_date is None or not re.match('^[0-9]{4}/[0-1][0-9]/[0-9]{2}$', birth_date):
            raise ValueError(f'Bad birth_date: {birth_date}')

        if gender is None or not re.match('^(مرد|زن)$', gender):
            raise ValueError(f'Bad gender: {gender}')

        if full_name is None and first_name is None and last_name is None:
            raise ValueError(f'Please set at least one of: full_name, first_name, last_name')

        if full_name is None:
            full_name = f'{first_name} {last_name}'

        url = f'/facility/v2/clients/{self.client_id}/users/{national_id}/sms/nidVerification'

        params = dict(birthDate=birth_date)

        if full_name is not None:
            params['fullName'] = full_name

        if first_name is not None:
            params['firstName'] = first_name

        if last_name is not None:
            params['lastName'] = last_name

        if father_name is not None:
            params['fatherName'] = father_name

        if gender is not None:
            params['gender'] = gender

        return NationalIdVerification(self._execute(
            uri=url,
            params=params,
            token=access_token,
        ).get('result'))

    def card_to_iban(self, card):
        """
        شرح: سرویس اطلاعات شبا

        اسکوپ: facility:card-to-iban:get

        رویکرد: Client-Credential

        {address}/facility/v2/clients/{clientId}/cardToIban?trackId={trackId}&card={card}
        https://apibeta.finnotech.ir :address
        Notes
        اسامی بانک‌هایی که این سرویس برای آن‌ها قابل انجام است:

        بانک آینده

        بانک اقتصاد نوین
        بانک کشاورزی
        بانک سامان
        بانک سرمایه
        بانک پاسارگاد
        بانک صادرات
        بانک ملی
        بانک رسالت
        بانک دی
        بانک انصار
        بانک ملت
        بانک شهر
        بانک مسکن
        بانک ایران زمین
        بانک پارسیان
        Headers
        مقادیر زیر باید در هدر قرار بگیرد

        Authorization : Bearer {Token}
        برای فراخوانی این سرویس باید از توکن CLIENT_CREDENTIAL استفاده نمایید.
        URI Parameters
        clientId : (اجباری) شناسه کلاینت
        Query Parameters
        trackId: اختیاری (string) ‫ کد پیگیری، رشته ای اختیاری با طول حداکثر ۴۰ کاراکتر شامل حرف و عدد. در صورت ارسال trackId، فراخوانی سرویس خود را با همین مقدار استعلام و پیگیری کنید.(در گزارش فراخوانی سرویس ها با همین رشته نتیجه را ببینید). در صورتیکه که این فیلد را ارسال نکنید یک رشته UUID برای این فراخوانی در نظر گرفته میشود و در پاسخ فراخوانی برگردانده میشود.
        example: cardToIban-029
        card: شماره کارت
        example: 6362141081734437
        Results Format
        Successful result format (status code 200)
          {
             "trackId": "cardToIban-029",
             "result": {
              "IBAN": "IR910800005000115426432001"
            , "bankName": "قرض الحسنه رسالت"
            , "deposit": "10.6423499.1"
            , "card" : "6362141081734437"
            , "depositStatus": "02"
            , "depositDescription": "حساب فعال است"
            , "depositComment": "سپرده حقيقي قرض الحسنه پس انداز حقيقي ريالی شیما کیایی"
            , "depositOwners": [
                  {
                    "firstName": "شیما"
                  , "lastName": "کیایی"
                  }
              ],
              "alertCode": "01"
          },
          , "status": "DONE"
          }
        result: آبجکتی از پاسخ سرویس شامل:
        IBAN: شماره شبا
        bankName: نام بانک
        deposit: شماره حساب
        card: شماره کارت
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

        # TODO: Add luhn check to reduce api call rate

        if card is None or not re.match('^[0-9]{16}$', card):
            raise ValueError(f'Bad card: {card}')

        url = f'/facility/v2/clients/{self.client_id}/cardToIban'
        return CardToIbanResponse(self._execute(
            uri=url,
            token=self.client_credential,
            params={'card': card}
        ).get('result'))
