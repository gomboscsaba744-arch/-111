import asyncio
from automators.telegram_cpf_bot import solve_math_captcha
import glob

for f in sorted(glob.glob("scratch/failed_captcha_*.png")):
    print(f"--- {f} ---")
    with open(f, "rb") as fp:
        image_bytes = fp.read()
    try:
        certain_ans, possible_answers = solve_math_captcha(image_bytes)
        print("Certain:", certain_ans)
        print("Possible:", possible_answers)
    except Exception as e:
        print("Error:", e)
