from typing import Optional, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from event.repositories import get_event_by_id
from common.utils import calculate_fighter_accuracy
from match.models import (
    BasicMatchStatSchema,
    SigStrMatchStatSchema,
    BasicMatchStatModel,
    SigStrMatchStatModel
)
from fighter.repositories import (
    get_fighter_by_id,
    get_top_fighter_by_stat
)
from match.repositories import (
    get_fighters_matches,
    get_match_by_id,
    get_fighter_match_by_match_id,
    get_fighter_basic_stats_aggregate, 
    get_fighter_sig_str_stats_aggregate,
)

async def get_fighter_all_matches(session: AsyncSession, fighter_id: int) -> List[Dict]:
    """
    특정 선수의 모든 경기 기록을 조회합니다.
    """
    results = []

    fighter_matches = await get_fighters_matches(session, fighter_id, limit=None)

    for fm in fighter_matches:
        match = await get_match_by_id(session, fm.match_id)
        if not match:
            continue
        weight_class = WeightClassSchema.get_name_by_id(match.weight_class_id)
        event = await get_event_by_id(session, match.event_id)
        participants = await get_fighter_match_by_match_id(session, fm.match_id)
        opponent = next((p for p in participants if p.fighter_id != fighter_id), None)

        results.append({
            "event" : event,
            "opponent" : opponent,
            "match": match,
            "result": fm.result,
            "weight_class": weight_class,
        })

    return results

async def get_fighter_vs_record(
    session: AsyncSession, 
    fighter_id1: int, 
    fighter_id2: int
) -> List[Dict]:
    """
    두 파이터간 과거 대전 기록을 조회합니다.
    """
    # 두 파이터 기본 정보 조회
    fighter1 = await get_fighter_by_id(session, fighter_id1)
    fighter2 = await get_fighter_by_id(session, fighter_id2)
    
    if not fighter1 or not fighter2:
        raise ValueError("One or both fighters not found")
    
    # 두 파이터간 경기 기록 조회
    matches = await get_matches_between_fighters(session, fighter_id1, fighter_id2)
    
    if not matches:
        return []
    
    results = []
    
    for match in matches:
        # 각 경기에서의 파이터 매치 정보 조회
        fighter_matches = await get_fighter_match_by_match_id(session, match.id)
        
        # 각 파이터의 결과 찾기
        fighter1_match = next((fm for fm in fighter_matches if fm.fighter_id == fighter_id1), None)
        fighter2_match = next((fm for fm in fighter_matches if fm.fighter_id == fighter_id2), None)
        
        # 이벤트 정보 조회 (만약 EventModel이 있다면)
        event = await get_event_by_id(session, match.event_id) if match.event_id else None
        
        # 각 파이터의 경기 통계 조회
        fighter1_basic_stats = await get_basic_match_stats(session, fighter_id1, match.id)
        fighter1_sig_str_stats = await get_sig_str_match_stats(session, fighter_id1, match.id)
        
        fighter2_basic_stats = await get_basic_match_stats(session, fighter_id2, match.id)
        fighter2_sig_str_stats = await get_sig_str_match_stats(session, fighter_id2, match.id)
        
        # 체급 정보 (WeightClassSchema가 있다면)
        weight_class = None
        if hasattr(match, 'weight_class_id') and match.weight_class_id:
            weight_class = WeightClassSchema.get_name_by_id(match.weight_class_id)
        
        match_result = {
            "match_info": {
                "event_name": event.name if event else None,
                "event_date": event.date if event else None,
                "is_main_event": match.is_main_event,
                "order": match.order,
                "match_id": match.id,
                "method": match.method,
                "result_round": match.result_round,
                "time": match.time,
                "weight_class": weight_class,
            },
            "fighter1": {
                "info": fighter1,
                "result": fighter1_match.result if fighter1_match else None,
                "basic_stats": fighter1_basic_stats,
                "sig_str_stats": fighter1_sig_str_stats,
            },
            "fighter2": {
                "info": fighter2,
                "result": fighter2_match.result if fighter2_match else None,
                "basic_stats": fighter2_basic_stats,
                "sig_str_stats": fighter2_sig_str_stats,
            }
        }
        
        results.append(match_result)
    
    # 최신 경기순으로 정렬 (match.id 기준)
    results.sort(key=lambda x: x["match_info"]["match_id"], reverse=True)
    
    return results

async def get_fighter_total_stat(session: AsyncSession, fighter_id: int) -> Optional[Dict]:
    """
    특정 선수의 모든 경기 통계를 데이터베이스 레벨에서 필드별로 합산하여 반환합니다.
    """
    fighter = await get_fighter_by_id(session, fighter_id)
    if not fighter:
        return None
    
    total_basic_stats = await get_fighter_basic_stats_aggregate(session, fighter_id)
    
    total_sig_str_stats = await get_fighter_sig_str_stats_aggregate(session, fighter_id)
    
    accuracy_stats = calculate_fighter_accuracy(total_basic_stats, total_sig_str_stats)
    
    return {
        "fighter": fighter,
        "basic_stats": total_basic_stats,
        "sig_str_stats": total_sig_str_stats,
        "accuracy": accuracy_stats,
    }

