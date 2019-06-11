from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, backref, Session
from . import Base
from .transaction_tag import TransactionTag

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer, ForeignKey("tags.id"))

    children = relationship('Tag', backref=backref('parent', remote_side=[id]))
    #transactions = relationship('Transaction', secondary='TransactionTag')

    def __repr__(self):
        return "Tag(%s, id=%u, supertag=(%s), subtags=(%s))" % (
            self.name,
            self.id,
            self.parent.name if self.parent else "None",
            ','.join([c.name for c in self.children]) if self.children else "None",)

    def usage(self):
        # (total assignments, total none assignments)
        return (
                Session.object_session(self)
                .query(TransactionTag).filter(TransactionTag.tag_id == self.id).count(),
                Session.object_session(self)
                .query(TransactionTag).filter(TransactionTag.tag_id != self.id).count()
                )
