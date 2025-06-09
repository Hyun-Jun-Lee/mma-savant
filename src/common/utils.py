
def _calculate_percentage(numerator: int, denominator: int) -> float:
    """
    백분율을 계산합니다. 분모가 0이면 0을 반환합니다.
    """
    if not denominator:
        return 0
    return round((numerator / denominator) * 100, 2)

def calculate_fighter_accuracy(basic_stats: Dict, sig_str_stats: Dict) -> Dict:
    """파이터 정확도 계산 헬퍼 함수"""
    return {
        "sig_str_accuracy": _calculate_percentage(basic_stats["sig_str_landed"], basic_stats["sig_str_attempted"]),
        "total_str_accuracy": _calculate_percentage(basic_stats["total_str_landed"], basic_stats["total_str_attempted"]),
        "td_accuracy": _calculate_percentage(basic_stats["td_landed"], basic_stats["td_attempted"]),
        "head_strikes_accuracy": _calculate_percentage(sig_str_stats["head_strikes_landed"], sig_str_stats["head_strikes_attempts"]),
        "body_strikes_accuracy": _calculate_percentage(sig_str_stats["body_strikes_landed"], sig_str_stats["body_strikes_attempts"]),
        "leg_strikes_accuracy": _calculate_percentage(sig_str_stats["leg_strikes_landed"], sig_str_stats["leg_strikes_attempts"]),
        "clinch_strikes_accuracy": _calculate_percentage(sig_str_stats["clinch_strikes_landed"], sig_str_stats["clinch_strikes_attempts"]),
        "ground_strikes_accuracy": _calculate_percentage(sig_str_stats["ground_strikes_landed"], sig_str_stats["ground_strikes_attempts"]),
    }