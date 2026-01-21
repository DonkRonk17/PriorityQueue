# PriorityQueue - Integration Plan

## 🎯 INTEGRATION GOALS

This document outlines how PriorityQueue integrates with:
1. Team Brain agents (Forge, Atlas, Clio, Nexus, Bolt, Porter)
2. Existing Team Brain tools
3. BCH (Beacon Command Hub) - future integration
4. Logan's daily workflows

---

## 📦 BCH INTEGRATION

### Overview

**Current Status:** Not yet integrated with BCH  
**Planned Phase:** BCH Phase 3 (Advanced Features)  
**Priority:** Medium

### Planned BCH Features

1. **Visual Queue Dashboard**
   - Real-time task queue view
   - Drag-and-drop priority adjustment
   - Status indicators with color coding
   - Agent workload distribution chart

2. **BCH Commands**
   ```
   @priority list              # Show task queue
   @priority next ATLAS        # Get next task for agent
   @priority add "title"       # Add new task
   @priority complete abc123   # Complete task
   ```

3. **Integration Points**
   - Auto-create tasks from BCH messages
   - Task notifications via BCH
   - Agent status sync with BCH dashboard

### Implementation Steps

1. Create BCH plugin/module for PriorityQueue
2. Add WebSocket endpoint for real-time updates
3. Build React components for queue visualization
4. Integrate with existing BCH notification system
5. Add authentication and access control

---

## 🤖 AI AGENT INTEGRATION

### Integration Matrix

| Agent | Primary Use Case | Integration Method | Priority |
|-------|------------------|-------------------|----------|
| **FORGE** | Orchestration, task assignment, review | Python API + CLI | **HIGH** |
| **ATLAS** | Task execution, builds, implementation | Python API | **HIGH** |
| **CLIO** | Linux operations, deployments | CLI | **HIGH** |
| **NEXUS** | Multi-platform testing, research | Python API | **MEDIUM** |
| **BOLT** | Free execution, simple tasks | CLI | **MEDIUM** |
| **PORTER** | Mobile development tasks | Python API | **MEDIUM** |

### Agent-Specific Workflows

---

#### FORGE (Orchestrator / Reviewer)

**Primary Use Case:** Task assignment, priority management, workflow orchestration

**Role in Queue:**
- Creates and prioritizes tasks
- Assigns tasks to appropriate agents
- Reviews completed work
- Monitors queue health

**Integration Steps:**
1. Start session by checking queue status
2. Review blocked tasks and dependencies
3. Create new tasks as needed
4. Assign/reassign based on agent availability
5. Review completed tasks

**Example Workflow:**
```python
from priorityqueue import PriorityQueue, TaskPriority, TaskCategory

queue = PriorityQueue()

# Daily orchestration routine
def forge_daily_routine():
    # Check queue health
    stats = queue.get_stats()
    print(f"Queue Status: {stats['total_tasks']} tasks")
    print(f"  Blocked: {stats['blocked_count']}")
    print(f"  Overdue: {stats['overdue_count']}")
    
    # Review blocked tasks
    blocked = queue.get_blocked()
    for task in blocked:
        print(f"BLOCKED: {task.title}")
        print(f"  Waiting on: {task.dependencies}")
    
    # Create tasks from planning
    task_id = queue.add(
        "Implement new feature",
        priority=TaskPriority.HIGH,
        category=TaskCategory.FEATURE,
        assigned_agent="ATLAS",
        deadline="2026-01-30T17:00:00"
    )
    
    # Review completed work
    completed = queue.get_completed(limit=10)
    for task in completed:
        print(f"COMPLETED: {task.title} by {task.assigned_agent}")
```

**CLI Quick Commands:**
```bash
# Morning check
priorityqueue stats
priorityqueue list --status BLOCKED
priorityqueue list --status PENDING --priority HIGH

# Assign task
priorityqueue add "New feature" -p HIGH -a ATLAS

# Review
priorityqueue list --status COMPLETED --limit 10
```

---

#### ATLAS (Executor / Builder)

**Primary Use Case:** Execute assigned tasks, implement features, fix bugs

**Role in Queue:**
- Receives task assignments
- Updates task status
- Reports completion/issues

**Integration Steps:**
1. Check for assigned tasks at session start
2. Get next highest priority task
3. Start task (status → IN_PROGRESS)
4. Complete work
5. Mark complete with notes

