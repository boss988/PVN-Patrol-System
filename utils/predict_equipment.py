import argparse
import json
import pandas as pd
from datetime import datetime

def load_data(input_file):
    try:
        df = pd.read_csv(input_file)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 成功读取CSV，共 {len(df)} 行数据")
        return df
    except Exception as e:
        raise ValueError(f"读取CSV失败: {e}")

def predict_health(df):
    # 这里是模拟预测逻辑，实际可以改成更复杂的模型
    ai_score = 75
    fault_prob = 40
    remaining_life = 365
    suggestion = "加强设备巡检，重点关注振动和备件库存情况。"
    top_risks = ["ct_deviation", "maintenance_overdue"]

    return {
        "ai_score": ai_score,
        "fault_prob_next_week": fault_prob,
        "remaining_life_days": remaining_life,
        "suggestion": suggestion,
        "top_risks": top_risks
    }

def save_results(output_file, result):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 预测完成，结果已保存到: {output_file}")
    except Exception as e:
        raise ValueError(f"保存JSON失败: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default='result.json')
    args = parser.parse_args()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始分析: {args.input}")

    df = load_data(args.input)
    result = predict_health(df)
    save_results(args.output, result)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 预测全部完成！")

if __name__ == "__main__":
    main()