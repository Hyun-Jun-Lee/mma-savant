import logging
from typing import Dict, List, Callable
import asyncio
import traceback

from bs4 import BeautifulSoup

from schemas import FighterMatch, BasicMatchStat, SigStrMatchStat

def parse_stat_with_of(text: str, kind: str) -> Dict[str, str]:
    """
    'X of Y' 형식의 텍스트를 파싱합니다.
    
    Args:
        text: 파싱할 텍스트 (예: '45 of 123')
        
    Returns:
        Dict[str, str]: {'landed': 'X', 'attempted': 'Y'} 형식의 딕셔너리
    """
    landed, attempted = map(str.strip, text.split('of'))
    return {f'{kind}_landed': landed, f'{kind}_attempted': attempted}

def convert_time_to_seconds(time_str):
    """Convert time string (M:SS) to seconds"""
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds

def calculate_sig_total_stats(rounds: List[Dict]) -> Dict:
    """
    모든 라운드의 significant strikes 통계를 합산합니다.
    """
    total = {
        'head_landed': 0,
        'head_attempted': 0,
        'body_landed': 0,
        'body_attempted': 0,
        'leg_landed': 0,
        'leg_attempted': 0,
        'distance_landed': 0,
        'distance_attempted': 0,
        'clinch_landed': 0,
        'clinch_attempted': 0,
        'ground_landed': 0,
        'ground_attempted': 0
    }
    
    for round_stats in rounds:
        for key in total.keys():
            total[key] += int(round_stats[key])
    
    # 숫자를 문자열로 변환
    return {k: str(v) for k, v in total.items()}

def calculate_total_stats(rounds: List[Dict]) -> Dict:
    """
    모든 라운드의 통계를 합산합니다.
    """
    total = {
        'knockdowns': 0,
        'control_time_seconds': 0,
        'submission_attempts': 0,
        'sig_str_landed': 0,
        'sig_str_attempted': 0,
        'total_str_landed': 0,
        'total_str_attempted': 0,
        'td_landed': 0,
        'td_attempted': 0
    }
    
    for round_stats in rounds:
        total['knockdowns'] += int(round_stats['knockdowns'])
        total['control_time_seconds'] += round_stats['control_time_seconds']
        total['submission_attempts'] += int(round_stats['submission_attempts'])
        total['sig_str_landed'] += int(round_stats['sig_str_landed'])
        total['sig_str_attempted'] += int(round_stats['sig_str_attempted'])
        total['total_str_landed'] += int(round_stats['total_str_landed'])
        total['total_str_attempted'] += int(round_stats['total_str_attempted'])
        total['td_landed'] += int(round_stats['td_landed'])
        total['td_attempted'] += int(round_stats['td_attempted'])
    
    # 숫자를 문자열로 변환
    return {k: str(v) for k, v in total.items()}

