import logging
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

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

def scrap_match_detail_total(html_path: str) -> Dict:
    """
    UFC 경기 상세 페이지에서 데이터를 추출합니다.
    
    Args:
        html_path (str): HTML 파일 경로
        
    Returns:
        Dict: 추출된 경기 상세 정보
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    # 테이블 찾기
    table = soup.find('table', {'class': 'b-fight-details__table'})
    if not table:
        logging.warning(f"테이블을 찾을 수 없습니다: {html_path}")
        return {}
    
    # 선수별 통계 데이터 추출
    fighter_1_rounds = []
    fighter_2_rounds = []
    rows = table.find_all('tr', class_='b-fight-details__table-row')[1:]  # 헤더 제외
    
    for round_num, row in enumerate(rows, 1):
        cols = row.find_all('td', class_='b-fight-details__table-col')
        if not cols:
            continue

        fighter_text = cols[0].get_text(strip=False).lstrip()
        fighters = [name.strip() for name in fighter_text.split('\n') if name.strip()]
        fighter_1, fighter_2 = fighters[:2]
        
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

        # fighter_1 데이터 구성
        fighter_1_stats = {
            'knockdowns': kd_1,
            'control_time_seconds': ctrl_time_1,
            'submission_attempts': sub_att_1,
            **sig_str_1,
            **total_str_1,
            **td_1
        }
        
        # fighter_2 데이터 구성
        fighter_2_stats = {
            'knockdowns': kd_2,
            'control_time_seconds': ctrl_time_2,
            'submission_attempts': sub_att_2,
            **sig_str_2,
            **total_str_2,
            **td_2
        }
        
        # 라운드 번호 추가
        fighter_1_stats['round'] = round_num
        fighter_2_stats['round'] = round_num
        
        fighter_1_rounds.append(fighter_1_stats)
        fighter_2_rounds.append(fighter_2_stats)
    
    # 총계 통계 계산
    fighter_1_total = calculate_total_stats(fighter_1_rounds)
    fighter_2_total = calculate_total_stats(fighter_2_rounds)
    
    return {
        'fighter_1': {
            'name': fighter_1,
            'rounds': fighter_1_rounds,
            'total': fighter_1_total
        },
        'fighter_2': {
            'name': fighter_2,
            'rounds': fighter_2_rounds,
            'total': fighter_2_total
        }
    }

if __name__ == "__main__":
    # 테스트용 코드
    html_path = "./downloaded_pages/fight-details_f39941b3743bf18c_20250210.html"
    match_details = scrap_match_detail_total(html_path)
    print(match_details)
