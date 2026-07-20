from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import (
    Column,
    ColumnClause,
    Executable,
    Result,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar('ModelType', bound=Base)
OperatorType = Callable[[Column, Any], ColumnClause]

action_map = {
    'gt': '__gt__',
    'lt': '__lt__',
    'ge': '__ge__',
    'le': '__le__',
    'in': 'in_',
    'contains': 'contains',
    'eq': '__eq__',
    'ne': '__ne__',
}


class AbstractRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_one(self, **filters: Any) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, offset: int, limit: int, **filters: Any) -> Sequence[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, obj_in: BaseModel | dict[str, Any]) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        obj_in: BaseModel | dict[str, Any],
        *,
        return_object: bool = False,
        **filters: Any,
    ) -> int | ModelType:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, return_object: bool = False, **filters: Any) -> int | ModelType:
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository, Generic[ModelType]):
    model: type[ModelType]
    duplicate_error_class = Exception
    object_not_found_error_class = Exception
    restrict_error_class = Exception

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.model_name = self.model.__name__

    async def execute(self, statement: Executable, action: Callable[[Any], Any] | None = None) -> Any:
        try:
            result: Result = await self.session.execute(statement)
            return action(result) if action else result

        except IntegrityError as e:
            raise e

    async def get_one(self, **filters: Any) -> ModelType:
        statement = select(self.model).where(*self.get_where_clauses(filters))
        return await self.execute(statement=statement, action=lambda result: result.scalars().one())

    async def get_one_or_none(self, **filters: Any) -> ModelType | None:
        statement = select(self.model).where(*self.get_where_clauses(filters))
        return await self.execute(statement=statement, action=lambda result: result.scalars().one_or_none())

    async def get_multi(self, offset: int = 0, limit: int = 50, /, **filters: Any) -> Sequence[ModelType]:
        statement = select(self.model).where(*self.get_where_clauses(filters)).offset(offset).limit(limit)
        return await self.execute(statement=statement, action=lambda result: result.scalars().all())

    def get_where_clauses(self, filters: dict[str, Any]) -> list[ColumnClause]:
        clauses: list[ColumnClause] = []
        for key, value in filters.items():
            if '__' not in key:
                key = f'{key}__eq'

            column_name, action_name = key.split('__')

            column: Column | None = getattr(self.model, column_name, None)
            if column is None:
                raise ValueError(f'Invalid column {column_name} for {self.model_name}')

            action: str | None = action_map.get(action_name)
            if action is None:
                raise ValueError(
                    f'Unsupported action: {action_name}, ',
                    f'supported actions: {", ".join(action_map.keys())}',
                )

            clause: ColumnClause = getattr(column, action)(value)
            clauses.append(clause)

        return clauses

    async def create(self, obj_in: BaseModel | dict[str, Any]) -> ModelType:
        data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
        statement = insert(self.model).values(**data).returning(self.model)
        return await self.execute(statement=statement, action=lambda result: result.scalar_one())

    async def update(
        self,
        obj_in: BaseModel | dict[str, Any],
        *,
        return_object: bool = False,
        **filters: Any,
    ) -> int | ModelType:
        obj_in = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
        statement = update(self.model).where(*self.get_where_clauses(filters)).values(**obj_in)

        if return_object:
            statement = statement.returning(self.model)
            return await self.execute(statement=statement, action=lambda result: result.scalars().one())

        return await self.execute(statement=statement, action=lambda result: result.rowcount)

    async def delete(self, return_object: bool = False, **filters: Any) -> int | ModelType:
        statement = delete(self.model).where(*self.get_where_clauses(filters))

        if return_object:
            statement = statement.returning(self.model)
            return await self.execute(statement=statement, action=lambda result: result.scalars().one())

        return await self.execute(statement=statement, action=lambda result: result.rowcount)

    async def get_count(self, **filters: Any) -> int:
        statement = select(func.count(self.model.id)).where(*self.get_where_clauses(filters))

        return await self.execute(statement, action=lambda result: result.scalar())