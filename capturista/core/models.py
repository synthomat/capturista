import uuid

import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, select, delete
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship, session


class BaseModel(DeclarativeBase):
    __abstract__ = True

    id = mapped_column(sa.Uuid(), primary_key=True, default=uuid.uuid4)
    created_at = mapped_column(sa.DateTime, default=sa.func.current_timestamp(), nullable=False)
    updated_at = mapped_column(sa.DateTime,
                               default=sa.func.current_timestamp(),
                               onupdate=sa.func.current_timestamp())


db = SQLAlchemy(model_class=BaseModel)


class Endpoint(BaseModel):
    __tablename__ = "endpoints"

    name = mapped_column(sa.String(255), nullable=False)

    data_source_id: Mapped[uuid] = mapped_column(ForeignKey("data_sources.id"), nullable=True)
    data_source: Mapped["DataSource"] = relationship()


class DataSource(BaseModel):
    __tablename__ = "data_sources"

    name = mapped_column(sa.String(255), nullable=False)

    loader_id = mapped_column(sa.Uuid(), nullable=False)
    is_active = mapped_column(sa.Boolean(), default=False, nullable=False)
    target_url = mapped_column(sa.Text())
    custom_config = mapped_column(sa.JSON())


class DataSourceRepository:
    def __init__(self, sess: session.Session):
        self.session = sess

    def get_all(self) -> [DataSource]:
        return self.session.scalars(select(DataSource)).all()

    def get_by_id(self, _id: str) -> DataSource | None:
        return self.session.scalar(select(DataSource).where(DataSource.id == uuid.UUID(_id)))

    def delete_by_id(self, _id: str):
        res = self.session.execute(delete(DataSource).where(DataSource.id == uuid.UUID(_id)))
        self.session.commit()

        return res.rowcount > 0
