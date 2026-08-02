# utils/ai_assistant.py
import argparse
import subprocess
from datetime import datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    args = parser.parse_args()

    prompt = f"""你是一个工厂设备问题点录入助手。
请把下面文字解析成结构化问题点。

需要解析的文字：
{args.text}"""

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在调用 Ollama...")

    try:
        result = subprocess.run(
            ["ollama", "run", "qwen2.5:7b", prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120
        )

        raw_output = result.stdout.strip()
        print(f"\n{'=' * 80}")
        print("【Ollama 原始完整输出】")
        print(raw_output)
        print(f"{'=' * 80}\n")

        # 直接返回原始文字（不做任何JSON解析）
        print('{"raw_output": "' + raw_output.replace('"', '\\"') + '"}')

    except Exception as e:
        print(f"调用失败: {e}")


if __name__ == "__main__":
    main()