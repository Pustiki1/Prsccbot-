from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///promocodes.db', echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class Promocode(Base):
    __tablename__ = 'promocodes'

    id = Column(Integer, primary_key=True)
    promocode = Column(String(100), nullable=False)
    worked = Column(Boolean, default=True)  # Boolean лучше чем String(100)

    @staticmethod
    def add_new_promocode(promo):
        session = SessionLocal()
        try:
            last_active = session.query(Promocode).filter_by(worked=True).order_by(Promocode.id.desc()).first()

            if last_active:
                last_active.worked = False
                session.add(last_active)

            new_promo = Promocode(promocode=promo, worked=True)
            session.add(new_promo)
            session.commit()

            return "success"
        except Exception as e:
            session.rollback()
            return str(e)
        finally:
            session.close()

    @staticmethod
    def check_promo(promo):
        session = SessionLocal()
        check_correct_promo = session.query(Promocode).filter_by(promocode=promo,
                                                                 worked=True,
                                                                 ).order_by(Promocode.id.desc()).first()
        try:
            if check_correct_promo:
                return "success"
            else:
                return "error"

        except Exception as e:
            return str(e)


def init_db():
    Base.metadata.create_all(engine)