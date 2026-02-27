"""
Fix api.py structure by moving Phase 1 and Phase 2 endpoints before if __name__ == '__main__'
"""

# Read the file
with open('api.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find the key sections
main_block_marker = "if __name__ == '__main__':"
phase1_marker = "# ============================================================================\n# PHASE 1: HISTORY TRACKING & SATELLITE MANAGEMENT"
phase2_marker = "# ============================================================================\n# PHASE 2: ALERTS & MANEUVER RECOMMENDATIONS"

# Split the content
main_block_start = content.find(main_block_marker)
phase1_start = content.find(phase1_marker)
phase2_start = content.find(phase2_marker)

# Extract sections
before_main = content[:main_block_start].rstrip() + "\n\n"
main_block = content[main_block_start:phase1_start].rstrip() + "\n"
phase1_and_2 = content[phase1_start:].rstrip() + "\n"

# Reorganize: before_main + phase1_and_2 + main_block
new_content = before_main + phase1_and_2 + "\n\n" + main_block

# Write back
with open('api.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ api.py structure fixed!")
print(f"  - Moved Phase 1 & 2 endpoints before main block")
print(f"  - Total lines: {len(new_content.splitlines())}")