**Example Workflow:**
```python
from priorityqueue import PriorityQueue, TaskPriority

queue = PriorityQueue()
agent = "ATLAS"

# Session start
def atlas_session_start():
    # Check for in-progress tasks
    in_progress = queue.get_in_progress()
    my_tasks = [t for t in in_progress if t.assigned_agent == agent]
    
    if my_tasks:
        print(f"Resuming: {my_tasks[0].title}")
        return my_tasks[0]
    
    # Get next task
    task = queue.get_next(agent)
    if task:
        print(f"Starting: {task.title}")
        queue.start(task.id, agent)
        return task
    
    print("No tasks available")
    return None

# Complete task
def atlas_complete_task(task_id, notes):
    queue.complete(task_id, notes=notes)
    print(f"[OK] Task completed")
    
    # Check what's next
    next_task = queue.get_next(agent)
    if next_task:
        print(f"Next up: {next_task.title}")
```

**CLI Quick Commands:**
```bash
# Session start
priorityqueue next --agent ATLAS

# Start task
priorityqueue start abc123 --agent ATLAS

# Complete
priorityqueue complete abc123 --notes "Implemented and tested"

# Check workload
priorityqueue list --agent ATLAS
```

---

#### CLIO (Linux / Ubuntu Agent)

**Primary Use Case:** Linux operations, deployments, system administration

**Platform Considerations:**
- CLI-first workflow
- Runs on Linux/Ubuntu/WSL
- Often handles deployments and server tasks

**Integration Steps:**
1. Clone repo to Linux environment
2. Add to PATH or create alias
3. Use CLI for all operations

**Example Workflow:**
```bash
# Add to bashrc
alias pq='python /path/to/priorityqueue.py'

# Daily workflow
pq next --agent CLIO

# Start task
pq start abc123 --agent CLIO

# After deployment
pq complete abc123 --notes "Deployed to production server"

# Check blocked
pq list --status BLOCKED
```

**Automation Example:**
```bash
#!/bin/bash
# clio_task_runner.sh

AGENT="CLIO"

# Get next task
TASK=$(pq next --agent $AGENT | grep -oP '\[\w+\] \K\w+')

if [ -n "$TASK" ]; then
    echo "Starting task: $TASK"
    pq start $TASK --agent $AGENT
    
    # Do work...
    
    pq complete $TASK --notes "Automated completion"
else
    echo "No tasks available"
fi
```

---

#### NEXUS (Multi-Platform Agent)

**Primary Use Case:** Cross-platform testing, research, multi-environment work

**Platform Considerations:**
- Works on Windows, Linux, macOS
- Often handles research and testing tasks
- May need to test tools on multiple platforms

**Integration Steps:**
1. Install on each platform
2. Sync queue data if needed
3. Report platform-specific results

**Example Workflow:**
```python
from priorityqueue import PriorityQueue, TaskCategory
import platform

queue = PriorityQueue()
agent = "NEXUS"

# Platform-aware task handling
task = queue.get_next(agent)
if task:
    queue.start(task.id, agent)
    
    # Do platform-specific work
    result = f"Tested on {platform.system()} {platform.release()}"
    
    queue.complete(task.id, notes=result)
```

**CLI Commands:**
```bash
# Testing workflow
priorityqueue next --agent NEXUS
priorityqueue start abc123 --agent NEXUS

# Research task
priorityqueue add "Research new library" \
    --category RESEARCH \
    --agent NEXUS \
    --priority MEDIUM
```

---

#### BOLT (Free Executor)

**Primary Use Case:** Simple tasks, repetitive work, cost-free execution

**Considerations:**
- Free agent (Cline + Grok)
- Best for simple, well-defined tasks
- Helps save API costs

**Integration Steps:**
1. Receive tasks from TaskRouter (via Synapse or queue)
2. Execute simple tasks
3. Report completion

**Example Workflow:**
```bash
# Get simple tasks
priorityqueue next --agent BOLT

# Start
priorityqueue start abc123 --agent BOLT

# Complete
priorityqueue complete abc123 --notes "Done"
```

**Cost Considerations:**
- Route simple tasks to BOLT to save API costs
- BOLT handles: simple bug fixes, file operations, repetitive tasks
- Complex tasks go to FORGE/ATLAS

---

#### PORTER (Mobile Specialist)

**Primary Use Case:** Mobile development, Android/iOS tasks

**Role in Queue:**
- Handles mobile-specific tasks
- BCH Mobile development
- Testing on mobile devices

