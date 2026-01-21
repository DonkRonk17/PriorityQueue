# PriorityQueue - Usage Examples

Quick navigation:
- [Example 1: Basic Task Management](#example-1-basic-task-management)
- [Example 2: Priority Scoring in Action](#example-2-priority-scoring-in-action)
- [Example 3: Dependency Chains](#example-3-dependency-chains)
- [Example 4: Agent Assignment](#example-4-agent-assignment)
- [Example 5: Sprint Planning Workflow](#example-5-sprint-planning-workflow)
- [Example 6: Emergency Priority Override](#example-6-emergency-priority-override)
- [Example 7: Daily Standup Queries](#example-7-daily-standup-queries)
- [Example 8: Search and Filter](#example-8-search-and-filter)
- [Example 9: Import/Export and Backup](#example-9-importexport-and-backup)
- [Example 10: Full Production Workflow](#example-10-full-production-workflow)

---

## Example 1: Basic Task Management

**Scenario:** First time using PriorityQueue to manage tasks.

### CLI Usage

```bash
# Step 1: Add your first task
python priorityqueue.py add "Set up development environment"

# Expected Output:
# [OK] Task created: a1b2c3d4
#      Title: Set up development environment
#      Priority: MEDIUM

# Step 2: Add more tasks with priorities
python priorityqueue.py add "Fix critical bug" --priority HIGH
python priorityqueue.py add "Write documentation" --priority LOW

# Step 3: List all tasks
python priorityqueue.py list

# Expected Output:
# Found 3 task(s):
#
# [PENDING] a1b2c3d4 [!] Set up development environment
# [PENDING] e5f6g7h8 [!!] Fix critical bug
# [PENDING] i9j0k1l2 [.] Write documentation

# Step 4: Get next task to work on
python priorityqueue.py next

# Expected Output:
# Next task:
#
# [PENDING] e5f6g7h8 [!!] Fix critical bug

# Step 5: Start the task
python priorityqueue.py start e5f6g7h8 --agent ATLAS

# Step 6: Complete when done
python priorityqueue.py complete e5f6g7h8 --notes "Fixed null pointer issue"
```

### Python API Usage

```python
from priorityqueue import PriorityQueue, TaskPriority

# Initialize
queue = PriorityQueue()

# Add tasks
task1 = queue.add("Set up development environment")
task2 = queue.add("Fix critical bug", priority=TaskPriority.HIGH)
task3 = queue.add("Write documentation", priority=TaskPriority.LOW)

# Get all pending
for task in queue.get_pending():
    print(f"{task.priority.name}: {task.title}")

# Output:
# HIGH: Fix critical bug
# MEDIUM: Set up development environment
# LOW: Write documentation

# Work on highest priority
next_task = queue.get_next()
print(f"Working on: {next_task.title}")  # Fix critical bug

queue.start(next_task.id, "ATLAS")
queue.complete(next_task.id, "Fixed!")
```

**What You Learned:**
- How to add tasks with different priorities
- How to list and query tasks
- How to work through the task lifecycle (add → start → complete)

---

## Example 2: Priority Scoring in Action

**Scenario:** Understanding how urgency affects priority ordering.

### Setup

```python
from priorityqueue import PriorityQueue, TaskPriority
from datetime import datetime, timedelta

queue = PriorityQueue()

# Clear any existing tasks for clean demo
# (In production, don't do this!)
```

### Adding Tasks with Deadlines

```python
now = datetime.now()

# Low priority but due in 30 minutes - URGENT!
urgent_low = queue.add(
    "Review PR (low priority but due soon)",
    priority=TaskPriority.LOW,
    deadline=(now + timedelta(minutes=30)).isoformat()
)

# Critical but due in a week
critical_later = queue.add(
    "Redesign architecture (critical but not urgent)",
    priority=TaskPriority.CRITICAL,
    deadline=(now + timedelta(days=7)).isoformat()
)

# High priority, overdue!
overdue_high = queue.add(
    "Deploy hotfix (OVERDUE)",
    priority=TaskPriority.HIGH,
    deadline=(now - timedelta(hours=2)).isoformat()
)

# Medium priority, no deadline
medium_normal = queue.add(
    "Update dependencies",
    priority=TaskPriority.MEDIUM
)
```

### Check Priority Order

```python
print("Tasks in priority order:")
for i, task in enumerate(queue.get_pending(), 1):
    score = task.calculate_score()
    print(f"{i}. {task.title}")
    print(f"   Priority: {task.priority.name}, Score: {score:.2f}")
    print()
```

**Expected Output:**
```
Tasks in priority order:
1. Deploy hotfix (OVERDUE)
   Priority: HIGH, Score: 0.20

2. Review PR (low priority but due soon)
   Priority: LOW, Score: 1.20

3. Redesign architecture (critical but not urgent)
   Priority: CRITICAL, Score: 0.90

4. Update dependencies
   Priority: MEDIUM, Score: 3.00
```

**What You Learned:**
- Overdue tasks jump to top regardless of base priority
- Deadline proximity boosts priority significantly
- Tasks without deadlines use base priority only

---

## Example 3: Dependency Chains

**Scenario:** Building a feature with sequential tasks.

### Creating Dependencies

```python
from priorityqueue import PriorityQueue, TaskPriority, TaskCategory

queue = PriorityQueue()

# Step 1: Create the root task (no dependencies)
design = queue.add(
    "Design user authentication system",
    priority=TaskPriority.HIGH,
    category=TaskCategory.RESEARCH,
    assigned_agent="FORGE"
)

# Step 2: Implementation depends on design
implement = queue.add(
    "Implement authentication",
    priority=TaskPriority.HIGH,
    category=TaskCategory.DEVELOPMENT,
    assigned_agent="ATLAS",
    dependencies=[design]  # Blocked until design completes
)

# Step 3: Tests depend on implementation
tests = queue.add(
    "Write authentication tests",
    priority=TaskPriority.HIGH,
    category=TaskCategory.TESTING,
    assigned_agent="NEXUS",
    dependencies=[implement]
)

# Step 4: Docs depend on tests
docs = queue.add(
    "Document authentication system",
    priority=TaskPriority.MEDIUM,
    category=TaskCategory.DOCUMENTATION,
    assigned_agent="CLIO",
    dependencies=[tests]
)

print("Created dependency chain: Design -> Implement -> Test -> Document")
```

### Check Task Statuses

```python
print("\nInitial Status:")
for task_id in [design, implement, tests, docs]:
    task = queue.get(task_id)
    print(f"  {task.title[:30]}: {task.status.name}")

# Output:
# Initial Status:
#   Design user authentication sys: PENDING
#   Implement authentication: BLOCKED
#   Write authentication tests: BLOCKED
#   Document authentication system: BLOCKED
```

### Work Through the Chain

```python
# Only design is available
next_task = queue.get_next("FORGE")
print(f"\nFORGE's next task: {next_task.title}")  # Design...

# Complete design
queue.start(design, "FORGE")
queue.complete(design, "Design document approved")

# Now implementation is unblocked
print("\nAfter completing design:")
for task_id in [design, implement, tests, docs]:
    task = queue.get(task_id)
    print(f"  {task.title[:30]}: {task.status.name}")

# Output:
#   Design user authentication sys: COMPLETED
#   Implement authentication: PENDING    <-- Unblocked!
#   Write authentication tests: BLOCKED
#   Document authentication system: BLOCKED
```

**What You Learned:**
- Tasks with unmet dependencies are automatically BLOCKED
- Completing a task automatically unblocks dependent tasks
- get_next() never returns blocked tasks

---

## Example 4: Agent Assignment

**Scenario:** Routing tasks to specific agents based on capabilities.

### Assigning Tasks to Agents

```python
from priorityqueue import PriorityQueue, TaskPriority

queue = PriorityQueue()

# Assign based on agent strengths
queue.add("Review pull request", assigned_agent="FORGE")      # Reviewer
queue.add("Implement feature", assigned_agent="ATLAS")         # Builder
queue.add("Deploy to server", assigned_agent="CLIO")          # Linux specialist
queue.add("Cross-platform test", assigned_agent="NEXUS")      # Multi-platform
queue.add("Simple bug fix", assigned_agent="BOLT")            # Free executor
queue.add("Mobile UI fix", assigned_agent="PORTER")           # Mobile specialist
queue.add("Any available agent can do this", assigned_agent="ANY")
```

### Get Tasks for Specific Agent

```python
# ATLAS gets only ATLAS or ANY tasks
atlas_task = queue.get_next("ATLAS")
print(f"ATLAS: {atlas_task.title}")

# FORGE gets only FORGE or ANY tasks
forge_task = queue.get_next("FORGE")
print(f"FORGE: {forge_task.title}")

# Get all tasks for an agent
atlas_workload = queue.get_agent_tasks("ATLAS")
print(f"\nATLAS has {len(atlas_workload)} tasks assigned")
```

### Check Agent Status

```python
# Mark ATLAS as busy
queue.start(atlas_task.id, "ATLAS")

# Check availability
status = queue.get_agent_status("ATLAS")
print(f"\nATLAS available: {status.available}")
print(f"Current task: {status.current_task}")

# List available agents
available = queue.get_available_agents()
print(f"Available agents: {[a.name for a in available]}")
```

**Expected Output:**
```
ATLAS: Implement feature
FORGE: Review pull request

ATLAS has 2 tasks assigned

ATLAS available: False
Current task: abc12345
Available agents: ['FORGE', 'CLIO', 'NEXUS', 'BOLT', 'PORTER']
```

**What You Learned:**
- Tasks can be assigned to specific agents
- "ANY" allows flexible routing
- Agent availability is tracked automatically

---

## Example 5: Sprint Planning Workflow

**Scenario:** Planning a 2-week sprint with Team Brain.

### CLI-Based Sprint Setup

```bash
# Set sprint deadline
SPRINT_END="2026-02-07T23:59:00"

# Add sprint tasks with deadlines
python priorityqueue.py add "User login feature" \
    --priority HIGH \
    --category FEATURE \
    --agent ATLAS \
    --deadline "$SPRINT_END" \
    --tags sprint5 auth

python priorityqueue.py add "Admin dashboard" \
    --priority MEDIUM \
    --category FEATURE \
    --agent BOLT \
    --deadline "$SPRINT_END" \
    --tags sprint5 admin

python priorityqueue.py add "API documentation" \
    --priority LOW \
    --category DOCUMENTATION \
    --agent CLIO \
    --deadline "$SPRINT_END" \
    --tags sprint5 docs

python priorityqueue.py add "Performance testing" \
    --priority MEDIUM \
    --category TESTING \
    --agent NEXUS \
    --deadline "$SPRINT_END" \
    --tags sprint5 testing
```

### View Sprint Status

```bash
# All sprint tasks
python priorityqueue.py search "sprint5"

# By status
python priorityqueue.py list --status PENDING
python priorityqueue.py list --status IN_PROGRESS
python priorityqueue.py list --status COMPLETED

# Statistics
python priorityqueue.py stats
```

**Example stats output:**
```
==================================================
PRIORITYQUEUE STATISTICS
==================================================

Total Tasks: 4
Completed Today: 0
Blocked: 0
Overdue: 0
Avg Completion Time: 0.0 min

By Status:
  PENDING: 4

By Priority:
  HIGH: 1
  MEDIUM: 2
  LOW: 1

By Agent:
  ATLAS: 1
  BOLT: 1
  CLIO: 1
  NEXUS: 1
==================================================
```

**What You Learned:**
- How to set up a sprint with deadlines and tags
- How to track sprint progress with searches and stats

---

## Example 6: Emergency Priority Override

**Scenario:** Production is down! Need to escalate immediately.

### Before Emergency

```python
from priorityqueue import PriorityQueue, TaskPriority
from datetime import datetime, timedelta

queue = PriorityQueue()

# Normal sprint work
queue.add("Implement feature X", priority=TaskPriority.HIGH)
queue.add("Write tests", priority=TaskPriority.MEDIUM)
queue.add("Update docs", priority=TaskPriority.LOW)

print("Normal order:")
for task in queue.get_pending()[:3]:
    print(f"  {task.priority.name}: {task.title}")
```

### Emergency Happens!

```python
# Production server down! 
emergency = queue.add(
    "EMERGENCY: Production server down - fix NOW!",
    priority=TaskPriority.CRITICAL,
    deadline=(datetime.now() + timedelta(minutes=30)).isoformat(),  # Due in 30 min
    assigned_agent="ANY",  # Anyone available
    tags=["emergency", "production"]
)

print("\nAfter emergency:")
for task in queue.get_pending()[:4]:
    print(f"  {task.priority.name}: {task.title[:50]}")
```

**Expected Output:**
```
Normal order:
  HIGH: Implement feature X
  MEDIUM: Write tests
  LOW: Update docs

After emergency:
  CRITICAL: EMERGENCY: Production server down - fix NOW
  HIGH: Implement feature X
  MEDIUM: Write tests
  LOW: Update docs
```

### Handle Emergency

```python
# Get the emergency (it's now #1)
emergency_task = queue.get_next()
print(f"\nDrop everything and fix: {emergency_task.title}")

# All hands on deck - any available agent
for agent in ["ATLAS", "CLIO", "BOLT"]:
    status = queue.get_agent_status(agent)
    if status.available:
        queue.start(emergency_task.id, agent)
        print(f"{agent} is handling the emergency!")
        break
```

**What You Learned:**
- CRITICAL + near deadline = highest priority
- Emergency tasks automatically bubble to top
- "ANY" assignment allows fast reassignment

---

## Example 7: Daily Standup Queries

**Scenario:** Running a daily standup to review team status.

### CLI Standup Script

```bash
#!/bin/bash
# standup.sh - Daily standup queries

echo "========================================"
echo "TEAM BRAIN DAILY STANDUP"
echo "========================================"
echo ""

echo ">> AGENT STATUS:"
python priorityqueue.py agents

echo ""
echo ">> IN PROGRESS:"
python priorityqueue.py list --status IN_PROGRESS

echo ""
echo ">> BLOCKED ITEMS:"
python priorityqueue.py list --status BLOCKED

echo ""
echo ">> COMPLETED YESTERDAY:"
python priorityqueue.py list --status COMPLETED --limit 5

echo ""
echo ">> QUEUE STATISTICS:"
python priorityqueue.py stats

echo ""
echo ">> NEXT PRIORITIES:"
for agent in FORGE ATLAS CLIO NEXUS BOLT PORTER; do
    echo ""
    echo "$agent's next task:"
    python priorityqueue.py next --agent $agent 2>/dev/null || echo "  No tasks available"
done
```

### Sample Output

```
========================================
TEAM BRAIN DAILY STANDUP
========================================

>> AGENT STATUS:
==================================================
TEAM BRAIN AGENT STATUS
==================================================

[AVAILABLE] FORGE
  Completed Today: 2
  Capabilities: COORDINATION, DOCUMENTATION, RESEARCH, REVIEW

[BUSY] ATLAS
  Current Task: abc12345
  Completed Today: 3
  Capabilities: DEVELOPMENT, TESTING, BUGFIX, FEATURE
...

>> IN PROGRESS:
Found 1 task(s):

[ACTIVE] abc12345 [!!] Implement user login @ATLAS

>> BLOCKED ITEMS:
Found 2 task(s):

[BLOCKED] def45678 [!] Write login tests
[BLOCKED] ghi78901 [.] Document login flow

>> QUEUE STATISTICS:
Total Tasks: 12
Completed Today: 5
Blocked: 2
...
```

**What You Learned:**
- How to create standup reports
- Quick visibility into team status and blockers

---

## Example 8: Search and Filter

**Scenario:** Finding specific tasks in a large queue.

### Search by Text

```bash
# Find all tasks mentioning "login"
python priorityqueue.py search "login"

# Find by tag
python priorityqueue.py search "security"
```

### Filter by Multiple Criteria

```python
from priorityqueue import PriorityQueue, TaskPriority, TaskStatus

queue = PriorityQueue()

# Get only HIGH priority, PENDING tasks for ATLAS
tasks = queue.get_queue(
    status=TaskStatus.PENDING,
    priority=TaskPriority.HIGH,
    agent="ATLAS",
    limit=10
)

for task in tasks:
    print(f"{task.id}: {task.title}")
```

### Advanced Filtering

```python
# Custom filter with Python
all_tasks = queue.get_queue(limit=100)

# Tasks with "security" tag
security_tasks = [t for t in all_tasks if "security" in t.tags]

# Overdue tasks
from datetime import datetime
overdue = [
    t for t in all_tasks
    if t.deadline and datetime.fromisoformat(t.deadline) < datetime.now()
    and t.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]
]

# Tasks created by specific person
logan_tasks = [t for t in all_tasks if t.created_by == "Logan"]
```

**What You Learned:**
- Text search across title, description, tags
- Built-in filters for common criteria
- Python filtering for complex queries

---

## Example 9: Import/Export and Backup

**Scenario:** Backing up queue data and restoring.

### Export Queue

```bash
# Export to file
python priorityqueue.py export --output backup_2026-01-21.json

# Export to stdout (for piping)
python priorityqueue.py export > queue_dump.json
```

### View Export Format

```json
{
  "exported_at": "2026-01-21T10:30:00",
  "version": "1.0.0",
  "tasks": {
    "abc123": {
      "id": "abc123",
      "title": "Implement feature",
      "status": "PENDING",
      "priority": 2,
      "dependencies": [],
      ...
    }
  },
  "agents": {
    "FORGE": {
      "name": "FORGE",
      "available": true,
      ...
    }
  },
  "stats": {
    "total_tasks": 10,
    ...
  }
}
```

### Import Queue

```bash
# Replace entire queue with import
python priorityqueue.py import backup_2026-01-21.json

# Merge with existing (add new, skip duplicates)
python priorityqueue.py import new_tasks.json --merge
```

### Python Backup Script

```python
from priorityqueue import PriorityQueue
from datetime import datetime
from pathlib import Path

queue = PriorityQueue()

# Daily backup
backup_dir = Path.home() / "backups" / "priorityqueue"
backup_dir.mkdir(parents=True, exist_ok=True)

backup_file = backup_dir / f"queue_{datetime.now().strftime('%Y%m%d')}.json"
queue.export_queue(backup_file)
print(f"Backed up to: {backup_file}")

# Keep only last 7 days
old_backups = sorted(backup_dir.glob("queue_*.json"))[:-7]
for old in old_backups:
    old.unlink()
    print(f"Deleted old backup: {old}")
```

**What You Learned:**
- Export for backups and migrations
- Import with merge option
- Automated backup strategies

---

## Example 10: Full Production Workflow

**Scenario:** Complete end-to-end workflow for a Team Brain session.

### Session Start

```python
from priorityqueue import PriorityQueue, TaskPriority, TaskCategory
from datetime import datetime, timedelta

# Initialize
queue = PriorityQueue()
agent_name = "ATLAS"

print("=" * 50)
print(f"SESSION START: {agent_name}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 50)

# Check for any in-progress tasks from last session
in_progress = queue.get_in_progress()
my_in_progress = [t for t in in_progress if t.assigned_agent == agent_name]

if my_in_progress:
    print(f"\n[!] Found {len(my_in_progress)} task(s) still in progress:")
    for task in my_in_progress:
        print(f"    {task.id}: {task.title}")
    print("    Review these before starting new work.\n")
```

### Check Assignments

```python
# Get queue status
stats = queue.get_stats()
print(f"\nQueue Status:")
print(f"  Total tasks: {stats['total_tasks']}")
print(f"  Pending: {stats['by_status'].get('PENDING', 0)}")
print(f"  Blocked: {stats['blocked_count']}")
print(f"  Overdue: {stats['overdue_count']}")

# Get my tasks
my_tasks = queue.get_agent_tasks(agent_name)
print(f"\n{agent_name}'s workload: {len(my_tasks)} tasks")

# Show blocked tasks I'm waiting on
blocked = [t for t in my_tasks if t.status.name == "BLOCKED"]
if blocked:
    print(f"\n[!] {len(blocked)} blocked tasks:")
    for task in blocked:
        deps = ", ".join(task.dependencies[:3])
        print(f"    {task.title[:40]} - waiting on: {deps}")
```

### Work on Next Task

```python
# Get highest priority available task
task = queue.get_next(agent_name)

if not task:
    print("\nNo tasks available. Check with FORGE for new assignments.")
else:
    print(f"\n{'=' * 50}")
    print(f"NEXT TASK: {task.title}")
    print(f"{'=' * 50}")
    print(f"ID: {task.id}")
    print(f"Priority: {task.priority.name}")
    print(f"Category: {task.category.name}")
    if task.deadline:
        deadline = datetime.fromisoformat(task.deadline)
        remaining = deadline - datetime.now()
        print(f"Deadline: {deadline.strftime('%Y-%m-%d %H:%M')} ({remaining.days}d {remaining.seconds//3600}h remaining)")
    if task.description:
        print(f"Description: {task.description}")
    if task.dependencies:
        print(f"Note: Originally had dependencies (now complete)")
    
    # Start working
    print("\nStarting task...")
    queue.start(task.id, agent_name)
    print("[OK] Task started. Status: IN_PROGRESS")
```

### Do the Work...

```python
# ... actual work happens here ...
# Simulate work completion
work_result = "Implemented the feature successfully"
work_notes = "Added 3 new files, 200 lines of code. All tests passing."
```

### Complete Task

```python
# Complete the task
queue.complete(task.id, notes=work_notes)

# Get updated task info
completed_task = queue.get(task.id)
print(f"\n{'=' * 50}")
print("TASK COMPLETED")
print(f"{'=' * 50}")
print(f"Task: {completed_task.title}")
print(f"Duration: {completed_task.actual_duration} minutes")
print(f"Notes: {completed_task.notes}")

# Check if this unblocked anything
# (The queue auto-updates blocked tasks)
newly_pending = queue.get_pending(limit=5)
print(f"\nNext tasks available: {len(newly_pending)}")
```

### Session End Summary

```python
print(f"\n{'=' * 50}")
print(f"SESSION END: {agent_name}")
print(f"{'=' * 50}")

# Get updated stats
stats = queue.get_stats()
agent_status = queue.get_agent_status(agent_name)

print(f"\nSession Summary:")
print(f"  Tasks completed today: {agent_status.completed_today}")
print(f"  Avg completion time: {stats['avg_completion_minutes']:.1f} min")
print(f"  Remaining in queue: {stats['by_status'].get('PENDING', 0)}")
print(f"  Blocked: {stats['blocked_count']}")

# Mark agent as available
queue.set_agent_available(agent_name, True)
print(f"\n{agent_name} marked as available for next session.")
print("=" * 50)
```

**Expected Full Session Output:**
```
==================================================
SESSION START: ATLAS
Time: 2026-01-21 10:30
==================================================

Queue Status:
  Total tasks: 15
  Pending: 8
  Blocked: 3
  Overdue: 1

ATLAS's workload: 5 tasks

[!] 2 blocked tasks:
    Write integration tests - waiting on: abc123
    Deploy feature - waiting on: def456, ghi789

==================================================
NEXT TASK: Implement user authentication
==================================================
ID: xyz890
Priority: HIGH
Category: DEVELOPMENT
Deadline: 2026-01-23 17:00 (2d 6h remaining)
Description: Add login/logout with JWT tokens

Starting task...
[OK] Task started. Status: IN_PROGRESS

... work happens ...

==================================================
TASK COMPLETED
==================================================
Task: Implement user authentication
Duration: 45 minutes
Notes: Added 3 new files, 200 lines of code. All tests passing.

Next tasks available: 4

==================================================
SESSION END: ATLAS
==================================================

Session Summary:
  Tasks completed today: 3
  Avg completion time: 38.2 min
  Remaining in queue: 7
  Blocked: 2

ATLAS marked as available for next session.
==================================================
```

**What You Learned:**
- Complete session workflow from start to finish
- Handling in-progress tasks from previous sessions
- Checking blocked tasks and dependencies
- Session summary and statistics

---

## Quick Reference

| Action | CLI | Python |
|--------|-----|--------|
| Add task | `priorityqueue add "title"` | `queue.add("title")` |
| List tasks | `priorityqueue list` | `queue.get_pending()` |
| Get next | `priorityqueue next` | `queue.get_next()` |
| Start task | `priorityqueue start ID` | `queue.start(id)` |
| Complete | `priorityqueue complete ID` | `queue.complete(id)` |
| Search | `priorityqueue search "query"` | `queue.search("query")` |
| Stats | `priorityqueue stats` | `queue.get_stats()` |
| Export | `priorityqueue export -o file.json` | `queue.export_queue(path)` |

---

**More examples and integration patterns:** [INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)
