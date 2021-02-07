from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Date

Base = declarative_base()

tag_post = Table(
    "tag_post",
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

comment_post = Table(
    "comment_post",
    Base.metadata,
    Column('comment_id', Integer, ForeignKey('comment.id')),
    Column('post_id', Integer, ForeignKey('post.id'))
)

class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, unique=False, nullable=False)
    pic_url = Column(String, unique=False, nullable=True)
    date = Column(Date, unique=False, nullable=False)
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship("Author")
    tags = relationship('Tag', secondary=tag_post)
    comments = relationship('Comment', secondary=comment_post)

class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, unique=False)
    posts = relationship("Post")


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, unique=True, primary_key=True)
    author_id = Column(Integer, unique=False, nullable=False)
    text = Column(String, unique=False, nullable=False)
    posts = relationship("Post", secondary=comment_post)


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, autoincrement=True, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    posts = relationship("Post", secondary=tag_post)
