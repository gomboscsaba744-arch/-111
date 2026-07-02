with open('app.py', 'r') as f:
    content = f.read()

start_marker = 'with st.expander("🎛️ VANGUARD 光效引擎 (Visual Engine Tuning)"'
end_marker = "''', height=0)\n"

start_idx = content.find(start_marker)
if start_idx != -1:
    end_idx = content.find(end_marker, start_idx) + len(end_marker)
    
    # Extract the block
    block = content[start_idx:end_idx]
    
    # Remove it from current location
    content = content[:start_idx] + content[end_idx:]
    
    # Append to the very end of the file
    content = content.rstrip() + "\n\n" + block
    
    with open('app.py', 'w') as f:
        f.write(content)
    print("Successfully moved to bottom.")
else:
    print("Block not found!")