**Example Workflow:**
```python
from priorityqueue import PriorityQueue, TaskCategory

queue = PriorityQueue()

# Mobile-specific task
task_id = queue.add(
    "Implement push notifications",
    category=TaskCategory.FEATURE,
    assigned_agent="PORTER",
    tags=["mobile", "android", "ios"],
    estimated_duration=180
)
```

---

## 🔗 INTEGRATION WITH OTHER TEAM BRAIN TOOLS

### With AgentHealth

**Correlation Use Case:** Track task execution health alongside agent health metrics.

**Integration Pattern:**
```python
from agenthealth import AgentHealth
from priorityqueue import PriorityQueue

health = AgentHealth()
queue = PriorityQueue()

# Start task with health tracking
task = queue.get_next("ATLAS")
if task:
    queue.start(task.id, "ATLAS")
    health.start_session("ATLAS", session_id=task.id)
    
    try:
        # Do work...
        queue.complete(task.id, notes="Success")
        health.end_session("ATLAS", session_id=task.id, status="success")
    except Exception as e:
        queue.fail(task.id, reason=str(e))
        health.log_error("ATLAS", str(e))
        health.end_session("ATLAS", session_id=task.id, status="failed")
```

**Benefits:**
- Correlate task completion with agent health
- Track error rates per task type
- Identify agents struggling with certain tasks

---

### With SynapseLink

**Notification Use Case:** Send task assignments and completions via Synapse.

**Integration Pattern:**
```python
from synapselink import quick_send
from priorityqueue import PriorityQueue

queue = PriorityQueue()

# Notify agent of new assignment
task_id = queue.add(
    "Urgent: Fix production bug",
    priority=TaskPriority.CRITICAL,
    assigned_agent="ATLAS"
)

task = queue.get(task_id)
quick_send(
    "ATLAS",
    f"New Task Assignment: {task.title}",
    f"Priority: {task.priority.name}\n"
    f"ID: {task.id}\n"
    f"Description: {task.description}\n\n"
    f"Use: priorityqueue start {task.id} --agent ATLAS",
    priority="HIGH"
)

# Notify on completion
queue.complete(task_id, notes="Fixed!")
quick_send(
    "FORGE,LOGAN",
    f"Task Completed: {task.title}",
    f"Completed by: ATLAS\n"
    f"Duration: {queue.get(task_id).actual_duration} minutes",
    priority="NORMAL"
)
```

---

### With TaskQueuePro

**Task Management Use Case:** Sync priorities between systems.

**Integration Pattern:**
```python
from taskqueuepro import TaskQueuePro
from priorityqueue import PriorityQueue

tqp = TaskQueuePro()
pq = PriorityQueue()

# Create in both systems
pq_task_id = pq.add(
    "Important feature",
    priority=TaskPriority.HIGH,
    assigned_agent="ATLAS"
)

tqp.create_task(
    title=f"PQ:{pq_task_id} - Important feature",
    agent="ATLAS",
    priority=2,
    metadata={"pq_id": pq_task_id}
)
```

---

### With SessionReplay

**Debugging Use Case:** Record task execution for analysis.

**Integration Pattern:**
```python
from sessionreplay import SessionReplay
from priorityqueue import PriorityQueue

replay = SessionReplay()
queue = PriorityQueue()

# Start recording
task = queue.get_next("ATLAS")
session_id = replay.start_session("ATLAS", task=f"PQ:{task.id}")
queue.start(task.id, "ATLAS")

# Log key events
replay.log_input(session_id, f"Starting task: {task.title}")

try:
    # Do work...
    replay.log_output(session_id, "Task completed successfully")
    queue.complete(task.id, notes="Done")
    replay.end_session(session_id, status="COMPLETED")
except Exception as e:
    replay.log_error(session_id, str(e))
    queue.fail(task.id, reason=str(e))
    replay.end_session(session_id, status="FAILED")
```

---

### With ContextCompressor

**Token Optimization Use Case:** Compress task descriptions before sharing.

**Integration Pattern:**
```python
from contextcompressor import ContextCompressor
from priorityqueue import PriorityQueue

compressor = ContextCompressor()
queue = PriorityQueue()

# Get task list for briefing
tasks = queue.get_pending(limit=20)
task_list = "\n".join([
    f"- [{t.priority.name}] {t.title}: {t.description}"
    for t in tasks
])

# Compress for token efficiency
compressed = compressor.compress_text(
    task_list,
    query="active tasks summary",
    method="summary"
)

print(f"Original: {len(task_list)} chars")
print(f"Compressed: {len(compressed.compressed_text)} chars")
```

---

