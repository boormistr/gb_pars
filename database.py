from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models


class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def get_or_create(self, session, model, **data):
        db_data = session.query(model).filter(model.url == data["url"]).first()
        if not db_data:
            db_data = model(**data)
        return db_data

    def get_or_create_comments(self, session, model, **data):
        db_data = session.query(model).filter(model.id == data["id"]).first()
        if not db_data:
            db_data = model(**data)
        return db_data

    def create_post(self, data):
        session = self.maker()
        tags = map(
            lambda tag_data: self.get_or_create(session, models.Tag, **tag_data), data["tags"]
        )
        # comments = map(
        #     lambda comments_data: self.get_or_create(session, models.Comment, **comments_data), data["comments"]
        # )
        comments = map(
            lambda comments_data: self.get_or_create_comments(session, models.Comment, **comments_data), data["comments"]
        )
        author = self.get_or_create(session, models.Author, **data["author"])
        post = self.get_or_create(session, models.Post, **data["post_data"], author=author)
        post.tags.extend(tags)
        post.comments.extend(comments)

        session.add(post)

        try:
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
