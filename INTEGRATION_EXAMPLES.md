# PriorityQueue - Integration Examples

## 🎯 INTEGRATION PHILOSOPHY

PriorityQueue is designed to work seamlessly with other Team Brain tools. This document provides **copy-paste-ready code examples** for common integration patterns.

---

## 📚 TABLE OF CONTENTS

1. [Pattern 1: PriorityQueue + AgentHealth](#pattern-1-priorityqueue--agenthealth)
2. [Pattern 2: PriorityQueue + SynapseLink](#pattern-2-priorityqueue--synapselink)
3. [Pattern 3: PriorityQueue + TaskQueuePro](#pattern-3-priorityqueue--taskqueuepro)
4. [Pattern 4: PriorityQueue + SessionReplay](#pattern-4-priorityqueue--sessionreplay)
5. [Pattern 5: PriorityQueue + KnowledgeSync](#pattern-5-priorityqueue--knowledgesync)
6. [Pattern 6: PriorityQueue + ErrorRecovery](#pattern-6-priorityqueue--errorrecovery)
7. [Pattern 7: PriorityQueue + ContextCompressor](#pattern-7-priorityqueue--contextcompressor)
8. [Pattern 8: PriorityQueue + MemoryBridge](#pattern-8-priorityqueue--memorybridge)
9. [Pattern 9: Daily Orchestration Workflow](#pattern-9-daily-orchestration-workflow)
10. [Pattern 10: Full Team Brain Stack](#pattern-10-full-team-brain-stack)

---

## Pattern 1: PriorityQueue + AgentHealth

**Use Case:** Correlate task execution with agent health monitoring

**Why:** Track how task completion affects agent performance and identify struggling agents

**Code:**

```python
from agenthealth import AgentHealth
from priorityqueue import PriorityQueue, TaskPriority

# Initialize both tools
health = AgentHealth()
queue = PriorityQueue()

agent = "ATLAS"

# Get next task
task = queue.get_next(agent)
if not task:
    print("No tasks available")
    exit()

# Start with correlated tracking
session_id = task.id  # Use task ID as session ID for correlation
queue.start(task.id, agent)
health.start_session(agent, session_id=session_id)

try:
    # Log health during work
    health.heartbeat(agent, status="active")
    
    # Do the actual work...
    result = "Work completed successfully"
    
    # Complete task
    queue.complete(task.id, notes=result)
    health.end_session(agent, session_id=session_id, status="success")
    
    print(f"[OK] Task {task.id} completed, health logged")
    
except Exception as e:
    # Log failure
    queue.fail(task.id, reason=str(e))
    health.log_error(agent, str(e))
    health.end_session(agent, session_id=session_id, status="failed")
    
    print(f"[X] Task {task.id} failed: {e}")
```

**Result:** Correlated health and task data - can analyze agent performance per task type

---

## Pattern 2: PriorityQueue + SynapseLink

**Use Case:** Notify agents of task assignments and completions

**Why:** Keep team informed automatically without manual status updates

**Code:**

```python
from synapselink import quick_send
from priorityqueue import PriorityQueue, TaskPriority

queue = PriorityQueue()

# === NOTIFY ON TASK ASSIGNMENT ===

def assign_task(title, agent, priority=TaskPriority.MEDIUM):
    """Create task and notify assigned agent."""
    task_id = queue.add(
        title,
        priority=priority,
        assigned_agent=agent
    )
    
    task = queue.get(task_id)
    
    # Notify agent
    quick_send(
        agent,
        f"New Task: {task.title}",
        f"ID: {task.id}\n"
        f"Priority: {task.priority.name}\n\n"
        f"To start: priorityqueue start {task.id} --agent {agent}",
        priority="NORMAL"
    )
    
    return task_id

# Example
assign_task("Implement login feature", "ATLAS", TaskPriority.HIGH)


# === NOTIFY ON COMPLETION ===

def complete_with_notification(task_id, notes, notify_agents=["FORGE"]):
    """Complete task and notify stakeholders."""
    task = queue.get(task_id)
    queue.complete(task_id, notes=notes)
    
    completed_task = queue.get(task_id)
    
    # Notify
    quick_send(
        ",".join(notify_agents),
        f"Task Completed: {task.title}",
        f"Completed by: {task.assigned_agent}\n"
        f"Duration: {completed_task.actual_duration} minutes\n"
        f"Notes: {notes}",
        priority="NORMAL"
    )

# Example
complete_with_notification("abc123", "Feature implemented and tested")


# === URGENT TASK ALERT ===

def create_urgent_task(title, description=""):
    """Create urgent task and alert everyone."""
    task_id = queue.add(
        title,
        description=description,
        priority=TaskPriority.CRITICAL,
        assigned_agent="ANY"
    )
    
    quick_send(
        "FORGE,ATLAS,CLIO,NEXUS,BOLT,PORTER",
        f"[URGENT] New Critical Task",
        f"Task: {title}\n"
        f"ID: {task_id}\n"
        f"Assigned: ANY (first available)\n\n"
        f"Someone please pick this up ASAP!",
        priority="HIGH"
    )
    
    return task_id
```

**Result:** Automatic notifications keep team synchronized

---

## Pattern 3: PriorityQueue + TaskQueuePro

**Use Case:** Manage tasks in both systems for different views

**Why:** PriorityQueue for intelligent ordering, TaskQueuePro for status tracking

**Code:**

```python
from taskqueuepro import TaskQueuePro
from priorityqueue import PriorityQueue, TaskPriority

tqp = TaskQueuePro()
pq = PriorityQueue()

# === SYNC TASK CREATION ===

def create_synced_task(title, agent, priority=TaskPriority.MEDIUM):
    """Create task in both systems."""
    # Create in PriorityQueue (intelligent ordering)
    pq_id = pq.add(title, priority=priority, assigned_agent=agent)
    
    # Mirror in TaskQueuePro (status tracking)
    tqp_id = tqp.create_task(
        title=f"[PQ:{pq_id}] {title}",
        agent=agent,
        priority=priority.value,
        metadata={"pq_id": pq_id}
    )
    
    return {"pq_id": pq_id, "tqp_id": tqp_id}


# === SYNC STATUS CHANGES ===

def sync_start(pq_id, tqp_id, agent):
    """Start task in both systems."""
    pq.start(pq_id, agent)
    tqp.start_task(tqp_id)

def sync_complete(pq_id, tqp_id, notes):
    """Complete task in both systems."""
    pq.complete(pq_id, notes=notes)
    tqp.complete_task(tqp_id, result={"notes": notes})


# === EXAMPLE WORKFLOW ===

# Create
ids = create_synced_task("Implement feature", "ATLAS", TaskPriority.HIGH)

# Start
sync_start(ids["pq_id"], ids["tqp_id"], "ATLAS")

# Complete
sync_complete(ids["pq_id"], ids["tqp_id"], "Feature done!")
```

**Result:** Best of both worlds - intelligent ordering + detailed tracking

---

## Pattern 4: PriorityQueue + SessionReplay

**Use Case:** Record task execution for debugging and analysis

**Why:** Replay failed task sessions to understand what went wrong

**Code:**

```python
from sessionreplay import SessionReplay
from priorityqueue import PriorityQueue

replay = SessionReplay()
queue = PriorityQueue()

agent = "ATLAS"

# Get task
task = queue.get_next(agent)
if not task:
    print("No tasks")
    exit()

# Start recording
session_id = replay.start_session(agent, task=f"PQ:{task.id} - {task.title}")
queue.start(task.id, agent)

# Log key events
replay.log_input(session_id, f"Starting task: {task.title}")
replay.log_input(session_id, f"Priority: {task.priority.name}")

try:
    # Step 1
    replay.log_output(session_id, "Step 1: Reading requirements...")
    # ... actual work ...
    
    # Step 2
    replay.log_output(session_id, "Step 2: Implementing solution...")
    # ... actual work ...
    
    # Step 3
    replay.log_output(session_id, "Step 3: Testing...")
    # ... actual work ...
    
    # Success
    replay.log_output(session_id, "All steps completed successfully")
    queue.complete(task.id, notes="Completed with session recording")
    replay.end_session(session_id, status="COMPLETED")
    
except Exception as e:
    # Log error
    replay.log_error(session_id, f"Error at step: {e}")
    queue.fail(task.id, reason=str(e))
    replay.end_session(session_id, status="FAILED")
    
    # Later, can replay this session to debug
    print(f"Session recorded: {session_id}")
    print("Use 'sessionreplay replay {session_id}' to debug")
```

**Result:** Full session replay available for failed task debugging

---

## Pattern 5: PriorityQueue + KnowledgeSync

**Use Case:** Store learnings from completed tasks

**Why:** Build organizational knowledge from task execution

**Code:**

```python
from knowledgesync import KnowledgeSync
from priorityqueue import PriorityQueue

queue = PriorityQueue()
ks = KnowledgeSync("ATLAS")

# === STORE LEARNING ON COMPLETION ===

def complete_with_learning(task_id, notes, learnings=None):
    """Complete task and optionally store learnings."""
    task = queue.get(task_id)
    queue.complete(task_id, notes=notes)
    
    if learnings:
        for learning in learnings:
            ks.add(
                learning["content"],
                category=learning.get("category", "FINDING"),
                topics=[task.category.name.lower()] + learning.get("topics", []),
                source=f"Task {task_id}: {task.title}"
            )
            print(f"Stored learning: {learning['content'][:50]}...")

# Example
complete_with_learning(
    "abc123",
    notes="Implemented caching for 50% speedup",
    learnings=[
        {
            "content": "Using Redis caching for API responses improves performance by 50%",
            "category": "FINDING",
            "topics": ["performance", "caching", "redis"]
        },
        {
            "content": "Cache invalidation is tricky - use TTL of 5 minutes for dynamic data",
            "category": "DECISION",
            "topics": ["caching", "architecture"]
        }
    ]
)


# === QUERY KNOWLEDGE BEFORE STARTING ===

def start_with_context(task_id, agent):
    """Start task with relevant knowledge context."""
    task = queue.get(task_id)
    
    # Find relevant learnings
    relevant = ks.query(task.title, limit=5)
    
    if relevant:
        print(f"\nRelevant knowledge for '{task.title}':")
        for entry in relevant:
            print(f"  - {entry.content[:80]}...")
        print()
    
    queue.start(task_id, agent)

# Example
start_with_context("def456", "ATLAS")
```

**Result:** Team knowledge grows with each completed task

---

## Pattern 6: PriorityQueue + ErrorRecovery

**Use Case:** Auto-retry failed tasks with intelligent recovery

**Why:** Reduce manual intervention for transient failures

**Code:**

```python
from errorrecovery import ErrorRecovery
from priorityqueue import PriorityQueue, TaskPriority

recovery = ErrorRecovery()
queue = PriorityQueue()

# === WRAP TASK EXECUTION WITH RECOVERY ===

@recovery.wrap(max_retries=3, fallback_result="SKIPPED")
def execute_risky_task(task_id, agent):
    """Execute task with automatic retry on failure."""
    task = queue.get(task_id)
    queue.start(task_id, agent)
    
    # Risky operation that might fail
    result = perform_risky_operation()
    
    queue.complete(task_id, notes=f"Success: {result}")
    return result


def perform_risky_operation():
    """Simulated operation that might fail."""
    import random
    if random.random() < 0.3:
        raise ConnectionError("Temporary network issue")
    return "Operation completed"


# === USE IN WORKFLOW ===

task = queue.get_next("ATLAS")
if task:
    try:
        result = execute_risky_task(task.id, "ATLAS")
        print(f"Task result: {result}")
    except Exception as e:
        # All retries failed
        queue.fail(task.id, reason=f"Failed after 3 retries: {e}")
        print(f"Task failed permanently: {e}")


# === CONDITIONAL RETRY BASED ON ERROR TYPE ===

def smart_execute(task_id, agent):
    """Execute with error-type-aware handling."""
    task = queue.get(task_id)
    queue.start(task_id, agent)
    
    try:
        result = perform_risky_operation()
        queue.complete(task_id, notes=f"Success: {result}")
        
    except ConnectionError as e:
        # Retry on network errors
        error_id = recovery.identify(str(e))
        if error_id and recovery.should_retry(error_id):
            queue.update(task_id, notes="Retrying due to network error...")
            # Put back in queue for retry
            queue._tasks[task_id].status = TaskStatus.PENDING
            queue._save_data()
        else:
            queue.fail(task_id, reason=str(e))
            
    except ValueError as e:
        # Don't retry validation errors
        queue.fail(task_id, reason=f"Validation error (no retry): {e}")
```

**Result:** Transient failures auto-recovered, permanent failures properly logged

---

## Pattern 7: PriorityQueue + ContextCompressor

**Use Case:** Compress task reports for token efficiency

**Why:** Save tokens when sharing large task summaries

**Code:**

```python
from contextcompressor import ContextCompressor
from priorityqueue import PriorityQueue

compressor = ContextCompressor()
queue = PriorityQueue()

# === COMPRESS QUEUE SUMMARY ===

def get_compressed_queue_summary():
    """Get token-efficient summary of current queue."""
    # Get all pending tasks
    pending = queue.get_pending(limit=50)
    
    # Build full summary
    full_summary = "Current Task Queue:\n\n"
    for task in pending:
        full_summary += f"- [{task.priority.name}] {task.title}\n"
        full_summary += f"  Agent: {task.assigned_agent}\n"
        full_summary += f"  Status: {task.status.name}\n"
        if task.description:
            full_summary += f"  Details: {task.description}\n"
        full_summary += "\n"
    
    # Compress
    compressed = compressor.compress_text(
        full_summary,
        query="task summary priorities",
        method="summary"
    )
    
    original_tokens = len(full_summary) // 4
    compressed_tokens = len(compressed.compressed_text) // 4
    savings = (original_tokens - compressed_tokens) / original_tokens * 100
    
    print(f"Original: ~{original_tokens} tokens")
    print(f"Compressed: ~{compressed_tokens} tokens")
    print(f"Savings: {savings:.1f}%")
    
    return compressed.compressed_text


# === COMPRESS COMPLETION REPORT ===

def complete_with_compressed_report(task_id, full_notes):
    """Complete task and store compressed report."""
    # Compress verbose notes
    compressed = compressor.compress_text(
        full_notes,
        query="key results",
        method="extraction"
    )
    
    # Store compressed version
    queue.complete(task_id, notes=compressed.compressed_text)
    
    # Return both
    return {
        "full": full_notes,
        "compressed": compressed.compressed_text,
        "savings": f"{compressed.compression_ratio*100:.1f}%"
    }


# Example
result = complete_with_compressed_report(
    "abc123",
    """
    Implementation completed successfully. Made the following changes:
    1. Added user authentication module with JWT support
    2. Created login/logout API endpoints
    3. Implemented password hashing with bcrypt
    4. Added session management with Redis
    5. Created unit tests for all new functions (25 tests)
    6. Updated API documentation with new endpoints
    7. Added rate limiting to prevent brute force attacks
    8. Implemented account lockout after 5 failed attempts
    
    Testing results:
    - All 25 unit tests passing
    - Integration tests passing
    - Load tested with 1000 concurrent users
    - Security scan completed with no vulnerabilities
    """
)

print(f"Saved {result['savings']} tokens")
```

**Result:** 50-70% token savings on verbose reports

---

## Pattern 8: PriorityQueue + MemoryBridge

**Use Case:** Persist task metadata across sessions

**Why:** Maintain context between sessions without re-querying

**Code:**

```python
from memorybridge import MemoryBridge
from priorityqueue import PriorityQueue

memory = MemoryBridge()
queue = PriorityQueue()

agent = "ATLAS"

# === STORE TASK CONTEXT ===

def start_task_with_memory(task_id, agent):
    """Start task and store context in memory."""
    task = queue.get(task_id)
    queue.start(task_id, agent)
    
    # Store context for later
    memory.set(f"current_task_{agent}", {
        "task_id": task_id,
        "title": task.title,
        "started_at": task.started_at,
        "priority": task.priority.name
    })
    memory.sync()
    
    return task


# === RESUME FROM MEMORY ===

def resume_task(agent):
    """Resume task from last session."""
    context = memory.get(f"current_task_{agent}")
    
    if context:
        task = queue.get(context["task_id"])
        if task and task.status.name == "IN_PROGRESS":
            print(f"Resuming: {context['title']}")
            print(f"Started: {context['started_at']}")
            return task
    
    print("No task to resume")
    return None


# === CLEAR ON COMPLETION ===

def complete_task_with_memory(task_id, agent, notes):
    """Complete task and clear from memory."""
    queue.complete(task_id, notes=notes)
    
    # Clear context
    memory.delete(f"current_task_{agent}")
    memory.sync()
    
    print("Task completed, context cleared")


# === SESSION WORKFLOW ===

# Session start
resumed = resume_task(agent)
if resumed:
    # Continue working on resumed task
    complete_task_with_memory(resumed.id, agent, "Resumed and completed")
else:
    # Get new task
    task = queue.get_next(agent)
    if task:
        start_task_with_memory(task.id, agent)
```

**Result:** Seamless session continuation with persistent context

---

## Pattern 9: Daily Orchestration Workflow

**Use Case:** FORGE's daily queue management routine

**Why:** Systematic daily prioritization and assignment

**Code:**

```python
from priorityqueue import PriorityQueue, TaskPriority, TaskStatus
from synapselink import quick_send
from datetime import datetime

queue = PriorityQueue()

def morning_orchestration():
    """FORGE's daily morning routine."""
    
    print("=" * 50)
    print(f"DAILY ORCHESTRATION - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 50)
    
    # 1. Get stats
    stats = queue.get_stats()
    print(f"\nQueue Status:")
    print(f"  Total: {stats['total_tasks']}")
    print(f"  Pending: {stats['by_status'].get('PENDING', 0)}")
    print(f"  In Progress: {stats['by_status'].get('IN_PROGRESS', 0)}")
    print(f"  Blocked: {stats['blocked_count']}")
    print(f"  Overdue: {stats['overdue_count']}")
    
    # 2. Check overdue
    overdue_tasks = [
        t for t in queue.get_pending()
        if t.deadline and datetime.fromisoformat(t.deadline) < datetime.now()
    ]
    
    if overdue_tasks:
        print(f"\n[!] OVERDUE TASKS ({len(overdue_tasks)}):")
        for task in overdue_tasks:
            print(f"    {task.id}: {task.title}")
            # Escalate
            queue.update(task.id, priority=TaskPriority.CRITICAL)
    
    # 3. Check blocked tasks
    blocked = queue.get_blocked()
    if blocked:
        print(f"\n[!] BLOCKED TASKS ({len(blocked)}):")
        for task in blocked:
            deps = ", ".join(task.dependencies[:3])
            print(f"    {task.title[:40]} <- waiting on: {deps}")
    
    # 4. Balance agent workloads
    print("\nAgent Workloads:")
    for agent in ["FORGE", "ATLAS", "CLIO", "NEXUS", "BOLT", "PORTER"]:
        tasks = queue.get_agent_tasks(agent)
        status = queue.get_agent_status(agent)
        avail = "AVAILABLE" if status.available else "BUSY"
        print(f"  {agent}: {len(tasks)} tasks ({avail})")
    
    # 5. Send daily briefing
    briefing = f"""Daily Queue Briefing - {datetime.now().strftime('%Y-%m-%d')}

Stats:
- Total: {stats['total_tasks']} tasks
- Pending: {stats['by_status'].get('PENDING', 0)}
- Blocked: {stats['blocked_count']}
- Overdue: {stats['overdue_count']}

Overdue: {len(overdue_tasks)} tasks need immediate attention
Blocked: {len(blocked)} tasks waiting on dependencies

Check your next task:
  priorityqueue next --agent [YOUR_NAME]
"""
    
    quick_send(
        "ATLAS,CLIO,NEXUS,BOLT,PORTER",
        "Daily Queue Briefing",
        briefing,
        priority="NORMAL"
    )
    
    print("\n[OK] Daily briefing sent to all agents")
    print("=" * 50)


# Run morning orchestration
morning_orchestration()
```

**Result:** Systematic daily queue management and team communication

---

## Pattern 10: Full Team Brain Stack

**Use Case:** Complete integration with all tools

**Why:** Maximum automation and coordination

**Code:**

```python
"""
Full Team Brain Stack Integration
Combines all tools for complete task management
"""

from priorityqueue import PriorityQueue, TaskPriority, TaskStatus
from synapselink import quick_send
from agenthealth import AgentHealth
from sessionreplay import SessionReplay
from knowledgesync import KnowledgeSync
from errorrecovery import ErrorRecovery
from datetime import datetime

# Initialize all tools
queue = PriorityQueue()
health = AgentHealth()
replay = SessionReplay()
knowledge = KnowledgeSync("ATLAS")
recovery = ErrorRecovery()

agent = "ATLAS"


def full_stack_task_execution(agent):
    """Execute task with full Team Brain integration."""
    
    # === PHASE 1: GET TASK ===
    task = queue.get_next(agent)
    if not task:
        print("No tasks available")
        return None
    
    print(f"Starting: {task.title}")
    
    # === PHASE 2: START WITH TRACKING ===
    session_id = task.id
    
    # Start in all systems
    queue.start(task.id, agent)
    health.start_session(agent, session_id=session_id)
    replay.start_session(agent, task=f"PQ:{task.id}")
    
    # Check for relevant knowledge
    prior_knowledge = knowledge.query(task.title, limit=3)
    if prior_knowledge:
        replay.log_input(session_id, f"Found {len(prior_knowledge)} relevant learnings")
    
    # === PHASE 3: EXECUTE WITH RECOVERY ===
    @recovery.wrap(max_retries=2)
    def do_work():
        replay.log_output(session_id, "Starting work...")
        health.heartbeat(agent, status="active")
        
        # Actual work here
        result = "Work completed successfully"
        
        replay.log_output(session_id, f"Result: {result}")
        return result
    
    try:
        result = do_work()
        
        # === PHASE 4: COMPLETE SUCCESSFULLY ===
        
        # Update all systems
        queue.complete(task.id, notes=result)
        health.end_session(agent, session_id=session_id, status="success")
        replay.end_session(session_id, status="COMPLETED")
        
        # Store learning
        knowledge.add(
            f"Completed task '{task.title}': {result}",
            category="FINDING",
            topics=[task.category.name.lower()],
            source=f"Task {task.id}"
        )
        
        # Notify
        quick_send(
            "FORGE",
            f"Task Completed: {task.title}",
            f"Agent: {agent}\nResult: {result}",
            priority="NORMAL"
        )
        
        print(f"[OK] Task completed with full tracking")
        return result
        
    except Exception as e:
        # === PHASE 5: HANDLE FAILURE ===
        
        queue.fail(task.id, reason=str(e))
        health.log_error(agent, str(e))
        health.end_session(agent, session_id=session_id, status="failed")
        replay.log_error(session_id, str(e))
        replay.end_session(session_id, status="FAILED")
        
        # Alert
        quick_send(
            "FORGE,LOGAN",
            f"Task Failed: {task.title}",
            f"Agent: {agent}\nError: {e}\n\nSession: {session_id}",
            priority="HIGH"
        )
        
        print(f"[X] Task failed: {e}")
        return None


# Execute
result = full_stack_task_execution(agent)

if result:
    print("\nNext task available:")
    next_task = queue.get_next(agent)
    if next_task:
        print(f"  {next_task.title}")
```

**Result:** Complete automation with health monitoring, session recording, knowledge storage, error recovery, and team notifications

---

## 📊 RECOMMENDED INTEGRATION PRIORITY

**Week 1 (Essential):**
1. ✅ AgentHealth - Health correlation
2. ✅ SynapseLink - Team notifications
3. ✅ SessionReplay - Debugging

**Week 2 (Productivity):**
4. ☐ KnowledgeSync - Learning storage
5. ☐ ErrorRecovery - Auto-retry
6. ☐ MemoryBridge - Session persistence

**Week 3 (Advanced):**
7. ☐ ContextCompressor - Token optimization
8. ☐ TaskQueuePro - Dual tracking
9. ☐ Full stack integration

---

## 🔧 TROUBLESHOOTING INTEGRATIONS

**Import Errors:**
```python
# Ensure all tools are in Python path
import sys
from pathlib import Path
sys.path.append(str(Path.home() / "OneDrive/Documents/AutoProjects"))

# Then import
from priorityqueue import PriorityQueue
```

**Version Conflicts:**
```bash
# Check versions
priorityqueue --version
agenthealth --version

# Update if needed
cd AutoProjects/PriorityQueue
git pull origin main
```

**Session ID Correlation:**
- Always use task.id as session_id for correlation
- Enables cross-tool analysis and debugging

---

**Last Updated:** January 21, 2026  
**Maintained By:** Forge (Team Brain)
