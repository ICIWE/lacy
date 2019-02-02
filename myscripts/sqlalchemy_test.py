# -*- coding: utf-8 -*-
# @author: NiHao

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker


engine = create_engine('mysql+pymysql://root:0000@localhost:3306/oo', echo=True)
base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class User(base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))

    def __repr__(self):
        return '<User name=%s>' % self.name


base.metadata.create_all(engine)

dawang = User(name='dawang')
session.add(dawang)
session.commit()
