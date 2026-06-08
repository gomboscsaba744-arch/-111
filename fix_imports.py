import os
import glob

for py_file in glob.glob("automators/*.py"):
    with open(py_file, "r") as f:
        content = f.read()
    
    if "from automators.excel_utils import save_df_to_excel" in content:
        # Remove it from the top
        content = content.replace("from automators.excel_utils import save_df_to_excel\n", "")
        # Add it after sys.path.append
        content = content.replace("from config import", "from automators.excel_utils import save_df_to_excel\nfrom config import")
        
        with open(py_file, "w") as f:
            f.write(content)
