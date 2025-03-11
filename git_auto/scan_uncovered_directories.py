import os
import re
import argparse
from pathlib import Path

def parse_codeowners(codeowners_path):
    """Parse existing CODEOWNERS file and extract directory patterns."""
    patterns = []
    
    with open(codeowners_path, 'r') as f:
        codeowners_content = f.read()
    
    # Skip comment lines and empty lines
    for line in codeowners_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Extract the pattern (directory path)
        parts = line.split()
        if parts:
            pattern = parts[0]
            # Convert glob patterns to regex patterns
            # Replace * with .* for regex
            pattern = pattern.replace('*', '.*')
            # Escape dots for regex
            pattern = pattern.replace('.', '\\.')
            # Ensure the pattern matches the full path
            if not pattern.startswith('^'):
                pattern = '^' + pattern
            if not pattern.endswith('$'):
                pattern = pattern + '$'
            
            patterns.append(pattern)
    
    return patterns

def find_uncovered_directories(repo_path, patterns, min_depth=1, max_depth=None, exclude_dirs=None):
    """Find directories in the repo that don't match any pattern in CODEOWNERS."""
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.github', 'node_modules', '__pycache__']
    
    uncovered = []
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Get relative path from repo root
        rel_path = os.path.relpath(root, repo_path)
        if rel_path == '.':
            continue
        
        # Check directory depth
        depth = len(rel_path.split(os.sep))
        if depth < min_depth:
            continue
        if max_depth and depth > max_depth:
            continue
        
        # Normalize path format to match CODEOWNERS
        norm_path = '/' + rel_path.replace('\\', '/')
        
        # Check if this directory is covered by any pattern
        covered = False
        for pattern in patterns:
            if re.match(pattern, norm_path):
                covered = True
                break
        
        if not covered:
            uncovered.append(norm_path)
    
    return uncovered

# Create a script that can be used directly with your existing CODEOWNERS file
with open('scan_uncovered_directories.py', 'w') as f:
    f.write('''
import os
import re
import argparse
from pathlib import Path

def parse_codeowners(codeowners_path):
    """Parse CODEOWNERS file and extract directory patterns."""
    patterns = []
    
    with open(codeowners_path, 'r') as f:
        codeowners_content = f.read()
    
    # Skip comment lines and empty lines
    for line in codeowners_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Extract the pattern (directory path)
        parts = line.split()
        if parts:
            pattern = parts[0]
            # Convert glob patterns to regex patterns
            # Replace * with .* for regex
            pattern = pattern.replace('*', '.*')
            # Escape dots for regex
            pattern = pattern.replace('.', '\\\\.')
            # Ensure the pattern matches the full path
            if not pattern.startswith('^'):
                pattern = '^' + pattern
            if not pattern.endswith('$'):
                pattern = pattern + '$'
            
            patterns.append(pattern)
    
    return patterns

def find_uncovered_directories(repo_path, patterns, min_depth=1, max_depth=None, exclude_dirs=None):
    """Find directories in the repo that don't match any pattern in CODEOWNERS."""
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.github', 'node_modules', '__pycache__']
    
    uncovered = []
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Get relative path from repo root
        rel_path = os.path.relpath(root, repo_path)
        if rel_path == '.':
            continue
        
        # Check directory depth
        depth = len(rel_path.split(os.sep))
        if depth < min_depth:
            continue
        if max_depth and depth > max_depth:
            continue
        
        # Normalize path format to match CODEOWNERS
        norm_path = '/' + rel_path.replace('\\\\', '/')
        
        # Check if this directory is covered by any pattern
        covered = False
        for pattern in patterns:
            if re.match(pattern, norm_path):
                covered = True
                break
        
        if not covered:
            uncovered.append(norm_path)
    
    return uncovered

def main():
    parser = argparse.ArgumentParser(description='Find directories not covered by CODEOWNERS')
    parser.add_argument('repo_path', help='Path to the repository')
    parser.add_argument('--codeowners', default='.github/CODEOWNERS', 
                        help='Path to CODEOWNERS file relative to repo_path')
    parser.add_argument('--min-depth', type=int, default=1, 
                        help='Minimum directory depth to check')
    parser.add_argument('--max-depth', type=int, default=None, 
                        help='Maximum directory depth to check')
    parser.add_argument('--exclude', nargs='+', default=['.git', '.github', 'node_modules', '__pycache__'],
                        help='Directories to exclude from checking')
    parser.add_argument('--output', help='Output file to write results')
    parser.add_argument('--format', choices=['plain', 'codeowners'], default='plain',
                        help='Output format: plain text or CODEOWNERS format')
    parser.add_argument('--default-owner', default='@coupang/terraform-reviewers',
                        help='Default owner to use for CODEOWNERS format')
    
    args = parser.parse_args()
    
    codeowners_path = os.path.join(args.repo_path, args.codeowners)
    if not os.path.exists(codeowners_path):
        print(f"Error: CODEOWNERS file not found at {codeowners_path}")
        return 1
    
    patterns = parse_codeowners(codeowners_path)
    uncovered = find_uncovered_directories(
        args.repo_path, 
        patterns, 
        min_depth=args.min_depth, 
        max_depth=args.max_depth, 
        exclude_dirs=args.exclude
    )
    
    # Sort directories alphabetically
    uncovered.sort()
    
    if args.output:
        with open(args.output, 'w') as f:
            if args.format == 'plain':
                for dir_path in uncovered:
                    f.write(f"{dir_path}\\n")
            else:  # codeowners format
                for dir_path in uncovered:
                    # Format according to CODEOWNERS style
                    if len(dir_path) < 50:
                        padding = ' ' * (50 - len(dir_path))
                        f.write(f"{dir_path}{padding}{args.default_owner}\\n")
                    else:
                        f.write(f"{dir_path} {args.default_owner}\\n")
        print(f"Results written to {args.output}")
    else:
        print("Directories not covered by CODEOWNERS:")
        for dir_path in uncovered:
            print(dir_path)
    
    print(f"\\nTotal uncovered directories: {len(uncovered)}")
    return 0

if __name__ == '__main__':
    exit(main())
''')

print("Created script: scan_uncovered_directories.py")
print("\nUsage examples:")
print("1. Basic usage:")
print("   python scan_uncovered_directories.py /path/to/your/repo")
print("\n2. Specify CODEOWNERS location:")
print("   python scan_uncovered_directories.py /path/to/your/repo --codeowners CODEOWNERS")
print("\n3. Generate CODEOWNERS-formatted output:")
print("   python scan_uncovered_directories.py /path/to/your/repo --format codeowners --output missing_owners.txt")
print("\n4. Exclude certain directories:")
print("   python scan_uncovered_directories.py /path/to/your/repo --exclude .terraform node_modules")
print("\n5. Set depth limits (e.g., only check directories 2-4 levels deep):")
print("   python scan_uncovered_directories.py /path/to/your/repo --min-depth 2 --max-depth 4")
