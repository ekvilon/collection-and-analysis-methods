from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table

Schema = declarative_base()


class IdMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)


class NameMixin:
    name = Column(String, nullable=False)


class UrlMixin:
    url = Column(String, nullable=False, unique=True)


tag_post = Table(
    "tag_post",
    Schema.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)


class Post(Schema, UrlMixin):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    published_at = Column(DateTime, nullable=False)
    title = Column(String, nullable=False)
    image_url = Column(String)
    author_id = Column(Integer, ForeignKey("author.id"))
    author = relationship("Author")
    tags = relationship("Tag", secondary=tag_post)
    comments = relationship("Comment")


class Author(Schema, IdMixin, NameMixin, UrlMixin):
    __tablename__ = "author"

    posts = relationship("Post")


class Tag(Schema, IdMixin, NameMixin, UrlMixin):
    __tablename__ = "tag"

    posts = relationship("Post", secondary=tag_post)


class Comment(Schema):
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    likes_count = Column(Integer)
    body = Column(String)
    created_at = Column(DateTime, nullable=False)
    author_id = Column(Integer, ForeignKey("author.id"))
    author = relationship("Author")
    post_id = Column(Integer, ForeignKey("post.id"))
    parent = relationship("Comment")
    children = relationship("Comment")
