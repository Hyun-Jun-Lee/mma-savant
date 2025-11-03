import asyncio
import logging
import traceback

from typing import List, Callable, Dict
from bs4 import BeautifulSoup

from fighter.models import RankingSchema
from common.models import WeightClassSchema
from fighter.repositories import get_fighter_by_name_best_record

# 한글-영문 체급 매핑 (DB weight_class.name과 일치)
DIVISION_MAPPING = {
    "Men's Pound-for-Pound": "men's pound-for-pound",
    "Men's Pound-for-PoundTop Rank": "men's pound-for-pound",  # span 공백 제거 대응
    "Women's Pound-for-Pound": "women's pound-for-pound",
    "Women's Pound-for-PoundTop Rank": "women's pound-for-pound",  # span 공백 제거 대응
    "플라이급": "flyweight",
    "밴텀급": "bantamweight",
    "페더급": "featherweight",
    "라이트급": "lightweight",
    "웰터급": "welterweight",
    "미들급": "middleweight",
    "라이트 헤비급": "light heavyweight",
    "헤비급": "heavyweight",
    "여성 스트로급": "women's strawweight",
    "여성 플라이급": "women's flyweight",
    "여성 밴텀급": "women's bantamweight",
}

def parse_ufc_rankings_from_html(html_content: str) -> Dict[str, Dict[int, str]]:
    """
    UFC 랭킹 HTML에서 체급별 랭킹을 추출하는 함수

    Args:
        html_content: HTML 텍스트

    Returns:
        {체급명: {순위: 선수명}} 형태의 딕셔너리
        챔피언은 0순위로 처리
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    rankings = {}

    # 모든 view-grouping 찾기
    groupings = soup.find_all('div', class_='view-grouping')

    for grouping in groupings:
        # 체급명 추출
        header = grouping.find('div', class_='view-grouping-header')
        if not header:
            continue

        division_raw = header.get_text(strip=True)

        # 한글 체급명을 영문으로 변환
        division = DIVISION_MAPPING.get(division_raw)
        if not division:
            logging.warning(f"알 수 없는 체급: {division_raw}")
            continue

        rankings[division] = {}

        # 챔피언 추출 (순위 0)
        champion_div = grouping.find('div', class_='rankings--athlete--champion')
        if champion_div:
            champion_h5 = champion_div.find('h5')
            if champion_h5:
                champion_link = champion_h5.find('a')
                if champion_link:
                    champion_name = champion_link.get_text(strip=True)
                    rankings[division][0] = champion_name
                    logging.debug(f"{division} 챔피언: {champion_name}")

        # 랭커 추출 (순위 1-15)
        table = grouping.find('table')
        if not table:
            continue

        tbody = table.find('tbody')
        if not tbody:
            continue

        rows = tbody.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 2:
                continue

            # 순위
            rank_col = cols[0]
            rank_text = rank_col.get_text(strip=True)
            try:
                rank = int(rank_text)
            except ValueError:
                continue

            # 선수명
            title_col = cols[1]
            fighter_link = title_col.find('a')
            if not fighter_link:
                continue

            fighter_name = fighter_link.get_text(strip=True)
            rankings[division][rank] = fighter_name
            logging.debug(f"{division} {rank}위: {fighter_name}")

    return rankings

async def mapping_ranking_fighter(session, ranking_dict: Dict[str, Dict[int, str]]) -> List[RankingSchema]:
    rankings = []
    for division, fighters in ranking_dict.items():
        for rank, fighter_name in fighters.items():
            weight_class_id = WeightClassSchema.get_id_by_name(division.lower())
            if not weight_class_id:
                logging.warning(f"체급 ID를 찾을 수 없습니다: {division}")
                continue

            try:
                # 동명이인이 있을 경우 승수가 가장 많은 선수 선택
                fighter = await get_fighter_by_name_best_record(session, fighter_name)
                if not fighter:
                    logging.warning(f"파이터를 찾을 수 없습니다: {fighter_name}")
                    continue

                rankings.append(RankingSchema(
                    weight_class_id=weight_class_id,
                    ranking=rank,
                    fighter_id=fighter.id
                ))
            except Exception as e:
                logging.error(f"파이터 매핑 실패: {fighter_name} - {str(e)}")
                logging.error(traceback.format_exc())
                continue

    return rankings

async def scrap_rankings(session, crawler_fn: Callable) -> List[RankingSchema]:
    try:
        # 한글 페이지 직접 크롤링 (HTML 파싱 사용)
        rankings_url = "https://kr.ufc.com/rankings"

        html_content = await crawler_fn(rankings_url)
        if not html_content:
            logging.error("랭킹 페이지 크롤링 실패")
            return []

        # HTML 파싱
        ranking_dict = parse_ufc_rankings_from_html(html_content)

        # DB 매핑
        rankings = await mapping_ranking_fighter(session, ranking_dict)

        return rankings

    except Exception as e:
        logging.error(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return []


async def main():
    from data_collector.crawler import crawl_with_httpx, crawl_with_crawl4ai
    from database.connection.postgres_conn import get_async_db_context
    
    try:
        async with get_async_db_context() as session:
            rankings = await scrap_rankings(session, crawl_with_httpx)

        print("total rankings: ", len(rankings))
        for ranking in rankings[:5]:
            print(ranking.model_dump())

    except Exception as e:
        logging.error(f"데이터 저장 중 오류 발생: {traceback.format_exc()}")

if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())