import os
import json
from typing import List, Optional, Dict, TypedDict, Type
from app import repositories

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# Load the configuration file
config_file_path = os.path.join(current_file_directory, "config.json")
with open(config_file_path, "r", encoding="utf-8") as config_file:
    config = json.load(config_file)


class DatabaseConfig(TypedDict):
    options: List[str]
    default: str
    current: Optional[str]


# We will need a bunch of potential environment variables to check on what services to use for which type of data.
Databases: Dict[str, DatabaseConfig] = {
    "UserDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
    "ConversationDB": {
        "options": ["postgresql"],
        "default": "postgresql",
        "current": None,
    },
    "DocumentDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
    "DocumentSetDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
    "UsageDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
    "MessageDB": {"options": ["postgresql"], "default": "postgresql", "current": None},
}

# Load all options
for db in Databases:
    if db in config and [db] in Databases[db]["options"]:
        Databases[db]["current"] = config[db]
    else:
        Databases[db]["current"] = Databases[db]["default"]

user_db = Databases["UserDB"]["current"]
conversation_db = Databases["ConversationDB"]["current"]
document_db = Databases["DocumentDB"]["current"]
document_set_db = Databases["DocumentSetDB"]["current"]
message_db = Databases["MessageDB"]["current"]
usage_db = Databases["UsageDB"]["current"]

UserRepositoryImpl: Type[repositories.UserRepository] = repositories.UserRepository
ConversationRepositoryImpl: Type[repositories.ConversationRepository] = (repositories.ConversationRepository)
DocumentRepositoryImpl: Type[repositories.DocumentRepository] = (repositories.DocumentRepository)
DocumentSetRepositoryImpl:Type[repositories.DocumentSetRepository] = (repositories.DocumentSetRepository)
MessageRepositoryImpl: Type[repositories.MessageRepository] = (repositories.MessageRepository)
UsageRepositoryImpl: Type[repositories.UsageRepository] = repositories.UsageRepository

# Load the correct database
if user_db == "postgresql":
    from app.dbs.postgresql import UserRepository

    UserRepositoryImpl = UserRepository

# This is just an example, on how this could be done for other databases
# elif user_db == "mongodb":
#    from app.dbs.mongodb import UserRepository
#    UserRepositoryImpl = UserRepository
else:
    raise Exception("No valid user database found")

if conversation_db == "postgresql":
    from app.dbs.postgresql import ConversationRepository

    ConversationRepositoryImpl = ConversationRepository

if document_db == "postgresql":
    from app.dbs.postgresql import DocumentRepository

    DocumentRepositoryImpl = DocumentRepository

if document_set_db == "postgresql":
    from app.dbs.postgresql import DocumentSetRepository

    DocumentSetRepositoryImpl = DocumentSetRepository

if message_db == "postgresql":
    from app.dbs.postgresql import MessageRepository

    MessageRepositoryImpl = MessageRepository

if usage_db == "postgresql":
    from app.dbs.postgresql import UsageRepository

    UsageRepositoryImpl = UsageRepository
