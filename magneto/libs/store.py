# coding: utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///magneto.db')
Session = sessionmaker(bind=engine)
session = Session()
