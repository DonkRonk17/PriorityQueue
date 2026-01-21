# PriorityQueue - Quick Start Guides

## 📖 ABOUT THESE GUIDES

Each Team Brain agent has a **5-minute quick-start guide** tailored to their role and workflows.

**Choose your guide:**
- [Forge (Orchestrator)](#-forge-quick-start)
- [Atlas (Executor)](#-atlas-quick-start)
- [Clio (Linux Agent)](#-clio-quick-start)
- [Nexus (Multi-Platform)](#-nexus-quick-start)
- [Bolt (Free Executor)](#-bolt-quick-start)
- [Porter (Mobile Specialist)](#-porter-quick-start)

---

## 🔥 FORGE QUICK START

**Role:** Orchestrator / Reviewer  
**Time:** 5 minutes  
**Goal:** Learn to manage the task queue and assign work to agents

### Step 1: Installation Check
```bash
# Verify PriorityQueue is available
python priorityqueue.py --version

# Expected: PriorityQueue v1.0.0
```

### Step 2: View Queue Status
```bash
# Get overall statistics
python priorityqueue.py stats

# See what's pending
python priorityqueue.py list --status PENDING

# Check blocked tasks
python priorityqueue.py list --status BLOCKED
```

### Step 3: Create and Assign Tasks
```python
from priorityqueue import PriorityQueue, TaskPriority, TaskCategory

queue = PriorityQueue()

# Create high-priority task for ATLAS
task_id = queue.add(
    "Implement user authentication",
    priority=TaskPriority.HIGH,
    category=TaskCategory.FEATURE,
    assigned_agent="ATLAS",
    deadline="2026-01-30T17:00:00"
)

print(f"Created task: {task_id}")
```

**CLI equivalent:**
```bash
python priorityqueue.py add "Implement user authentication" \
    --priority HIGH \
    --category FEATURE \
    --agent ATLAS \
    --deadline "2026-01-30T17:00:00"
```

### Step 4: Create Dependency Chains
```python
# Design → Implement → Test → Document
design = queue.add("Design API", priority=TaskPriority.HIGH, assigned_agent="FORGE")
implement = queue.add("Implement API", dependencies=[design], assigned_agent="ATLAS")
test = queue.add("Test API", dependencies=[implement], assigned_agent="NEXUS")
docs = queue.add("Document API", dependencies=[test], assigned_agent="CLIO")

print("Created 4-step dependency chain")
```

### Step 5: Review Agent Workloads
```bash
# See all agent status
python priorityqueue.py agents

# Check specific agent's tasks
python priorityqueue.py list --agent ATLAS
```

### Common Forge Commands
```bash
# Morning check
priorityqueue stats
priorityqueue list --status BLOCKED

# Assign urgent task
priorityqueue add "URGENT: Fix bug" -p CRITICAL -a ANY

# Review completed
priorityqueue list --status COMPLETED --limit 10

# Search for specific tasks
priorityqueue search "authentication"
```

### Next Steps for Forge
1. Read [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) - Full orchestration patterns
2. Review [EXAMPLES.md](EXAMPLES.md) - Example 5 (Sprint Planning)
3. Set up daily queue review routine
4. Create task templates for common work types

---

## ⚡ ATLAS QUICK START

**Role:** Executor / Builder  
**Time:** 5 minutes  
**Goal:** Learn to receive, work on, and complete assigned tasks

### Step 1: Installation Check
```bash
python -c "from priorityqueue import PriorityQueue; print('OK')"
# Expected: OK
```

### Step 2: Get Your Next Task
```python
from priorityqueue import PriorityQueue

queue = PriorityQueue()

# Get highest priority task for ATLAS
task = queue.get_next("ATLAS")
if task:
    print(f"Next: {task.title}")
    print(f"Priority: {task.priority.name}")
    print(f"ID: {task.id}")
else:
    print("No tasks available")
```

**CLI equivalent:**
```bash
python priorityqueue.py next --agent ATLAS --verbose
```

### Step 3: Start Working
```python
# Start the task
queue.start(task.id, "ATLAS")
print(f"Started: {task.title}")
```

**CLI:**
```bash
python priorityqueue.py start abc123 --agent ATLAS
```

### Step 4: Complete When Done
```python
# Complete with notes
queue.complete(task.id, notes="Implemented and tested. All tests passing.")
print("Task completed!")

# Check next task
next_task = queue.get_next("ATLAS")
if next_task:
    print(f"Next up: {next_task.title}")
```

**CLI:**
```bash
python priorityqueue.py complete abc123 --notes "Implemented and tested"
```

### Step 5: Handle Issues
```python
# If task fails
queue.fail(task.id, reason="External API unavailable")

# If requirements change
queue.cancel(task.id, reason="Feature cancelled by Logan")
```

### Common Atlas Commands
```bash
# Session start
priorityqueue next --agent ATLAS

# Start task
priorityqueue start abc123 --agent ATLAS

# View my tasks
priorityqueue list --agent ATLAS

# Complete
priorityqueue complete abc123 --notes "Done!"

# Mark failed
priorityqueue fail abc123 --reason "Bug in dependency"
```

### Next Steps for Atlas
1. Add to session start routine: `queue.get_next("ATLAS")`
2. Always complete tasks with meaningful notes
3. Use [EXAMPLES.md](EXAMPLES.md) - Example 10 (Full Production Workflow)

---

## 🐧 CLIO QUICK START

**Role:** Linux / Ubuntu Agent  
**Time:** 5 minutes  
**Goal:** Learn CLI-based task management for Linux workflows

### Step 1: Installation
```bash
# Clone to home directory
git clone https://github.com/DonkRonk17/PriorityQueue.git ~/PriorityQueue
cd ~/PriorityQueue

# Verify
python3 priorityqueue.py --version

# Create alias (add to ~/.bashrc)
echo 'alias pq="python3 ~/PriorityQueue/priorityqueue.py"' >> ~/.bashrc
source ~/.bashrc
```

### Step 2: Get Your Tasks
```bash
# Get next task
pq next --agent CLIO

# List all your tasks
pq list --agent CLIO
```

### Step 3: Standard Workflow
```bash
# Get next task
pq next --agent CLIO

# Example output:
# Next task:
# [PENDING] abc123 [!] Deploy to production @CLIO

# Start working
pq start abc123 --agent CLIO

# After deployment...
pq complete abc123 --notes "Deployed to prod server, all services healthy"
```

### Step 4: Deployment Task Pattern
```bash
#!/bin/bash
# deploy_task.sh - Wrapper for deployment tasks

TASK_ID=$1

if [ -z "$TASK_ID" ]; then
    echo "Getting next task..."
    TASK_ID=$(pq next --agent CLIO 2>/dev/null | grep -oP '\[PENDING\] \K\w+')
fi

if [ -z "$TASK_ID" ]; then
    echo "No tasks available"
    exit 0
fi

echo "Starting task: $TASK_ID"
pq start $TASK_ID --agent CLIO

# Do deployment...
# Your deployment commands here

if [ $? -eq 0 ]; then
    pq complete $TASK_ID --notes "Deployment successful"
else
    pq fail $TASK_ID --reason "Deployment failed"
fi
```

### Common Clio Commands
```bash
pq next --agent CLIO           # Get next task
pq start ID --agent CLIO       # Start task
pq complete ID --notes "Done"  # Complete
pq list --status BLOCKED       # Check blockers
pq history --limit 20          # View history
```

### Platform-Specific Tips
- Use shell aliases for faster access
- Data stored in `~/.priorityqueue/`
- Works with cron for automated checks

### Next Steps for Clio
1. Add `pq` alias to bashrc
2. Create deployment wrapper scripts
3. Set up cron for queue monitoring

---

## 🌐 NEXUS QUICK START

**Role:** Multi-Platform Agent  
**Time:** 5 minutes  
**Goal:** Learn cross-platform task handling

### Step 1: Platform Detection
```python
import platform
from priorityqueue import PriorityQueue

queue = PriorityQueue()
print(f"Running on: {platform.system()} {platform.release()}")
```

### Step 2: Get and Execute Tasks
```python
from priorityqueue import PriorityQueue

queue = PriorityQueue()

# Get task
task = queue.get_next("NEXUS")
if task:
    print(f"Task: {task.title}")
    queue.start(task.id, "NEXUS")
    
    # Do platform-specific work...
    import platform
    result = f"Tested on {platform.system()}"
    
    queue.complete(task.id, notes=result)
```

### Step 3: Multi-Platform Testing Pattern
```python
import platform
from priorityqueue import PriorityQueue

queue = PriorityQueue()

def run_platform_test(task_id):
    """Run test and report platform results."""
    task = queue.get(task_id)
    queue.start(task_id, "NEXUS")
    
    # Platform info
    sys_info = {
        "os": platform.system(),
        "release": platform.release(),
        "python": platform.python_version()
    }
    
    # Run tests...
    test_result = "PASS"  # or "FAIL"
    
    notes = f"Platform: {sys_info['os']} {sys_info['release']}\n"
    notes += f"Python: {sys_info['python']}\n"
    notes += f"Result: {test_result}"
    
    queue.complete(task_id, notes=notes)
```

### Common Nexus Commands
```bash
# Works on Windows, Linux, macOS
python priorityqueue.py next --agent NEXUS
python priorityqueue.py list --category TESTING
python priorityqueue.py search "cross-platform"
```

### Platform Considerations
- **Windows:** Use `python` or `py`
- **Linux/macOS:** Use `python3`
- Data syncs via `~/.priorityqueue/` (cross-platform path)

### Next Steps for Nexus
1. Test tool on all platforms
2. Create platform-specific test reports
3. Use for research and multi-environment tasks

---

## 🆓 BOLT QUICK START

**Role:** Free Executor (Cline + Grok)  
**Time:** 5 minutes  
**Goal:** Learn to receive and complete simple tasks cost-free

### Step 1: Verify Access
```bash
# No API key required!
python priorityqueue.py --version
```

### Step 2: Get Simple Tasks
```bash
# Get next task assigned to BOLT
python priorityqueue.py next --agent BOLT

# Or tasks available to any agent
python priorityqueue.py next --agent ANY
```

### Step 3: Execute Tasks
```bash
# Start task
python priorityqueue.py start abc123 --agent BOLT

# Do the work (simple tasks only!)...

# Complete
python priorityqueue.py complete abc123 --notes "Done"
```

### Step 4: Best Practices for BOLT
```
GOOD for BOLT:
✓ Simple bug fixes
✓ File operations (rename, move, copy)
✓ Formatting/linting code
✓ Running scripts
✓ Basic documentation updates

NOT for BOLT:
✗ Complex architectural decisions
✗ Multi-file refactoring
✗ Ambiguous requirements
✗ Critical security code
```

### Common Bolt Commands
```bash
pq next --agent BOLT                        # Get task
pq start ID --agent BOLT                    # Start
pq complete ID --notes "Simple fix done"    # Complete
pq list --priority LOW --priority MEDIUM    # View simple tasks
```

### Cost Savings
- BOLT is FREE (Cline + Grok)
- Handles simple tasks that don't need expensive API calls
- Helps Logan stay under $60/month budget

### Next Steps for Bolt
1. Focus on well-defined, simple tasks
2. Report unclear requirements to FORGE
3. Complete tasks quickly to maximize throughput

---

## 📱 PORTER QUICK START

**Role:** Mobile Development Specialist  
**Time:** 5 minutes  
**Goal:** Learn to manage mobile development tasks

### Step 1: Installation
```bash
# Clone to Android Studio projects area
git clone https://github.com/DonkRonk17/PriorityQueue.git
cd PriorityQueue
python priorityqueue.py --version
```

### Step 2: Get Mobile Tasks
```python
from priorityqueue import PriorityQueue

queue = PriorityQueue()

# Get next mobile task
task = queue.get_next("PORTER")
if task:
    print(f"Mobile Task: {task.title}")
    print(f"Tags: {task.tags}")  # Look for 'mobile', 'android', 'ios'
```

**CLI:**
```bash
python priorityqueue.py next --agent PORTER
python priorityqueue.py search "mobile"
```

### Step 3: Mobile Development Workflow
```python
# Start mobile task
task = queue.get_next("PORTER")
queue.start(task.id, "PORTER")

# After implementing feature...
notes = """
- Added push notification support
- Tested on Android 13 emulator
- iOS build pending
"""
queue.complete(task.id, notes=notes)
```

### Step 4: Tag-Based Filtering
```bash
# Search for Android tasks
python priorityqueue.py search "android"

# Search for iOS tasks
python priorityqueue.py search "ios"

# Search for BCH Mobile tasks
python priorityqueue.py search "bch mobile"
```

### Common Porter Commands
```bash
pq next --agent PORTER             # Get mobile task
pq search "mobile"                 # Find mobile tasks
pq list --category FEATURE         # Feature tasks
pq start ID --agent PORTER         # Start
pq complete ID --notes "Tested on Android/iOS"
```

### Mobile-Specific Tips
- Use tags: `mobile`, `android`, `ios`, `bch-mobile`
- Note platform tested in completion notes
- Track build numbers in metadata

### Next Steps for Porter
1. Add mobile-specific tags to tasks
2. Document platform compatibility in notes
3. Focus on BCH Mobile polishing tasks

---

## 📚 ADDITIONAL RESOURCES

**For All Agents:**
- Full Documentation: [README.md](README.md)
- 10 Working Examples: [EXAMPLES.md](EXAMPLES.md)
- Integration Guide: [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)
- Integration Patterns: [INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)
- Quick Reference: [CHEAT_SHEET.txt](CHEAT_SHEET.txt)

**Support:**
- GitHub Issues: https://github.com/DonkRonk17/PriorityQueue/issues
- Synapse: Post in THE_SYNAPSE/active/
- Direct: Message FORGE for complex issues

---

**Last Updated:** January 21, 2026  
**Maintained By:** Forge (Team Brain)
