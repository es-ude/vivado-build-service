from docs.config import Config
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

config = Config().get()
Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    client_id = Column(String)
    task_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


engine = create_engine(config['DB URL'], echo=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def db_insert(client_id, task_id):
    new_task = Task(client_id=client_id, task_id=task_id)
    session.add(new_task)
    session.commit()

def db_get_all():
    return session.query(Task).all()