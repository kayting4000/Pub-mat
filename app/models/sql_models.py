import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database_pg import Base


class RoleEnum(str, enum.Enum):
    editor_in_chief = "editor_in_chief"
    associate_editor = "associate_editor"
    writer = "writer"
    photojournalist = "photojournalist"
    layout_artist = "layout_artist"
    cartoonist = "cartoonist"


CONSOLE_ROLES = ("editor_in_chief", "associate_editor")
STAFF_ROLES = ("writer", "photojournalist", "layout_artist", "cartoonist")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(Enum(RoleEnum), default=RoleEnum.writer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    articles: Mapped[list["PublishedArticle"]] = relationship("PublishedArticle", back_populates="author")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    articles: Mapped[list["PublishedArticle"]] = relationship("PublishedArticle", back_populates="category")


class PublishedArticle(Base):
    __tablename__ = "published_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    draft_id: Mapped[str] = mapped_column(String(24), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    author: Mapped["User"] = relationship("User", back_populates="articles")
    category: Mapped["Category | None"] = relationship("Category", back_populates="articles")
    pubmat_assets: Mapped[list["PubMatAsset"]] = relationship("PubMatAsset", back_populates="article")


class PubMatAsset(Base):
    __tablename__ = "pubmat_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("published_articles.id"), nullable=False)
    asset_url: Mapped[str] = mapped_column(String(500), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    article: Mapped["PublishedArticle"] = relationship("PublishedArticle", back_populates="pubmat_assets")