async def compare_fighters_stats(
    session: AsyncSession,
    fighter_id_1: int,
    fighter_id_2: int,
) -> Optional[Dict]:
    """
    두 선수의 모든 스탯을 비교합니다.
    """
    fighter1 = await get_fighter_by_id(session, fighter_id_1)
    fighter2 = await get_fighter_by_id(session, fighter_id_2)
    
    if not fighter1 or not fighter2:
        raise ValueError("One or both fighters not found")

    # 각 파이터의 통계 데이터 조회
    fighter1_basic_stats = await get_fighter_basic_stats_aggregate(session, fighter_id_1)
    fighter1_sig_str_stats = await get_fighter_sig_str_stats_aggregate(session, fighter_id_1)
    
    fighter2_basic_stats = await get_fighter_basic_stats_aggregate(session, fighter_id_2)
    fighter2_sig_str_stats = await get_fighter_sig_str_stats_aggregate(session, fighter_id_2)
    
    # 정확도 계산
    fighter1_accuracy = calculate_fighter_accuracy(fighter1_basic_stats, fighter1_sig_str_stats)
    fighter2_accuracy = calculate_fighter_accuracy(fighter2_basic_stats, fighter2_sig_str_stats)
    
    # 비교 결과 생성
    comparison = {}
    
    # 기본 통계 비교
    for stat_name in fighter1_basic_stats:
        if stat_name != "match_count":  # 경기 수는 별도 처리
            fighter1_val = fighter1_basic_stats[stat_name]
            fighter2_val = fighter2_basic_stats[stat_name]
            
            comparison[stat_name] = {
                "fighter1_value": fighter1_val,
                "fighter2_value": fighter2_val,
                "winner": "fighter1" if fighter1_val > fighter2_val else "fighter2" if fighter2_val > fighter1_val else "tie"
            }
    
    # 유효 타격 통계 비교
    for stat_name in fighter1_sig_str_stats:
        if stat_name != "match_count":
            fighter1_val = fighter1_sig_str_stats[stat_name]
            fighter2_val = fighter2_sig_str_stats[stat_name]
            
            comparison[stat_name] = {
                "fighter1_value": fighter1_val,
                "fighter2_value": fighter2_val,
                "winner": "fighter1" if fighter1_val > fighter2_val else "fighter2" if fighter2_val > fighter1_val else "tie"
            }
    
    # 정확도 비교
    accuracy_comparison = {}
    for acc_name in fighter1_accuracy:
        fighter1_acc = fighter1_accuracy[acc_name]
        fighter2_acc = fighter2_accuracy[acc_name]
        
        accuracy_comparison[acc_name] = {
            "fighter1_accuracy": fighter1_acc,
            "fighter2_accuracy": fighter2_acc,
            "winner": "fighter1" if fighter1_acc > fighter2_acc else "fighter2" if fighter2_acc > fighter1_acc else "tie"
        }
    
    return {
        "fighter1": {
            "info": fighter1,
            "basic_stats": fighter1_basic_stats,
            "sig_str_stats": fighter1_sig_str_stats,
            "accuracy": fighter1_accuracy,
        },
        "fighter2": {
            "info": fighter2,
            "basic_stats": fighter2_basic_stats,
            "sig_str_stats": fighter2_sig_str_stats,
            "accuracy": fighter2_accuracy,
        },
        "comparison": {
            "stats": comparison,
            "accuracy": accuracy_comparison,
        }
    }

async def get_fighter_with_top_stat(session: AsyncSession, stat_name: str, limit :int = 10) -> Optional[Dict]:
    """
    특정 스탯에서 가장 높은 값을 가진 파이터를 조회
    """
    if stat_name in BasicMatchStatSchema.model_fields:
        stat_model = BasicMatchStatModel
    elif stat_name in SigStrMatchStatSchema.model_fields:
        stat_model = SigStrMatchStatModel
    else:
        raise ValueError(f"Invalid stat_name: {stat_name}")

    result = await get_top_fighter_by_stat(session, stat_model, stat_name, limit)
    
    formatted_result = []
    for idx, (fighter_schema, total_stat) in enumerate(result):
        formatted_result.append({
            "rank": idx + 1,
            "fighter_name": fighter_schema.name,
            "fighter_id": fighter_schema.id,
            "stat_name": stat_name,
            "total_stat": total_stat,
        })
    
    return formatted_result