async def scrape_match_basic_statistics(crawler_fn: Callable, match_detail_url: str, fighter_dict: Dict[str, int] = None, fighter_match_dict: Dict[int, FighterMatch] = None) -> List[BasicMatchStat]:
    """
    UFC 경기 상세 페이지에서 데이터를 추출합니다.
    """
    try:
        html_content = await crawler_fn(match_detail_url)
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logging.error(f"매치 기본 통계 크롤링 중 오류 발생: {traceback.format_exc()}")
        return []
    
    # 테이블 찾기
    table = soup.find('table', {'class': 'b-fight-details__table'})
    if not table:
        logging.warning(f"테이블을 찾을 수 없습니다: {html_path}")
        return {}
    
    # 선수별 통계 데이터 추출
    fighter_rounds = []
    rows = table.find_all('tr', class_='b-fight-details__table-row')[1:]  # 헤더 제외
    
    for round_num, row in enumerate(rows, 1):
        cols = row.find_all('td', class_='b-fight-details__table-col')
        if not cols:
            continue

        fighter_text = cols[0].get_text(strip=False).lstrip()
        fighters = [name.strip() for name in fighter_text.split('\n') if name.strip()]
        fighter_1, fighter_2 = fighters[:2]
        fighter_1_id, fighter_2_id = fighter_dict.get(fighter_1.lower().strip(), 0), fighter_dict.get(fighter_2.lower().strip(), 0)
        fighter_1_match = fighter_match_dict.get(fighter_1_id, None)
        fighter_2_match = fighter_match_dict.get(fighter_2_id, None)
        
        if not fighter_1_match or not fighter_2_match:
            logging.warning(f"매치 정보를 찾을 수 없습니다: {fighter_1} vs {fighter_2}, - {match_detail_url}")
            continue
        
        kd_text = cols[1].get_text(strip=False).lstrip().split('\n')
        kd_data = [kd.strip() for kd in kd_text if kd.strip()]
        kd_1, kd_2 = kd_data[:2]
            
        sig_str_data = [sig_str.strip() for sig_str in cols[2].get_text(strip=False).lstrip().split('\n') if sig_str.strip()]
        sig_str_1, sig_str_2 = map(parse_stat_with_of, sig_str_data[:2], ["sig_str", "sig_str"])

        total_str_data = [sig_str.strip() for sig_str in cols[4].get_text(strip=False).lstrip().split('\n') if sig_str.strip()]
        total_str_1, total_str_2 = map(parse_stat_with_of, total_str_data[:2], ["total_str", "total_str"])
        
        td_data = [td.strip() for td in cols[5].get_text(strip=False).lstrip().split('\n') if td.strip()]
        td_1, td_2 = map(parse_stat_with_of, td_data[:2], ["td", "td"])
        
        sub_att_data = [sub_att.strip() for sub_att in cols[7].get_text(strip=False).lstrip().split('\n') if sub_att.strip()]
        sub_att_1, sub_att_2 = sub_att_data[:2]
        
        ctrl_time_data = [ctrl_time.strip() for ctrl_time in cols[9].get_text(strip=False).lstrip().split('\n') if ctrl_time.strip()]
        ctrl_time_1, ctrl_time_2 = [convert_time_to_seconds(t) for t in ctrl_time_data[:2]]

        # TODO : BasicMatchStat
        fighter_1_match_statistics = BasicMatchStat(
            fighter_match_id=fighter_1_match.id,
            knockdowns=kd_1,
            control_time_seconds=ctrl_time_1,
            submission_attempts=sub_att_1,
            sig_str_landed=sig_str_1['sig_str_landed'],
            sig_str_attempted=sig_str_1['sig_str_attempted'],
            total_str_landed=total_str_1['total_str_landed'],
            total_str_attempted=total_str_1['total_str_attempted'],
            td_landed=td_1['td_landed'],
            td_attempted=td_1['td_attempted'],
            round=round_num
        )
        fighter_2_match_statistics = BasicMatchStat(
            fighter_match_id=fighter_2_match.id,
            knockdowns=kd_2,
            control_time_seconds=ctrl_time_2,
            submission_attempts=sub_att_2,
            sig_str_landed=sig_str_2['sig_str_landed'],
            sig_str_attempted=sig_str_2['sig_str_attempted'],
            total_str_landed=total_str_2['total_str_landed'],
            total_str_attempted=total_str_2['total_str_attempted'],
            td_landed=td_2['td_landed'],
            td_attempted=td_2['td_attempted'],
            round=round_num
        )
        
        fighter_rounds.append(fighter_1_match_statistics)
        fighter_rounds.append(fighter_2_match_statistics)
    
    # NOTE : total 값이 필요한가?
    # fighter_1_total = calculate_total_stats(fighter_1_rounds)
    # fighter_2_total = calculate_total_stats(fighter_2_rounds)

    return fighter_rounds

