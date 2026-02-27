"""
Fix datetime.utcnow() deprecation warnings
Replace with datetime.now(timezone.utc)
"""

import os
import re

files_to_fix = [
    'history/history_service.py',
    'alerts/alert_service.py',
    'satellites/satellite_manager.py',
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if timezone is imported
    if 'from datetime import' in content and 'timezone' not in content:
        # Add timezone to imports
        content = re.sub(
            r'from datetime import ([^\n]+)',
            lambda m: f"from datetime import {m.group(1)}, timezone" if 'timezone' not in m.group(1) else m.group(0),
            content,
            count=1
        )
    
    # Replace datetime.utcnow() with datetime.now(timezone.utc)
    original_count = content.count('datetime.utcnow()')
    content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
    new_count = content.count('datetime.now(timezone.utc)')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Fixed {filepath}: {original_count} replacements")

print("\n✓ All datetime warnings fixed!")
