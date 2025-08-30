#!/usr/bin/env python3
"""
AI観光解析システム - Processing Time 統計分析
DynamoDB ai-tourism-poc-analyze-logs-dev テーブルの解析処理時間分析
"""
import statistics
import json
from datetime import datetime

# DynamoDBから取得したprocessing_time_ms値
processing_times = [
    9607, 7757, 8690, 13678, 6944, 10246, 9594, 12969, 7125, 9071,
    7710, 10918, 9318, 14332, 8219, 7176, 8134, 6142, 7681, 6544,
    10919, 7898, 10014, 9784, 8510, 9464, 10878, 8926, 9704, 8859,
    10740, 8406, 10623, 13605, 9743, 14142, 9658
]

def analyze_processing_times():
    """Processing Time統計分析"""
    
    # 基本統計
    total_count = len(processing_times)
    average_ms = statistics.mean(processing_times)
    median_ms = statistics.median(processing_times)
    min_ms = min(processing_times)
    max_ms = max(processing_times)
    stdev_ms = statistics.stdev(processing_times)
    
    # 秒単位での表示用
    average_sec = average_ms / 1000
    median_sec = median_ms / 1000
    min_sec = min_ms / 1000
    max_sec = max_ms / 1000
    
    # パーセンタイル計算
    p75_ms = statistics.quantiles(processing_times, n=4)[2]  # 75th percentile
    p90_ms = statistics.quantiles(processing_times, n=10)[8]  # 90th percentile
    p95_ms = statistics.quantiles(processing_times, n=20)[18]  # 95th percentile
    
    # 分布分析
    fast_count = len([t for t in processing_times if t < 8000])
    medium_count = len([t for t in processing_times if 8000 <= t <= 12000])
    slow_count = len([t for t in processing_times if t > 12000])
    
    # レポート生成
    report = {
        "analysis_date": datetime.now().isoformat(),
        "data_source": "ai-tourism-poc-analyze-logs-dev",
        "sample_size": total_count,
        "statistics": {
            "average_ms": round(average_ms, 2),
            "average_sec": round(average_sec, 2),
            "median_ms": round(median_ms, 2),
            "median_sec": round(median_sec, 2),
            "min_ms": min_ms,
            "min_sec": round(min_sec, 2),
            "max_ms": max_ms,
            "max_sec": round(max_sec, 2),
            "standard_deviation_ms": round(stdev_ms, 2),
            "percentiles": {
                "75th_ms": round(p75_ms, 2),
                "90th_ms": round(p90_ms, 2),
                "95th_ms": round(p95_ms, 2)
            }
        },
        "performance_distribution": {
            "fast_responses": {
                "count": fast_count,
                "percentage": round((fast_count/total_count)*100, 1),
                "description": "< 8秒"
            },
            "medium_responses": {
                "count": medium_count,
                "percentage": round((medium_count/total_count)*100, 1),
                "description": "8-12秒"
            },
            "slow_responses": {
                "count": slow_count,
                "percentage": round((slow_count/total_count)*100, 1),
                "description": "> 12秒"
            }
        },
        "recommendations": []
    }
    
    # パフォーマンス評価
    if average_sec > 12:
        report["recommendations"].append("平均応答時間が12秒を超過 - Lambda関数の最適化が必要")
    elif average_sec > 10:
        report["recommendations"].append("平均応答時間が10秒超 - パフォーマンス監視強化推奨")
    else:
        report["recommendations"].append("平均応答時間は良好 - 現在の設定を維持")
    
    if slow_count / total_count > 0.2:
        report["recommendations"].append(f"全体の{round((slow_count/total_count)*100, 1)}%が12秒超 - Gemini API最適化が必要")
    
    if max_sec > 14:
        report["recommendations"].append("最大応答時間が14秒超 - タイムアウト設定の見直し推奨")
    
    return report

if __name__ == "__main__":
    result = analyze_processing_times()
    
    print("=" * 60)
    print("🤖 AI観光解析システム - Processing Time 統計分析")
    print("=" * 60)
    print(f"📊 分析日時: {result['analysis_date']}")
    print(f"📈 データソース: {result['data_source']}")
    print(f"🔢 サンプル数: {result['sample_size']}件")
    print()
    
    stats = result['statistics']
    print("📈 基本統計:")
    print(f"  平均応答時間: {stats['average_ms']}ms ({stats['average_sec']}秒)")
    print(f"  中央値:       {stats['median_ms']}ms ({stats['median_sec']}秒)")
    print(f"  最小値:       {stats['min_ms']}ms ({stats['min_sec']}秒)")
    print(f"  最大値:       {stats['max_ms']}ms ({stats['max_sec']}秒)")
    print(f"  標準偏差:     {stats['standard_deviation_ms']}ms")
    print()
    
    print("📊 パーセンタイル:")
    percentiles = stats['percentiles']
    print(f"  75th percentile: {percentiles['75th_ms']}ms")
    print(f"  90th percentile: {percentiles['90th_ms']}ms")
    print(f"  95th percentile: {percentiles['95th_ms']}ms")
    print()
    
    print("⚡ パフォーマンス分布:")
    dist = result['performance_distribution']
    print(f"  高速応答 ({dist['fast_responses']['description']}):   {dist['fast_responses']['count']}件 ({dist['fast_responses']['percentage']}%)")
    print(f"  標準応答 ({dist['medium_responses']['description']}): {dist['medium_responses']['count']}件 ({dist['medium_responses']['percentage']}%)")
    print(f"  低速応答 ({dist['slow_responses']['description']}):   {dist['slow_responses']['count']}件 ({dist['slow_responses']['percentage']}%)")
    print()
    
    print("💡 推奨事項:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"  {i}. {rec}")
    print()
    
    print("=" * 60)
    print("✅ 分析完了")
    print("=" * 60)
    
    # JSON出力も行う
    with open('processing_time_report.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("📄 詳細レポート: processing_time_report.json に保存")