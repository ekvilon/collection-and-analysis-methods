from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .schema import Schema, Post, Author, Tag, Comment


class Database:
    def __init__(self, database_url):
        engine = create_engine(database_url)
        Schema.metadata.create_all(engine)
        self._getSession = sessionmaker(engine)

    def _insert_or_update(self, session, model, filter_criteria, **data):
        record = session.query(model).filter(filter_criteria).first()

        try:
            if record is None:
                record = model(**data)
                session.add(record)
            session.commit()
        except Exception as ex:
            print(ex)
            session.rollback()
        return record

    def _insert_or_update_comments(self, session, comments: list) -> list:
        result = []
        if comments:
            for comment in comments:
                author_record = self._insert_or_update(
                    session, Author, Author.url == comment["author"]["url"], **comment["author"]
                )
                record = self._insert_or_update(
                    session,
                    Comment,
                    Comment.id == comment["id"],
                    **comment["comment"],
                    author=author_record,
                )

                result.append(record)
                result.extend(self._insert_or_update_comments(session, comment["children"]))

        return result

    def create_post(self, data):
        with self._getSession() as session:
            comments = self._insert_or_update_comments(session, data["comments"])
            author = self._insert_or_update(
                session,
                Author,
                Author.url == data["author"]["url"],
                **data["author"],
            )
            tags = list(
                map(
                    lambda tag_data: self._insert_or_update(
                        session, Tag, Tag.url == tag_data["url"], **tag_data
                    ),
                    data["tags"],
                )
            )
            post = self._insert_or_update(
                session,
                Post,
                Post.id == data["post"]["id"],
                **data["post"],
                author=author,
            )
            post.tags.extend(tags)
            post.comments.extend(comments)
            session.add(post)

            try:
                session.commit()
            except Exception as ex:
                print(ex)
                session.rollback()
            finally:
                session.close()
