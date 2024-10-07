import urllib
import pymongo
import os

USER_COLLECTION = "users"
KEY_COLLECTION = "apikeys"
QUOTA_COLLECTION = "usage"
MODEL_COLLECTION = "model"
ID_FIELD = "auth_id"


mongo_user = urllib.parse.quote_plus(os.environ.get("MONGOUSER", "user"))
mongo_password = urllib.parse.quote_plus(os.environ.get("MONGOPASSWORD", "password"))
mongo_URL = os.environ.get("MONGOHOST", "localhost")
# Set up required endpoints.
mongo_client = pymongo.MongoClient(
    "mongodb://%s:%s@%s/" % (mongo_user, mongo_password, mongo_URL)
)
