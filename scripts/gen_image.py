#!/usr/bin/env python3
"""
APIMart gpt-image-2 生图工具（当前项目专用）
============================================
昨天在 AI-Canvas 项目验证过的链路：提交任务 -> 轮询 /v1/tasks/{id} -> 下载图片。

特性：
- 文生图 / 图生图（参考图 image_urls，URL + base64 混填，最多 16 张）
- 默认 gpt-image-2, resolution=1k, size=auto
- 走 Clash Verge 代理 127.0.0.1:7897
- 零依赖：仅用 curl + python 标准库

用法：
  python scripts/gen_image.py --prompt "一只橘猫坐在窗台看夕阳，水彩画"
  python scripts/gen_image.py --prompt "把这张照片变成水彩画" --ref ./photo.jpg --ref https://example.com/a.png
  python scripts/gen_image.py --prompt "..." --size "3:4" --resolution "2k" --n 2

API Key 从环境变量 APIMART_API_KEY 读取（或 .env 文件）。
"""
import argparse
import base64
import json
import mimetypes
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------- 配置 ----------
PROXY = os.environ.get("APIMART_PROXY", "http://127.0.0.1:7897")
BASE_URL = "https://api.apimart.ai/v1"
MODEL = "gpt-image-2"
DEFAULT_SIZE = "auto"
DEFAULT_RESOLUTION = "1k"
POLL_INTERVAL = 3  # 秒
MAX_POLLS = 100
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "images"


def load_api_key() -> str:
    """从环境变量或项目 .env 读取 API key。"""
    key = os.environ.get("APIMART_API_KEY", "")
    if key:
        return key
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("APIMART_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("❌ 未找到 API key：请设置环境变量 APIMART_API_KEY，或在项目 .env 中写入 APIMART_API_KEY=sk-...")
    sys.exit(1)


def to_data_url(path: str) -> str:
    """本地文件 -> data URL（用于 image_urls 参考图）。"""
    p = Path(path)
    if not p.exists():
        print(f"❌ 参考图不存在: {path}")
        sys.exit(1)
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def run_curl(args: list, timeout: int = 60) -> dict:
    """执行 curl（带代理），解析 JSON 返回。"""
    cmd = ["curl", "-s", "--proxy", PROXY] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        print(f"❌ curl 失败: {result.stderr}")
        sys.exit(1)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"❌ 响应不是 JSON: {result.stdout[:500]}")
        sys.exit(1)


def submit_task(payload: dict, api_key: str) -> str:
    # Windows 命令行长度限制（WinError 206）：长提示词改用临时文件传参
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
        tmp_path = f.name
    try:
        data = run_curl([
            "-X", "POST",
            f"{BASE_URL}/images/generations",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-d", f"@{tmp_path}",
        ], timeout=120)
    finally:
        os.unlink(tmp_path)
    try:
        task_id = data["data"][0]["task_id"]
        print(f"✅ 任务已提交: {task_id}")
        return task_id
    except (KeyError, IndexError, TypeError):
        print(f"❌ 提交失败: {json.dumps(data, ensure_ascii=False)[:500]}")
        sys.exit(1)


def poll_task(task_id: str, api_key: str) -> dict:
    for i in range(MAX_POLLS):
        time.sleep(POLL_INTERVAL)
        data = run_curl([
            f"{BASE_URL}/tasks/{task_id}",
            "-H", f"Authorization: Bearer {api_key}",
        ], timeout=30)
        try:
            status = data["data"]["status"]
        except (KeyError, TypeError):
            print(f"❌ 查询失败: {json.dumps(data, ensure_ascii=False)[:500]}")
            sys.exit(1)
        if status == "completed":
            print(f"✅ 生成完成（第 {i + 1} 次轮询）")
            return data["data"]["result"]
        if status == "failed":
            err = data["data"].get("error", {}).get("message", "unknown error")
            print(f"❌ 生成失败: {err}")
            sys.exit(1)
        print(f"⏳ 生成中... ({status}) 第 {i + 1}/{MAX_POLLS} 次轮询")
    print("❌ 轮询超时")
    sys.exit(1)


def download_image(url: str, out_path: Path):
    subprocess.run(
        ["curl", "-s", "-o", str(out_path), url],
        capture_output=True, timeout=60,
    )
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"📸 已保存: {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")
        # 双格式输出：MEDIA: 行 + markdown 图片标签（Hermes 桌面端内联显示用）
        win_path = str(out_path).replace("/", "\\")
        print(f"MEDIA:{win_path}")
        print(f"![生成图片]({win_path})")
    else:
        print(f"❌ 下载失败: {url}")


def main():
    parser = argparse.ArgumentParser(description="APIMart gpt-image-2 生图")
    parser.add_argument("--prompt", required=True, help="生成提示词")
    parser.add_argument("--ref", action="append", default=[], help="参考图（URL 或本地路径，可多个）")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"图片比例，默认 {DEFAULT_SIZE}")
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION, help=f"分辨率档位，默认 {DEFAULT_RESOLUTION} (1k/2k/4k)")
    parser.add_argument("--n", type=int, default=1, help="生成数量，默认 1")
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT), help="输出目录")
    parser.add_argument("--output-name", default="", help="输出文件名（不含扩展名）")
    args = parser.parse_args()

    api_key = load_api_key()

    payload = {
        "model": MODEL,
        "prompt": args.prompt,
        "n": args.n,
        "size": args.size,
        "resolution": args.resolution,
    }
    if args.ref:
        refs = []
        for r in args.ref:
            refs.append(to_data_url(r) if not r.startswith(("http://", "https://", "data:")) else r)
        payload["image_urls"] = refs
        print(f"🖼️ 图生图模式，{len(refs)} 张参考图")

    print(f"🎨 提交生成: model={MODEL} size={args.size} resolution={args.resolution} n={args.n}")
    task_id = submit_task(payload, api_key)
    result = poll_task(task_id, api_key)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    images = result.get("images", [])
    if not images:
        print(f"❌ 结果中没有图片: {json.dumps(result, ensure_ascii=False)[:500]}")
        sys.exit(1)

    name = args.output_name or f"gen_{time.strftime('%Y%m%d_%H%M%S')}"
    for i, img in enumerate(images):
        url = img["url"][0] if isinstance(img.get("url"), list) else img["url"]
        ext = ".png"
        suffix = f"_{i + 1}" if len(images) > 1 else ""
        download_image(url, out_dir / f"{name}{suffix}{ext}")


if __name__ == "__main__":
    main()