async def scrape_match_significant_strikes(crawler_fn: Callable, match_detail_url: str, fighter_dict: Dict[str, int] = None, fighter_match_dict: Dict[int, FighterMatch] = None) -> List[SigStrMatchStat]:
    """
    UFC 경기 상세 페이지에서 significant strikes 데이터를 추출합니다.
    """
    try:
        html_content = await crawler_fn(match_detail_url)
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logging.error(f"유의미한 타격 통계 크롤링 중 오류 발생: {traceback.format_exc()}")
        return []
    
    # Significant Strikes 테이블 찾기
    sig_tables = soup.find_all('table', class_='b-fight-details__table')
    sig_table = None
    
    # 정확한 테이블 찾기 - Head, Body, Leg 컬럼이 있는 테이블
    for table in sig_tables:
        headers = table.find_all('th', class_='b-fight-details__table-col')
        header_texts = [h.text.strip() for h in headers]
        if 'Head' in header_texts and 'Body' in header_texts and 'Leg' in header_texts:
            sig_table = table
            break
    
    if not sig_table:
        print(f"Significant strikes 테이블을 찾을 수 없습니다 - {match_detail_url}")
        return []
    
    # 라운드별 데이터 추출
    fighter_rounds = []
    rows = sig_table.find_all('tr', class_='b-fight-details__table-row')[1:]  # 헤더 제외
    
    for round_num, row in enumerate(rows, 1):
        cols = row.find_all('td', class_='b-fight-details__table-col')
            
        fighter_text = cols[0].get_text(strip=False).lstrip()
        fighters = [name.strip() for name in fighter_text.split('\n') if name.strip()]
        fighter_1, fighter_2 = fighters[:2]
        fighter_1_id, fighter_2_id = fighter_dict.get(fighter_1.lower().strip(), 0), fighter_dict.get(fighter_2.lower().strip(), 0)
        fighter_1_match = fighter_match_dict.get(fighter_1_id, None)
        fighter_2_match = fighter_match_dict.get(fighter_2_id, None)

        # 모든 타격 데이터 추출
        head_data = [head.strip() for head in cols[3].get_text(strip=False).lstrip().split('\n') if head.strip()]
        head_1, head_2 = map(parse_stat_with_of, head_data[:2], ["head", "head"])
        
        body_data = [body.strip() for body in cols[4].get_text(strip=False).lstrip().split('\n') if body.strip()]
        body_1, body_2 = map(parse_stat_with_of, body_data[:2], ["body", "body"])
        
        leg_data = [leg.strip() for leg in cols[5].get_text(strip=False).lstrip().split('\n') if leg.strip()]
        leg_1, leg_2 = map(parse_stat_with_of, leg_data[:2], ["leg", "leg"])
        
        distance_data = [dist.strip() for dist in cols[6].get_text(strip=False).lstrip().split('\n') if dist.strip()]
        distance_1, distance_2 = map(parse_stat_with_of, distance_data[:2], ["distance", "distance"])
        
        clinch_data = [clinch.strip() for clinch in cols[7].get_text(strip=False).lstrip().split('\n') if clinch.strip()]
        clinch_1, clinch_2 = map(parse_stat_with_of, clinch_data[:2], ["clinch", "clinch"])
        
        ground_data = [ground.strip() for ground in cols[8].get_text(strip=False).lstrip().split('\n') if ground.strip()]
        ground_1, ground_2 = map(parse_stat_with_of, ground_data[:2], ["ground", "ground"])

        fighter_1_strike_detail = SigStrMatchStat(
            fighter_match_id=fighter_1_match.id,
            head_strikes_landed=head_1['head_landed'],
            head_strikes_attempts=head_1['head_attempted'],
            body_strikes_landed=body_1['body_landed'],
            body_strikes_attempts=body_1['body_attempted'],
            leg_strikes_landed=leg_1['leg_landed'],
            leg_strikes_attempts=leg_1['leg_attempted'],
            clinch_strikes_landed=clinch_1['clinch_landed'],
            clinch_strikes_attempts=clinch_1['clinch_attempted'],
            ground_strikes_landed=ground_1['ground_landed'],
            ground_strikes_attempts=ground_1['ground_attempted'],
            round=round_num
        )
        
        fighter_2_strike_detail = SigStrMatchStat(
            fighter_match_id=fighter_2_match.id,
            head_strikes_landed=head_2['head_landed'],
            head_strikes_attempts=head_2['head_attempted'],
            body_strikes_landed=body_2['body_landed'],
            body_strikes_attempts=body_2['body_attempted'],
            leg_strikes_landed=leg_2['leg_landed'],
            leg_strikes_attempts=leg_2['leg_attempted'],
            clinch_strikes_landed=clinch_2['clinch_landed'],
            clinch_strikes_attempts=clinch_2['clinch_attempted'],
            ground_strikes_landed=ground_2['ground_landed'],
            ground_strikes_attempts=ground_2['ground_attempted'],
            round=round_num
        )
        
        fighter_rounds.append(fighter_1_strike_detail)
        fighter_rounds.append(fighter_2_strike_detail)
    
    return fighter_rounds

async def main():
    from core.crawler import crawl_with_httpx

    try:
        # 테스트용 코드
        match_detail_url = "http://ufcstats.com/fight-details/d13849f49f99bf01"
        fighter_dict = {
            "Stefan Struve": 1,
            "Khabib Nurmagomedov": 2
        }
        fighter_match_dict = {
            1: FighterMatch(id=1, fighter_id=1, match_id=1),
            2: FighterMatch(id=2, fighter_id=2, match_id=1)
        }
        basic_stats = await scrape_match_basic_statistics(crawl_with_httpx, match_detail_url, fighter_dict, fighter_match_dict)
        sig_stats = await scrape_match_significant_strikes(crawl_with_httpx, match_detail_url, fighter_dict, fighter_match_dict)
        
        logging.info(f"기본 매치 통계: {len(basic_stats)}개 항목 추출됨")
        logging.info(f"유의미한 타격 통계: {len(sig_stats)}개 항목 추출됨")
        
        # 결과 출력 (첫 번째 항목만 샘플로 표시)
        if basic_stats:
            logging.info(f"기본 통계 예시: {basic_stats[0]}")
        if sig_stats:
            logging.info(f"타격 통계 예시: {sig_stats[0]}")
            
    except Exception as e:
        logging.error(f"메인 함수 실행 중 오류 발생: {traceback.format_exc()}")

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 비동기 실행
    asyncio.run(main())