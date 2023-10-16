import uuid

import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship


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


class DataSource(db.Model):
    __tablename__ = "data_sources"

    name = mapped_column(sa.String(255), nullable=False)

    loader_type = mapped_column(sa.String(50))
    is_active = mapped_column(sa.Boolean(), default=False, nullable=False)
    target_url = mapped_column(sa.Text())
    slots = mapped_column(sa.JSON())
