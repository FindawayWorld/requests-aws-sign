try:
    from urllib.parse import urlparse, urlencode, parse_qs, quote
except ImportError:
    from urlparse import urlparse, parse_qs
    from urllib import urlencode, quote

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

class AWSV4Sign(requests.auth.AuthBase):
    """
    AWS V4 Request Signer for Requests.
    """

    def __init__(self, credentials, region, service):
        if not region:
            raise ValueError("You must supply an AWS region")
        self.credentials = credentials
        self.region = region
        self.service = service

    def encode_params(self, query_params):
        try:
            # this function replicates the below functionality some of the args we weren't using
            # for reference: https://github.com/python/cpython/blob/master/Lib/urllib/parse.py#L837
            return urlencode(parse_qs(url.query, keep_blank_values=True, quote_via=quote), doseq=True)
        except TypeError as e:
            parsed_qs = parse_qs(query_params, keep_blank_values=True)
            escaped_params = {}
            for k, v in parsed_qs.items():
                escaped_params[quote(k)] = map(lambda x: quote(x), v)

            result = []
            for k, v in escaped_params.items():
                for one_value in v:
                    result.append(k + '=' + one_value)

            return '&'.join(result).encode('utf-8')

    def __call__(self, r):
        url = urlparse(r.url)
        path = url.path or '/'
        querystring = ''
        if url.query:
            querystring = '?' + self.encode_params(parsed_params)
        safe_url = url.scheme + '://' + url.netloc.split(':')[0] + path + querystring
        request = AWSRequest(method=r.method.upper(), url=safe_url, data=r.body)
        SigV4Auth(self.credentials, self.service, self.region).add_auth(request)
        r.headers.update(dict(request.headers.items()))
        return r
