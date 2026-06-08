with open('automators/mabang_export_bot.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "await target.evaluate(\"let el = document.getElementById('fuzzySearchValue')" in line:
        lines[i] = "                await target.evaluate('''let el = document.getElementById('fuzzySearchValue'); if(!el) el = document.querySelector('input[name=\"OrderSearch.fuzzySearchValue\"]'); if(el) el.disabled = false;''')\n"
        break

with open('automators/mabang_export_bot.py', 'w') as f:
    f.writelines(lines)
