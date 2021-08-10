from pathlib import Path
import os
import socket
import sys

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.sql import func as sqlfunc
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative
from datetime import datetime
from typing import Optional, Callable, List

SqlAlchemyBase = sqlalchemy.ext.declarative.declarative_base()

__factory: Optional[Callable[[], Session]] = None


def global_init(db_path: str):
    """

    :param db_path: Full db Path for sqlite testing or mysql URL
    :return:
    """

    global __factory

    if __factory:
        return

    connection_str = 'sqlite+pysqlite:///' + db_path
    engine = sqlalchemy.create_engine(connection_str, echo=False, connect_args={"check_same_thread": False})
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    """
    Creates a sync session

    :return: Session
    """

    global __factory

    if not __factory:
        raise Exception("You must call global_init() before using this method.")

    session: Session = __factory()
    session.expire_on_commit = False

    return session


class Record(SqlAlchemyBase):
    __tablename__ = 'records'
    id: int = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    created_date: datetime = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)
    ISP: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    speedtest_server: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    server_id: int = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    latency: float = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    jitter: float = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    download_speed: int = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    download_speed_mbps: float = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    upload_speed: int = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    upload_speed_mbps: float = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    download_data_MB: float = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    upload_data_MB: float = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    client_ip: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    server_ip: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    result_url: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    server_location: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    server_country: str = sqlalchemy.Column(sqlalchemy.String, nullable=True)


def add_record(data):
    db = create_session()
    record = Record()
    record.ISP = data['isp']
    record.speedtest_server = f"{data['server']['name']} {data['server']['location']}"
    record.server_id = data['server']['id']
    record.latency = data['ping']['latency']
    record.jitter = data['ping']['jitter']
    record.download_speed_mbps = data['download']['bandwidth'] / 125000
    record.upload_speed_mbps = data['upload']['bandwidth'] / 125000
    record.client_ip = data['interface']['externalIp']
    record.result_url = data['result']['url']
    record.server_location = data['server']['location']
    record.server_country = data['server']['country']
    record.download_speed = data['download']['bandwidth']
    record.upload_speed = data['upload']['bandwidth']
    record.download_data_MB = data['download']['bytes'] / 1000000
    record.upload_data_MB = data['upload']['bytes'] / 1000000
    record.server_ip = data['server']['ip']

    db.add(record)
    db.commit()
    db.refresh(record)


def db_get_countries(isp_filter=None):
    db = create_session()
    if not isp_filter:
        data = db.query(Record.server_country).distinct().all()
    else:
        data = db.query(Record.server_country).where(Record.speedtest_server == isp_filter).distinct().all()
    data = [item[0] for item in data]
    data.sort()
    data.reverse()
    data.append(None)
    data.reverse()
    return data


def db_get_cities(isp_filter=None, country_filter=None):
    db = create_session()
    if not isp_filter and not country_filter:
        data = db.query(Record.server_location).distinct().all()
    elif isp_filter and not country_filter:
        data = db.query(Record.server_location).where(Record.speedtest_server == isp_filter).distinct().all()
    elif not isp_filter and country_filter:
        data = db.query(Record.server_location).where(Record.server_country == country_filter).distinct().all()
    else:
        data = db.query(Record.server_location).filter(Record.server_country == country_filter,
                                                       Record.speedtest_server == isp_filter).distinct().all()

    data = [item[0] for item in data]
    data.sort()
    data.insert(0, None)
    return data


def gb_get_isp(country_filter=None, city_filter=None):
    db = create_session()
    if not country_filter and not city_filter:
        data = db.query(Record.speedtest_server).distinct().all()
    elif country_filter and not city_filter:
        data = db.query(Record.speedtest_server).where(Record.server_country == country_filter).distinct().all()
    else:
        data = db.query(Record.server_location).filter(Record.server_country == country_filter,
                                                       Record.server_location == city_filter).distinct().all()
    data = [item[0] for item in data]
    data.sort()
    data.insert(0, None)
    return data


def get_total_tests():
    db = create_session()
    count = db.query(Record.id).count()
    return count


def get_possible_tests_total():
    db = create_session()
    return db.query(Record.speedtest_server + Record.server_location).distinct().count()


def get_country_from_city(city):
    db = create_session()
    country = db.query(Record.server_country).where(Record.server_location == city)
    if country:
        return country.first()[0]
    else:
        return None


def get_speedtest_results(country, city, isp, date_start=None, date_stop=None):
    db = create_session()
    if not date_start and not date_stop:
        data = db.query(Record).filter(Record.server_country == country, Record.speedtest_server == isp,
                                       Record.server_location == city).order_by(sqlalchemy.asc(Record.created_date)).all()
    else:
        data = db.query(Record).filter(Record.server_country == country, Record.speedtest_server == isp,
                                       Record.server_location == city).filter(Record.created_date.between(date_start, date_stop))
    data = [item.__dict__ for item in data]
    pandas_data = []
    for item in data:
        pandas_data.append({
            'latency': item['latency'],
            'download_speed': item['download_speed_mbps'],
            'upload_speed': item['upload_speed_mbps'],
            'date': item['created_date']
        })
    return pandas_data


def get_latest_data(length=20):
    db = create_session()
    data = db.query(Record).order_by(Record.id.desc()).limit(length)
    data = [item.__dict__ for item in data]
    pandas_data = []
    for item in data:
        pandas_data.append({
                'data': [item['latency'], item['download_speed_mbps'], item['upload_speed_mbps'],],
                'speedtest_server': f"{item['speedtest_server']} {item['server_location']} {str(item['created_date'].strftime('%H-%M'))}"
            })
    return pandas_data


def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1000.00:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1000.00
    return "%.2f %s%s" % (num, 'Y', suffix)


def get_total_data_consumption(upload=False, download=False):
    db = create_session()
    if upload:
        total_upload_data = sizeof_fmt(db.query(sqlfunc.sum(Record.upload_data_MB)).scalar() * 1000000)
        return total_upload_data
    else:
        total_download_data = sizeof_fmt(db.query(sqlfunc.sum(Record.download_data_MB)).scalar() * 1000000)
        return total_download_data


if __name__ == '__main__':
    db_path = (Path(__file__).parent / 'speedtest_log.sqlite').absolute()
    global_init(db_path.as_posix())
    data = db_get_countries()
