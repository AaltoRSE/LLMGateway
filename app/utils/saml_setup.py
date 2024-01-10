from onelogin.saml2.settings import OneLogin_Saml2_Settings
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
print(BASE_DIR)
SAML_DIR = os.path.join(BASE_DIR, "saml")

saml_settings = OneLogin_Saml2_Settings(
    settings=None, custom_base_path=SAML_DIR, sp_validation_only=True
)
