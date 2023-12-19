from onelogin.saml2.settings import OneLogin_Saml2_Settings

BASE = "https://llm-gateway.k8s-test.cs.aalto.fi"
saml_config = {
    "strict": True,
    "debug": True,
    "sp": {
        "entityId": "%s/saml/metadata" % BASE,
        "assertionConsumerService": {
            "url": "%s/saml/acs" % BASE,
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
        },
        "singleLogoutService": {
            "url": "%s/saml/sls" % BASE,
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
    },
    "idp": {
        "entityId": "https://devel.idp.aalto.fi/idp/shibboleth",
        "singleSignOnService": {
            "url": "https://devel.idp.aalto.fi/idp/profile/SAML2/Redirect/SSO",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
        "singleLogoutService": {
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            "url": "https://devel.idp.aalto.fi/idp/profile/SAML2/Redirect/SLO",
        },
        "x509cert": "MIIFGzCCAwOgAwIBAgIUCH/Md10XaJNOMEHEpbnvdjn0ABEwDQYJKoZIhvcNAQEL BQAwHTEbMBkGA1UEAwwSZGV2ZWwuaWRwLmFhbHRvLmZpMB4XDTE4MTEyODA3NTEz MFoXDTI4MTEyNTA3NTEzMFowHTEbMBkGA1UEAwwSZGV2ZWwuaWRwLmFhbHRvLmZp MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAx6UGxma5RNicPZ78CzQs 2lXsxj9YblGHJkT7vPQzEJvrLvkL7h6mvwhib64d+/z9rkamU4FzosKn95Ac60rM 3X/GOYgqaNw1i2lmxYuvPtzKxD1QT4aQxPoj9OzHDOfj8WqI5Y3v+5sr0N91TQGE +kFy670wwP8UgYx2knw4AEBGi8Eo3W/gUvFk8adIbtgTDIko1bc8Ktal6j487tTC NrZC/yZulmeNJQKtFA2HxQLvLOdK6NwmS1saTYvBl5i6bQGut9+sme1ZGm6DmOae 4KhoD++0fft7KFISrJJHWsYcR+kzrbKXlNf9uEqmu4bicN97mnzoz7Xf4VkvikJR FvftrJA/DDfsBrTLMdgI9sI2o7R47W4CjjiJTgs71xSMt2gMLtP7pWwjRMAQKXR8 UpecJiBi7f7mxOMrQkG8aHHk6E0kohnvn9cbPtiCCyPTUHWZvb7YKnEHFHAJfWTh P2w7RjnfxNYtfZZ4sIXCCigaOLIA+2xYL+IUW3nJMhruifoQQxe8ZDIkhKfYujqk m6aboRkRmj7dtfruv8xMzACrorIOmxwDCSfKut6hE7BhGRqyxmS3J4HN4v43HGxO kZ6gnrpZADfZsuCdnu6RzXgxMHr5HrHNm0irZn6j8juZZ83QlAkDdSXeiF/uM7Ci S3d8mmPhEEsRr0dHuL8spoMCAwEAAaNTMFEwHQYDVR0OBBYEFAJI4SEtrKp90RN3 4Cspn2e4KfgnMB8GA1UdIwQYMBaAFAJI4SEtrKp90RN34Cspn2e4KfgnMA8GA1Ud EwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggIBAJQdKMAaEhjUAqmakVYqzX/w RXaQhhchsPwFwPW/+gv3VzYC1giS63RGipHZKmlJQmXN/FNaRxbpAXbRs6/HoM+h NTqvqONxd62+pZidE9hRfPaYhqoN/G7xv9VGzYZd52s6leSewKr8nhE4feQqtM2h sboCvzp5qjbrRrtZw/4l1c5VpK7XhkCPcLLTrX2xcrVExe2D3ZJAiuhv9ppg8Mza Fe+l3chYo9oO1+5bYODYWQEV8HlE4ihpP76SyD/egy7uqBcA8448fioWflxIAfG4 xqWnPdUMbTnkMptvrKtT+8cr/+9GoSUZMwP+A1rZaxfz0umtEybDfOlSAv4aWZ9+ lJ+U1/eBEa/a4RgutF+Lb8YPn38suNvX54h1tM/vy95VW1sb+4i6P6so8pdpGty6 uTlhYFChcj9gzrl5p8cVqIhkbuTxpSetKPKI3G1sP7h503yrR/t2KubhDtdbHrhM /bkVJutFeQylksvfbKkNJNyjGeSBiw37PXbWeKH71ZtXPG6uM2teuMhHFhoy6/SK c5Ko3acY1076SK6oGEmhi7Ht53Ae7KUo5dTxPfTXz1nyWpWzsifkS/hd7gdzVGXQ anvYDUMe6iKr6Pbk/soyepefLqHrTqSxWgMtDf4ZhBEHwuRxSkjgSSo1XcTuKULA 2zkmEe3gyHpefW3suPwQ",
    },
}

saml_settings = OneLogin_Saml2_Settings(settings=saml_config, sp_validation_only=True)
