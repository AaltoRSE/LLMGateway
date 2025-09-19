from fastapi import Depends
from typing import Annotated, List

# DB Specific imports
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from ..models.llmmodel_model import LLMModel as DBLLMModel
from ..db import db as db_dependency

# App imports
from app.repositories.model_repository import LLMModelRepository, LLMModelData
from app.schemas.llmmodel_schema import LLMModelDataDetails


class SQLModelRepository(LLMModelRepository):
    def __init__(self, db: Annotated[Session, Depends(db_dependency.get_db)]):
        self.db = db

    def _convert_db_to_schema(self, db_model: DBLLMModel) -> LLMModelData:
        details = LLMModelDataDetails(
            id=db_model.llm_model_id,
            owned_by=db_model.owned_by,
            object=db_model.object,
            type=db_model.type,
        )
        return LLMModelData(
            path=db_model.path,
            host=db_model.host,
            model=details,
            name=db_model.name,
            description=db_model.description,
            prompt_cost=db_model.prompt_cost,
            completion_cost=db_model.completion_cost,
            cached_token_cost=db_model.cached_token_cost,
        )

    def _convert_schema_to_db(self, model: LLMModelData) -> DBLLMModel:
        return DBLLMModel(
            path=model.path,
            host=model.host,
            name=model.name,
            description=model.description,
            prompt_cost=model.prompt_cost,
            completion_cost=model.completion_cost,
            cached_token_cost=model.cached_token_cost,
            llm_model_id=model.model.id,
            owned_by=model.model.owned_by,
            object=model.model.object,
            type=model.model.type,
        )

    async def get_models(self) -> List[LLMModelData]:
        """
        Get a list of the data of all models
        """
        models = self.db.query(DBLLMModel).all()
        return [self._convert_db_to_schema(model) for model in models]

    def _get_db_model_by_id(self, id: str) -> DBLLMModel | None:
        return self.db.query(DBLLMModel).filter(DBLLMModel.id == id).first()

    async def get_model(self, id: str) -> LLMModelData:
        """
        Get the mode with the given ID
        """
        model = self._get_db_model_by_id(id)
        return self._convert_db_to_schema(model) if model is not None else None

    async def add_model(self, model: LLMModelData) -> LLMModelData | None:
        """
        Add a new model
        """
        print("Adding new model")
        dbmodel = self._convert_schema_to_db(model)
        try:
            self.db.add(dbmodel)
            self.db.commit()
            self.db.refresh(dbmodel)
        except IntegrityError:
            self.db.rollback()
            return None
        return self._convert_db_to_schema(dbmodel)

    async def update_model(self, model: LLMModelData) -> LLMModelData | None:
        """
        Update a model, returns the updated model
        """
        db_model: DBLLMModel | None = await self._get_db_model_by_id(model.model.id)
        if db_model is None:
            return None
        db_model.path = model.path
        db_model.host = model.host
        db_model.name = model.name
        db_model.description = model.description
        db_model.prompt_cost = model.prompt_cost
        db_model.completion_cost = model.completion_cost
        db_model.cached_token_cost = model.cached_token_cost
        db_model.id = model.model.id
        db_model.object = model.model.object
        db_model.owned_by = model.model.owned_by
        db_model.object = model.model.object
        db_model.type = model.model.type
        self.db.commit()
        self.db.refresh(db_model)
        return self._convert_db_to_schema(db_model)

    async def remove_model(self, id: str) -> bool:
        model = self._get_db_model_by_id(id)
        if model is None:
            return False
        self.db.delete(model)
        self.db.commit()
        return True
