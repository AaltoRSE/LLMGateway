# This file provides the app with simpler access points for everything necessary for the use of a postgresql database

from .repositories import (
    user_repository,
    conversation_repository,
    message_repository,
    usage_repository,
    document_repository,
    document_set_repository,
)

UserRepository = user_repository.SQLUserRepository
ConversationRepository = conversation_repository.SQLConversationRepository
MessageRepository = message_repository.SQLMessageRepository
UsageRepository = usage_repository.SQLUsageRepository
DocumentRepository = document_repository.SQLDocumentRepository
DocumentSetRepository = document_set_repository.SQLDocumentSetRepository