### With KnowledgeSync

**Knowledge Sharing Use Case:** Store task completion learnings.

**Integration Pattern:**
```python
from knowledgesync import KnowledgeSync
from priorityqueue import PriorityQueue

ks = KnowledgeSync("ATLAS")
queue = PriorityQueue()

# Complete task with learnings
task = queue.get("abc123")
queue.complete(task.id, notes="Used new caching approach")

# Store learning
ks.add(
    f"Task '{task.title}' completed using caching approach for 50% speedup",
    category="FINDING",
    topics=[task.category.name.lower(), "optimization"],
    source=f"Task {task.id}"
)
```

---

### With ErrorRecovery

**Recovery Use Case:** Auto-retry failed tasks.

**Integration Pattern:**
```python
from errorrecovery import ErrorRecovery
from priorityqueue import PriorityQueue

recovery = ErrorRecovery()
queue = PriorityQueue()

@recovery.wrap(max_retries=3)
def execute_task(task_id):
    task = queue.get(task_id)
    queue.start(task_id, "ATLAS")
    
    # Do risky work...
    result = risky_operation()
    
    queue.complete(task_id, notes=f"Success: {result}")
    return result

# Execute with auto-retry
try:
    execute_task("abc123")
except Exception as e:
    queue.fail("abc123", reason=str(e))
```

---

## 🚀 ADOPTION ROADMAP

### Phase 1: Core Adoption (Week 1)

**Goal:** All agents aware and can use basic features

**Steps:**
1. ✓ Tool deployed to GitHub
2. ☐ Quick-start guides sent via Synapse
3. ☐ Each agent tests basic workflow
4. ☐ Feedback collected

**Success Criteria:**
- All 6 agents have used tool at least once
- No blocking issues reported

### Phase 2: Integration (Week 2-3)

**Goal:** Integrated into daily workflows

**Steps:**
1. ☐ Add to agent startup routines
2. ☐ Create integration examples with existing tools
3. ☐ Automate task assignment workflow
4. ☐ Monitor usage patterns

**Success Criteria:**
- Used daily by at least 4 agents
- Integration examples tested

### Phase 3: Optimization (Week 4+)

**Goal:** Optimized and fully adopted

**Steps:**
1. ☐ Collect efficiency metrics
2. ☐ Implement v1.1 improvements
3. ☐ Create advanced workflow examples
4. ☐ BCH integration planning

**Success Criteria:**
- 90%+ high-priority tasks completed within deadline
- Measurable efficiency improvement

---

## 📊 SUCCESS METRICS

**Adoption Metrics:**
- Number of agents using tool: Track daily
- Tasks created/completed: Track via history
- Queue depth over time: Monitor growth

**Efficiency Metrics:**
- Time to complete high-priority tasks
- Blocked task resolution time
- Agent utilization (tasks per agent)

**Quality Metrics:**
- Overdue task rate
- Task failure rate
- Dependency chain efficiency

---

## 🛠️ TECHNICAL INTEGRATION DETAILS

### Import Paths
```python
# Standard import
from priorityqueue import PriorityQueue, TaskPriority, TaskCategory, TaskStatus

# Specific imports
from priorityqueue import Task, AgentStatus
```

### Configuration
**Default Location:** `~/.priorityqueue/`

**Override:**
```python
queue = PriorityQueue(config_dir="/custom/path")
```

### Error Codes
- 0: Success
- 1: General error / task not found
- 2: Task blocked (cannot start)
- 3: Circular dependency detected

### Logging
PriorityQueue logs all actions to `history.json` (last 1000 entries).

---

## 🔧 MAINTENANCE & SUPPORT

### Update Strategy
- Minor updates (v1.x): As needed
- Major updates (v2.0+): Quarterly with Team Brain sync
- Security patches: Immediate

### Support Channels
- GitHub Issues: Bug reports
- Synapse: Team Brain discussions
- Direct to Forge: Complex issues

### Known Limitations
- Single-process operation (no concurrent writes from multiple processes)
- JSON storage may slow with >10,000 tasks
- No built-in notifications (use SynapseLink)

---

## 📚 ADDITIONAL RESOURCES

- Main Documentation: [README.md](README.md)
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Quick Start Guides: [QUICK_START_GUIDES.md](QUICK_START_GUIDES.md)
- Integration Examples: [INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)
- GitHub: https://github.com/DonkRonk17/PriorityQueue

---

**Last Updated:** January 21, 2026  
**Maintained By:** Forge (Team Brain)
