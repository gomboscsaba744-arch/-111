import glob
from automators.telegram_cpf_bot import solve_math_captcha

images = sorted(glob.glob("scratch/debug_captchas/*.png")) + sorted(glob.glob("scratch/failed_captcha_*.png"))
total = len(images)
correct = 0

for f in images:
    with open(f, "rb") as fp:
        image_bytes = fp.read()
    print(f"--- {f} ---")
    try:
        ans, poss = solve_math_captcha(image_bytes)
        print("Ans:", ans, "Poss:", poss)
    except Exception as e:
        print("Error:", e)
