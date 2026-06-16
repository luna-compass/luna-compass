# utils/session_logger.py
# セッション履歴の記録と管理

import os
import csv
import datetime
import streamlit as st
from pathlib import Path


LOG_FILE = "data/session_log.csv"


def init_log_file():
    """ログファイルが存在しなければ作成"""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "reading_type",  # "general" / "compat" / "tarot"
                "user_name",
                "mode",  # "自分を占う" / "別の人を占う"
                "session_duration_sec",
                "status"  # "success" / "error" / "cancelled"
            ])


def log_session(reading_type, user_name="Guest", mode="自分を占う", duration_sec=0, status="success"):
    """セッションをログに記録"""
    init_log_file()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            reading_type,
            user_name,
            mode,
            duration_sec,
            status
        ])


def get_session_logs():
    """ログをすべて読み込む"""
    init_log_file()
    logs = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            logs = list(reader)
    except Exception as e:
        st.error(f"ログ読み込みエラー: {e}")
    return logs


def get_today_sessions():
    """本日のセッションを取得"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    logs = get_session_logs()
    return [log for log in logs if log["timestamp"].startswith(today)]


def get_session_stats():
    """統計情報を計算して返す"""
    logs = get_session_logs()
    
    if not logs:
        return {
            "total": 0,
            "today": 0,
            "by_type": {},
            "success_rate": 0,
            "avg_duration": 0,
        }
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_logs = [log for log in logs if log["timestamp"].startswith(today)]
    
    # 占い種別ごとの集計
    by_type = {}
    for log in logs:
        rt = log["reading_type"]
        by_type[rt] = by_type.get(rt, 0) + 1
    
    # 成功率
    success_count = len([log for log in logs if log["status"] == "success"])
    success_rate = (success_count / len(logs) * 100) if logs else 0
    
    # 平均実行時間
    try:
        durations = [float(log["session_duration_sec"]) for log in logs if log["session_duration_sec"]]
        avg_duration = sum(durations) / len(durations) if durations else 0
    except:
        avg_duration = 0
    
    return {
        "total": len(logs),
        "today": len(today_logs),
        "by_type": by_type,
        "success_rate": round(success_rate, 1),
        "avg_duration": round(avg_duration, 1),
    }


def clear_logs():
    """ログを全削除（管理者用）"""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    init_log_file()
