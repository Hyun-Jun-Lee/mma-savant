#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UFC 체급 정보를 초기화하는 Python 스크립트
alembic 마이그레이션 후 실행하세요
"""

from datetime import datetime
from sqlalchemy import text
from database.session import db_session, engine
from models import WeightClassModel


def check_if_weight_classes_exist():
    """체급 정보가 이미 존재하는지 확인"""
    with db_session() as session:
        count = session.query(WeightClassModel).count()
        return count > 0


def initialize_weight_classes():
    """체급 정보 초기화"""
    if check_if_weight_classes_exist():
        print("체급 테이블이 이미 초기화되어 있습니다.")
        return
    
    # 체급 정보 생성
    weight_classes = [
        WeightClassModel(name="Flyweight"),
        WeightClassModel(name="Bantamweight"),
        WeightClassModel(name="Featherweight"),
        WeightClassModel(name="Lightweight"),
        WeightClassModel(name="Welterweight"),
        WeightClassModel(name="Middleweight"),
        WeightClassModel(name="Light Heavyweight"),
        WeightClassModel(name="Heavyweight"),
        WeightClassModel(name="Women's Strawweight"),
        WeightClassModel(name="Women's Flyweight"),
        WeightClassModel(name="Women's Bantamweight"),
        WeightClassModel(name="Women's Featherweight"),
        WeightClassModel(name="Catch Weight"),
    ]
    
    # 데이터베이스에 체급 정보 저장
    with db_session() as session:
        for weight_class in weight_classes:
            # 날짜 필드 설정
            weight_class.created_at = datetime.now()
            weight_class.updated_at = datetime.now()
            session.add(weight_class)
    
    # ID 시퀀스 설정 (PostgreSQL 전용)
    with engine.connect() as connection:
        connection.execute(text("SELECT setval('weight_class_id_seq', 13, true)"))
    
    print("체급 테이블 초기화 완료: 13개 항목 생성됨")


if __name__ == "__main__":
    initialize_weight_classes()
