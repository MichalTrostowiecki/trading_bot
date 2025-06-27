# Git Commands Reference - Fibonacci Trading Bot Project

## Quick Reference Guide
This document provides a comprehensive reference of Git commands commonly used in the Fibonacci Trading Bot project development workflow.

## Daily Development Commands

### Repository Setup
```bash
# Clone repository
git clone git@github.com:MichalTrostowiecki/trading_bot.git
cd trading_bot

# Add upstream remote (for forks)
git remote add upstream git@github.com:MichalTrostowiecki/trading_bot.git

# Verify remotes
git remote -v
```

### Branch Management
```bash
# List all branches
git branch -a

# Create and switch to new branch
git checkout -b feature/new-feature-name

# Switch to existing branch
git checkout main
git checkout feature/existing-feature

# Update current branch with latest main
git fetch origin
git rebase origin/main

# Delete local branch
git branch -d feature/completed-feature

# Delete remote branch
git push origin --delete feature/completed-feature
```

### Staging and Committing
```bash
# Check status
git status

# Add files to staging
git add .                    # Add all files
git add src/core/fibonacci.py  # Add specific file
git add src/core/            # Add directory

# Commit with message
git commit -m "feat(fibonacci): implement retracement calculation"

# Amend last commit
git commit --amend -m "feat(fibonacci): implement retracement calculation with tests"

# Interactive staging
git add -p                   # Review each change before staging
```

### Pushing and Pulling
```bash
# Push current branch
git push origin feature/fibonacci-calculation

# Push and set upstream
git push -u origin feature/fibonacci-calculation

# Pull latest changes
git pull origin main

# Fetch without merging
git fetch origin
```

## Advanced Workflow Commands

### Rebasing and Merging
```bash
# Interactive rebase (clean up commits)
git rebase -i HEAD~3        # Rebase last 3 commits

# Rebase onto main
git rebase origin/main

# Abort rebase if conflicts are too complex
git rebase --abort

# Continue rebase after resolving conflicts
git add .
git rebase --continue

# Merge branch (from main)
git checkout main
git merge feature/fibonacci-calculation

# Squash merge
git merge --squash feature/fibonacci-calculation
```

### Conflict Resolution
```bash
# View conflicts
git status
git diff

# Use merge tool
git mergetool

# Mark conflicts as resolved
git add conflicted-file.py

# Continue merge/rebase
git rebase --continue
# or
git commit
```

### Stashing Changes
```bash
# Stash current changes
git stash

# Stash with message
git stash save "WIP: fibonacci calculation optimization"

# List stashes
git stash list

# Apply latest stash
git stash pop

# Apply specific stash
git stash apply stash@{1}

# Drop stash
git stash drop stash@{1}
```

## Release Management Commands

### Tagging
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Create lightweight tag
git tag v1.0.0

# List tags
git tag -l

# Push tags
git push origin v1.0.0
git push origin --tags

# Delete tag
git tag -d v1.0.0
git push origin --delete v1.0.0
```

### Release Workflow
```bash
# Create release branch
git checkout main
git pull origin main
git checkout -b release/v1.0.0

# Bump version and commit
# Edit version files
git add .
git commit -m "chore(release): bump version to v1.0.0"

# Push release branch
git push origin release/v1.0.0

# After PR merge, tag the release
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Debugging and History Commands

### Viewing History
```bash
# View commit history
git log --oneline
git log --graph --oneline --all

# View file history
git log --follow src/core/fibonacci.py

# View changes in commit
git show commit-hash

# View changes between commits
git diff commit1..commit2

# View changes in specific file
git diff HEAD~1 src/core/fibonacci.py
```

### Finding Issues
```bash
# Find when bug was introduced
git bisect start
git bisect bad HEAD
git bisect good v1.0.0

# Search for text in history
git log -S "fibonacci_calculation" --source --all

# Find who changed a line
git blame src/core/fibonacci.py

# Show file at specific commit
git show commit-hash:src/core/fibonacci.py
```

### Undoing Changes
```bash
# Undo unstaged changes
git checkout -- src/core/fibonacci.py

# Undo staged changes
git reset HEAD src/core/fibonacci.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert commit (create new commit)
git revert commit-hash
```

## Collaboration Commands

### Working with Remotes
```bash
# Add remote
git remote add upstream git@github.com:MichalTrostowiecki/trading_bot.git

# Fetch from all remotes
git fetch --all

# Push to specific remote
git push upstream main

# Set upstream branch
git branch --set-upstream-to=origin/main main
```

### Syncing Fork
```bash
# Sync fork with upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### Cherry-picking
```bash
# Apply specific commit to current branch
git cherry-pick commit-hash

# Cherry-pick without committing
git cherry-pick --no-commit commit-hash

# Cherry-pick range of commits
git cherry-pick commit1..commit2
```

## CI/CD Integration Commands

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Skip hooks for emergency commit
git commit --no-verify -m "emergency fix"
```

### GitHub CLI Integration
```bash
# Install GitHub CLI
# Windows: winget install GitHub.cli
# Mac: brew install gh

# Authenticate
gh auth login

# Create PR
gh pr create --title "feat(fibonacci): new calculation engine" \
             --body "Implements advanced Fibonacci calculations"

# List PRs
gh pr list

# Check PR status
gh pr status

# Merge PR
gh pr merge 123 --squash

# Create release
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes"
```

## Troubleshooting Commands

### Common Issues
```bash
# Fix "detached HEAD" state
git checkout main

# Recover deleted branch
git reflog
git checkout -b recovered-branch commit-hash

# Fix diverged branches
git fetch origin
git reset --hard origin/main

# Clean untracked files
git clean -fd

# Reset to specific commit
git reset --hard commit-hash

# Undo merge
git reset --hard HEAD~1
```

### Configuration Issues
```bash
# Check configuration
git config --list

# Set user info
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default editor
git config --global core.editor "code --wait"

# Set up GPG signing
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_GPG_KEY
```

## Performance and Maintenance

### Repository Maintenance
```bash
# Clean up repository
git gc --aggressive --prune=now

# Check repository integrity
git fsck

# Show repository size
git count-objects -vH

# Prune remote branches
git remote prune origin
```

### Large File Handling
```bash
# Track large files with Git LFS
git lfs track "*.csv"
git lfs track "data/historical/*"

# Add .gitattributes
git add .gitattributes

# Check LFS status
git lfs status

# Pull LFS files
git lfs pull
```

## Aliases for Common Commands

Add these to your `.gitconfig` for faster workflow:

```bash
# Set up useful aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'
git config --global alias.graph 'log --graph --oneline --all'
git config --global alias.pushf 'push --force-with-lease'
```

## Emergency Procedures

### Hotfix Workflow
```bash
# Create hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# Make fix and test
# ... make changes ...
pytest tests/ -v

# Commit and push
git add .
git commit -m "fix(critical): resolve position sizing bug"
git push origin hotfix/critical-bug-fix

# Create emergency PR
gh pr create --title "HOTFIX: Critical position sizing bug" \
             --body "Fixes critical bug affecting live trading" \
             --label "hotfix,critical"
```

### Rollback Procedures
```bash
# Rollback to previous release
git checkout main
git reset --hard v1.0.0
git push --force-with-lease origin main

# Create rollback tag
git tag -a v1.0.1-rollback -m "Rollback to v1.0.0"
git push origin v1.0.1-rollback
```

This reference guide provides all the essential Git commands needed for effective collaboration on the Fibonacci Trading Bot project.
