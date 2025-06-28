import re
import asyncio
import logging
import traceback

from typing import List, Callable, Dict

from schemas import Ranking, WeightClass

def parse_ufc_rankings_from_markdown(markdown_content: str) -> Dict[str, Dict[int, str]]:
    """
    UFC 랭킹 마크다운에서 체급별 랭킹을 추출하는 함수
    
    Args:
        markdown_content: crawl4ai로 가져온 마크다운 텍스트
        
    Returns:
        {체급명: {순위: 선수명}} 형태의 딕셔너리
        챔피언은 0순위로 처리
    """
    rankings = {}
    
    # 마크다운을 줄 단위로 분할
    lines = markdown_content.split('\n')
    
    current_division = None
    current_champion = None
    in_ranking_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 체급명 찾기 (#### 로 시작하는 라인)
        if line.startswith('####') and not line.startswith('#####'):
            # 체급명 추출 (#### 이후 텍스트)
            division_match = re.search(r'####\s+(.+)', line)
            if division_match:
                current_division = division_match.group(1).strip()
                in_ranking_section = False
                current_champion = None
                logging.info(f"체급 발견: {current_division}")
                continue
                
        # 챔피언 찾기 (##### [선수명] 패턴)
        if current_division and line.startswith('#####'):
            champion_match = re.search(r'#####\s+\[([^\]]+)\]', line)
            if champion_match:
                current_champion = champion_match.group(1).strip()
                logging.info(f"{current_division} 챔피언: {current_champion}")
                
                # 챔피언을 0순위로 추가
                if current_division not in rankings:
                    rankings[current_division] = {}
                rankings[current_division][0] = current_champion
                continue
                
        # 랭킹 데이터 추출 (숫자 | [선수명] | 변동사항 패턴)
        # 테이블 구분선을 기다리지 않고 바로 랭킹 라인을 찾음
        if current_division and '|' in line:
            # 순위 | [선수명] | 변동사항 패턴 매칭
            ranking_match = re.match(r'^(\d+)\s*\|\s*\[([^\]]+)\]', line)
            if ranking_match:
                rank = int(ranking_match.group(1))
                fighter_name = ranking_match.group(2).strip()
                
                if current_division not in rankings:
                    rankings[current_division] = {}
                rankings[current_division][rank] = fighter_name
                logging.debug(f"{current_division} {rank}위: {fighter_name}")
                
                # 첫 번째 랭킹을 발견했으면 랭킹 섹션 시작으로 표시
                if not in_ranking_section:
                    in_ranking_section = True
                    logging.info(f"{current_division} 랭킹 섹션 시작")
                continue
            
            # 테이블 구분선 (---|---|--- 패턴)
            elif '---|---|---' in line:
                in_ranking_section = True
                logging.info(f"{current_division} 테이블 구분선 발견")
                continue
                
        # 랭킹 섹션 종료 조건
        if in_ranking_section and (line.strip() == '' or line.startswith('#')):
            in_ranking_section = False
    
    return rankings

async def scrap_rankings(crawler_fn: Callable, rankings_url: str) -> List[Ranking]:
    try:
        lang_result = await crawler_fn("https://www.ufc.com/language/switch/en")
        
        if not lang_result.success:
            print(f"언어 설정 실패: {lang_result.error_message}")
            return None 
        
        crawl_result = await crawler_fn(rankings_url)
        if not crawl_result:
            return []
        
        markdown_content = crawl_result.markdown

        rankings = parse_ufc_rankings_from_markdown(markdown_content)
        return rankings
        
    except Exception as e:
        logging.error(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return []


async def main():
    import json
    from datetime import datetime
    from core.crawler import crawl_with_httpx, crawl_with_crawl4ai
    
    try:
        rankings_url = "https://www.ufc.com/rankings"
        rankings = await scrap_rankings(crawl_with_crawl4ai, rankings_url)
        
        # JSON으로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"ufc_rankings_{timestamp}.json"
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)
            
        print(f"\n랜킹 데이터가 {json_filename} 파일에 저장되었습니다.")

    except Exception as e:
        logging.error(f"데이터 저장 중 오류 발생: {traceback.format_exc()}")

if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())