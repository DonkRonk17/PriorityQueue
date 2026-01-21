#!/usr/bin/env python3
"""
PriorityQueue - Intelligent Task Prioritization for Team Brain

A sophisticated task queue system that automatically prioritizes tasks based on:
- Urgency (deadline proximity)
- Importance (assigned priority level)
- Dependencies (blocked tasks wait)
- Agent availability (route to free agents)
- Resource requirements (match capabilities)

Ensures Logan's most important tasks are handled first by the optimal agent,
with automatic reordering as context changes.

Author: Forge (Team Brain)
For: Logan Smith / Metaphy LLC
Version: 1.0.0
Date: January 21, 2026
License: MIT
Q-Mode: Tool #17 of 18 (Tier 3: Advanced Capabilities)
"""

import argparse
import json
import sys
import uuid
import heapq
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import time


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class TaskStatus(Enum):
    """Task status states."""
    PENDING = "PENDING"         # Waiting to be started
    IN_PROGRESS = "IN_PROGRESS" # Currently being worked on
    BLOCKED = "BLOCKED"         # Waiting for dependencies
    COMPLETED = "COMPLETED"     # Successfully finished
    CANCELLED = "CANCELLED"     # No longer needed
    FAILED = "FAILED"           # Failed after attempts


class TaskPriority(Enum):
    """Base priority levels."""
    CRITICAL = 1    # Must be done immediately
    HIGH = 2        # Very important
    MEDIUM = 3      # Normal priority
    LOW = 4         # Can wait
    BACKLOG = 5     # Do when nothing else


class TaskCategory(Enum):
    """Task categories for grouping."""
    DEVELOPMENT = "DEVELOPMENT"
    DOCUMENTATION = "DOCUMENTATION"
    TESTING = "TESTING"
    BUGFIX = "BUGFIX"
    FEATURE = "FEATURE"
    RESEARCH = "RESEARCH"
    COORDINATION = "COORDINATION"
    MAINTENANCE = "MAINTENANCE"
    URGENT = "URGENT"
    OTHER = "OTHER"


# Team Brain agents
AGENTS = ["FORGE", "ATLAS", "CLIO", "NEXUS", "BOLT", "PORTER", "ANY"]

# Default config location
DEFAULT_CONFIG_DIR = Path.home() / ".priorityqueue"

# Version
VERSION = "1.0.0"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Task:
    """Represents a task in the priority queue."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.OTHER
    assigned_agent: str = "ANY"
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None  # ISO format
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    tags: List[str] = field(default_factory=list)
    estimated_duration: int = 30  # Minutes
    actual_duration: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: 'Task') -> bool:
        """For heap comparison - lower score = higher priority."""
        return self.calculate_score() < other.calculate_score()
    
    def calculate_score(self) -> float:
        """
        Calculate priority score (lower = higher priority).
        
        Factors:
        - Base priority (1-5)
        - Urgency multiplier (deadline proximity)
        - Age factor (older tasks get slight boost)
        - Blocked penalty (blocked tasks deprioritized)
        """
        score = float(self.priority.value)
        
        # Urgency multiplier based on deadline
        if self.deadline:
            try:
                deadline_dt = datetime.fromisoformat(self.deadline)
                now = datetime.now()
                hours_until_deadline = (deadline_dt - now).total_seconds() / 3600
                
                if hours_until_deadline < 0:
                    # Overdue - highest urgency
                    score *= 0.1
                elif hours_until_deadline < 1:
                    # Due within 1 hour
                    score *= 0.3
                elif hours_until_deadline < 4:
                    # Due within 4 hours
                    score *= 0.5
                elif hours_until_deadline < 24:
                    # Due within 24 hours
                    score *= 0.7
                elif hours_until_deadline < 72:
                    # Due within 3 days
                    score *= 0.9
            except (ValueError, TypeError):
                pass
        
        # Age factor - older tasks get slight priority boost
        try:
            created = datetime.fromisoformat(self.created_at)
            age_hours = (datetime.now() - created).total_seconds() / 3600
            if age_hours > 24:
                score *= 0.95  # Slight boost for aging tasks
            if age_hours > 72:
                score *= 0.90
        except (ValueError, TypeError):
            pass
        
        # Blocked tasks get penalty
        if self.status == TaskStatus.BLOCKED:
            score *= 10  # Significantly deprioritize blocked tasks
        
        return score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['category'] = self.category.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary."""
        data = data.copy()
        data['status'] = TaskStatus(data.get('status', 'PENDING'))
        data['priority'] = TaskPriority(data.get('priority', 3))
        data['category'] = TaskCategory(data.get('category', 'OTHER'))
        return cls(**data)


@dataclass
class AgentStatus:
    """Tracks agent availability and workload."""
    name: str
    available: bool = True
    current_task: Optional[str] = None  # Task ID
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_today: int = 0
    capabilities: List[str] = field(default_factory=list)
    max_concurrent: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentStatus':
        """Create from dictionary."""
        return cls(**data)


# ============================================================================
# PRIORITY QUEUE CLASS
# ============================================================================

class PriorityQueue:
    """
    Intelligent task prioritization system for Team Brain.
    
    Features:
    - Multi-factor priority scoring (urgency, importance, age, dependencies)
    - Dependency tracking with automatic blocking
    - Agent availability management
    - Real-time reordering as context changes
    - Persistent storage (JSON)
    - Full Python API and CLI interface
    
    Example:
        >>> queue = PriorityQueue()
        >>> task_id = queue.add("Fix bug in login", priority=TaskPriority.HIGH)
        >>> queue.add("Write tests", dependencies=[task_id])
        >>> next_task = queue.get_next()  # Returns highest priority available task
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize PriorityQueue.
        
        Args:
            config_dir: Directory for storing queue data.
                       Defaults to ~/.priorityqueue/
        """
        self.config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks_file = self.config_dir / "tasks.json"
        self.agents_file = self.config_dir / "agents.json"
        self.history_file = self.config_dir / "history.json"
        
        self._tasks: Dict[str, Task] = {}
        self._agents: Dict[str, AgentStatus] = {}
        self._history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        self._load_data()
        self._initialize_agents()
    
    def _load_data(self) -> None:
        """Load data from persistent storage."""
        # Load tasks
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._tasks = {k: Task.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, IOError):
                self._tasks = {}
        
        # Load agents
        if self.agents_file.exists():
            try:
                with open(self.agents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._agents = {k: AgentStatus.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, IOError):
                self._agents = {}
        
        # Load history
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._history = []
    
    def _save_data(self) -> None:
        """Save data to persistent storage."""
        # Save tasks
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            data = {k: v.to_dict() for k, v in self._tasks.items()}
            json.dump(data, f, indent=2)
        
        # Save agents
        with open(self.agents_file, 'w', encoding='utf-8') as f:
            data = {k: v.to_dict() for k, v in self._agents.items()}
            json.dump(data, f, indent=2)
        
        # Save history (keep last 1000 entries)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self._history[-1000:], f, indent=2)
    
    def _initialize_agents(self) -> None:
        """Initialize default Team Brain agents if not present."""
        for agent_name in AGENTS:
            if agent_name not in self._agents and agent_name != "ANY":
                self._agents[agent_name] = AgentStatus(
                    name=agent_name,
                    capabilities=self._get_agent_capabilities(agent_name)
                )
        self._save_data()
    
    def _get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Get default capabilities for an agent."""
        capabilities = {
            "FORGE": ["COORDINATION", "DOCUMENTATION", "RESEARCH", "REVIEW"],
            "ATLAS": ["DEVELOPMENT", "TESTING", "BUGFIX", "FEATURE"],
            "CLIO": ["DEVELOPMENT", "MAINTENANCE", "DOCUMENTATION"],
            "NEXUS": ["RESEARCH", "TESTING", "DOCUMENTATION"],
            "BOLT": ["DEVELOPMENT", "BUGFIX", "FEATURE"],
            "PORTER": ["DEVELOPMENT", "MOBILE", "TESTING"],
        }
        return capabilities.get(agent_name, ["OTHER"])
    
    def _log_action(self, action: str, task_id: str, details: Dict[str, Any] = None) -> None:
        """Log an action to history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "task_id": task_id,
            "details": details or {}
        }
        self._history.append(entry)
    
    def _update_blocked_status(self) -> None:
        """Update blocked status for all tasks based on dependencies."""
        for task_id, task in self._tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED, TaskStatus.IN_PROGRESS]:
                continue
            
            if task.dependencies:
                # Check if all dependencies are completed
                all_deps_complete = all(
                    (dep_task := self._tasks.get(dep_id)) and dep_task.status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                
                if not all_deps_complete:
                    task.status = TaskStatus.BLOCKED
                elif all_deps_complete and task.status == TaskStatus.BLOCKED:
                    task.status = TaskStatus.PENDING
            else:
                # No dependencies - should be pending if was blocked
                if task.status == TaskStatus.BLOCKED:
                    task.status = TaskStatus.PENDING
    
    # ========================================================================
    # TASK MANAGEMENT
    # ========================================================================
    
    def add(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        category: TaskCategory = TaskCategory.OTHER,
        assigned_agent: str = "ANY",
        created_by: str = "",
        deadline: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        estimated_duration: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a new task to the queue.
        
        Args:
            title: Task title (required)
            description: Detailed description
            priority: TaskPriority level (CRITICAL, HIGH, MEDIUM, LOW, BACKLOG)
            category: TaskCategory for grouping
            assigned_agent: Specific agent or "ANY"
            created_by: Who created this task
            deadline: ISO format deadline string
            dependencies: List of task IDs this depends on
            tags: List of tags for filtering
            estimated_duration: Estimated minutes to complete
            metadata: Additional custom data
            
        Returns:
            Task ID (UUID string)
            
        Example:
            >>> task_id = queue.add("Implement login", priority=TaskPriority.HIGH)
        """
        with self._lock:
            task_id = str(uuid.uuid4())[:8]  # Short UUID
            
            task = Task(
                id=task_id,
                title=title,
                description=description,
                priority=priority,
                category=category,
                assigned_agent=assigned_agent,
                created_by=created_by,
                deadline=deadline,
                dependencies=dependencies or [],
                tags=tags or [],
                estimated_duration=estimated_duration,
                metadata=metadata or {}
            )
            
            # Check if blocked by dependencies
            if task.dependencies:
                all_deps_complete = all(
                    (dep_task := self._tasks.get(dep_id)) and dep_task.status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if not all_deps_complete:
                    task.status = TaskStatus.BLOCKED
            
            self._tasks[task_id] = task
            self._log_action("ADD", task_id, {"title": title, "priority": priority.name})
            self._save_data()
            
            return task_id
    
    def get(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            Task object or None if not found
        """
        return self._tasks.get(task_id)
    
    def update(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        category: Optional[TaskCategory] = None,
        assigned_agent: Optional[str] = None,
        deadline: Optional[str] = None,
        tags: Optional[List[str]] = None,
        estimated_duration: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update a task's fields.
        
        Args:
            task_id: Task ID to update
            Other args: Fields to update (None = no change)
            
        Returns:
            True if updated, False if task not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if priority is not None:
                task.priority = priority
            if category is not None:
                task.category = category
            if assigned_agent is not None:
                task.assigned_agent = assigned_agent
            if deadline is not None:
                task.deadline = deadline
            if tags is not None:
                task.tags = tags
            if estimated_duration is not None:
                task.estimated_duration = estimated_duration
            if notes is not None:
                task.notes = notes
            
            self._log_action("UPDATE", task_id, {"fields": "updated"})
            self._save_data()
            return True
    
    def delete(self, task_id: str) -> bool:
        """
        Delete a task from the queue.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks.pop(task_id)
            self._log_action("DELETE", task_id, {"title": task.title})
            self._save_data()
            return True
    
    def start(self, task_id: str, agent: Optional[str] = None) -> bool:
        """
        Mark a task as in progress.
        
        Args:
            task_id: Task ID to start
            agent: Agent starting the task
            
        Returns:
            True if started, False if blocked or not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.BLOCKED:
                return False
            
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat()
            
            if agent:
                task.assigned_agent = agent
                if agent in self._agents:
                    self._agents[agent].current_task = task_id
                    self._agents[agent].available = False
            
            self._log_action("START", task_id, {"agent": agent})
            self._save_data()
            return True
    
    def complete(self, task_id: str, notes: str = "") -> bool:
        """
        Mark a task as completed.
        
        Args:
            task_id: Task ID to complete
            notes: Completion notes
            
        Returns:
            True if completed, False if not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            if notes:
                task.notes = notes
            
            # Calculate actual duration
            if task.started_at:
                try:
                    started = datetime.fromisoformat(task.started_at)
                    completed = datetime.fromisoformat(task.completed_at)
                    task.actual_duration = int((completed - started).total_seconds() / 60)
                except (ValueError, TypeError):
                    pass
            
            # Update agent status
            if task.assigned_agent in self._agents:
                agent = self._agents[task.assigned_agent]
                agent.current_task = None
                agent.available = True
                agent.completed_today += 1
                agent.last_active = datetime.now().isoformat()
            
            # Update blocked tasks that depend on this
            self._update_blocked_status()
            
            self._log_action("COMPLETE", task_id, {"duration": task.actual_duration})
            self._save_data()
            return True
    
    def fail(self, task_id: str, reason: str = "") -> bool:
        """
        Mark a task as failed.
        
        Args:
            task_id: Task ID that failed
            reason: Failure reason
            
        Returns:
            True if marked, False if not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            if reason:
                task.notes = f"FAILED: {reason}"
            
            # Update agent status
            if task.assigned_agent in self._agents:
                agent = self._agents[task.assigned_agent]
                agent.current_task = None
                agent.available = True
            
            self._log_action("FAIL", task_id, {"reason": reason})
            self._save_data()
            return True
    
    def cancel(self, task_id: str, reason: str = "") -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID to cancel
            reason: Cancellation reason
            
        Returns:
            True if cancelled, False if not found
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.status = TaskStatus.CANCELLED
            if reason:
                task.notes = f"CANCELLED: {reason}"
            
            # Update agent status
            if task.assigned_agent in self._agents and task.status == TaskStatus.IN_PROGRESS:
                agent = self._agents[task.assigned_agent]
                agent.current_task = None
                agent.available = True
            
            self._log_action("CANCEL", task_id, {"reason": reason})
            self._save_data()
            return True
    
    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """
        Add a dependency to a task.
        
        Args:
            task_id: Task ID to add dependency to
            depends_on: Task ID that must complete first
            
        Returns:
            True if added, False if task not found or circular
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or depends_on not in self._tasks:
                return False
            
            # Check for circular dependency
            if self._would_create_cycle(task_id, depends_on):
                return False
            
            if depends_on not in task.dependencies:
                task.dependencies.append(depends_on)
            
            self._update_blocked_status()
            self._log_action("ADD_DEPENDENCY", task_id, {"depends_on": depends_on})
            self._save_data()
            return True
    
    def remove_dependency(self, task_id: str, depends_on: str) -> bool:
        """Remove a dependency from a task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if depends_on in task.dependencies:
                task.dependencies.remove(depends_on)
            
            self._update_blocked_status()
            self._save_data()
            return True
    
    def _would_create_cycle(self, task_id: str, new_dep: str) -> bool:
        """Check if adding a dependency would create a cycle."""
        visited = set()
        
        def dfs(current: str) -> bool:
            if current == task_id:
                return True
            if current in visited:
                return False
            visited.add(current)
            
            task = self._tasks.get(current)
            if not task:
                return False
            
            for dep in task.dependencies:
                if dfs(dep):
                    return True
            return False
        
        return dfs(new_dep)
    
    # ========================================================================
    # QUEUE OPERATIONS
    # ========================================================================
    
    def get_next(self, agent: Optional[str] = None) -> Optional[Task]:
        """
        Get the highest priority task that's ready to work on.
        
        Args:
            agent: Specific agent to get task for (considers assignment and capabilities)
            
        Returns:
            Highest priority available task, or None if queue empty
            
        Example:
            >>> task = queue.get_next("ATLAS")
            >>> if task:
            ...     queue.start(task.id, "ATLAS")
        """
        self._update_blocked_status()
        
        # Get all pending tasks
        candidates = [
            task for task in self._tasks.values()
            if task.status == TaskStatus.PENDING
        ]
        
        if not candidates:
            return None
        
        # Filter by agent if specified
        if agent:
            filtered = []
            for task in candidates:
                if task.assigned_agent == "ANY" or task.assigned_agent == agent:
                    filtered.append(task)
            candidates = filtered
        
        if not candidates:
            return None
        
        # Sort by priority score and return best
        candidates.sort(key=lambda t: t.calculate_score())
        return candidates[0]
    
    def get_queue(
        self,
        status: Optional[TaskStatus] = None,
        agent: Optional[str] = None,
        category: Optional[TaskCategory] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 50
    ) -> List[Task]:
        """
        Get tasks from queue with optional filters.
        
        Args:
            status: Filter by status
            agent: Filter by assigned agent
            category: Filter by category
            priority: Filter by priority level
            limit: Maximum tasks to return
            
        Returns:
            List of tasks sorted by priority score
        """
        self._update_blocked_status()
        
        tasks = list(self._tasks.values())
        
        # Apply filters
        if status:
            tasks = [t for t in tasks if t.status == status]
        if agent:
            tasks = [t for t in tasks if t.assigned_agent == agent or t.assigned_agent == "ANY"]
        if category:
            tasks = [t for t in tasks if t.category == category]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        
        # Sort by priority score
        tasks.sort(key=lambda t: t.calculate_score())
        
        return tasks[:limit]
    
    def get_pending(self, limit: int = 50) -> List[Task]:
        """Get all pending tasks sorted by priority."""
        return self.get_queue(status=TaskStatus.PENDING, limit=limit)
    
    def get_in_progress(self) -> List[Task]:
        """Get all in-progress tasks."""
        return self.get_queue(status=TaskStatus.IN_PROGRESS, limit=100)
    
    def get_blocked(self) -> List[Task]:
        """Get all blocked tasks."""
        return self.get_queue(status=TaskStatus.BLOCKED, limit=100)
    
    def get_completed(self, limit: int = 50) -> List[Task]:
        """Get recently completed tasks."""
        tasks = self.get_queue(status=TaskStatus.COMPLETED, limit=limit)
        # Sort by completion time (most recent first)
        tasks.sort(key=lambda t: t.completed_at or "", reverse=True)
        return tasks
    
    def search(self, query: str, limit: int = 50) -> List[Task]:
        """
        Search tasks by title, description, or tags.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Matching tasks sorted by relevance
        """
        query_lower = query.lower()
        results = []
        
        for task in self._tasks.values():
            score = 0
            
            # Title match (highest weight)
            if query_lower in task.title.lower():
                score += 10
            
            # Description match
            if query_lower in task.description.lower():
                score += 5
            
            # Tag match
            for tag in task.tags:
                if query_lower in tag.lower():
                    score += 3
            
            # Notes match
            if query_lower in task.notes.lower():
                score += 2
            
            if score > 0:
                results.append((score, task))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[0], reverse=True)
        return [task for _, task in results[:limit]]
    
    def reorder(self) -> List[Task]:
        """
        Manually trigger queue reordering.
        
        Returns:
            Reordered list of pending tasks
        """
        self._update_blocked_status()
        return self.get_pending()
    
    # ========================================================================
    # AGENT MANAGEMENT
    # ========================================================================
    
    def set_agent_available(self, agent: str, available: bool = True) -> bool:
        """
        Set an agent's availability status.
        
        Args:
            agent: Agent name
            available: Whether agent is available
            
        Returns:
            True if updated, False if agent not found
        """
        with self._lock:
            if agent not in self._agents:
                return False
            
            self._agents[agent].available = available
            self._agents[agent].last_active = datetime.now().isoformat()
            self._save_data()
            return True
    
    def get_agent_status(self, agent: str) -> Optional[AgentStatus]:
        """Get an agent's current status."""
        return self._agents.get(agent)
    
    def get_available_agents(self) -> List[AgentStatus]:
        """Get all available agents."""
        return [a for a in self._agents.values() if a.available]
    
    def get_agent_tasks(self, agent: str) -> List[Task]:
        """Get all tasks assigned to an agent."""
        return [
            t for t in self._tasks.values()
            if t.assigned_agent == agent and t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
        ]
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue metrics
        """
        tasks = list(self._tasks.values())
        
        by_status = {}
        for status in TaskStatus:
            by_status[status.value] = len([t for t in tasks if t.status == status])
        
        by_priority = {}
        for priority in TaskPriority:
            by_priority[priority.name] = len([t for t in tasks if t.priority == priority])
        
        by_agent = {}
        for agent in AGENTS:
            if agent != "ANY":
                by_agent[agent] = len([t for t in tasks if t.assigned_agent == agent])
        
        # Calculate completion metrics
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.actual_duration]
        avg_duration = sum(t.actual_duration for t in completed) / len(completed) if completed else 0
        
        return {
            "total_tasks": len(tasks),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_agent": by_agent,
            "completed_today": len([
                t for t in tasks
                if t.status == TaskStatus.COMPLETED
                and t.completed_at
                and t.completed_at.startswith(datetime.now().strftime("%Y-%m-%d"))
            ]),
            "avg_completion_minutes": round(avg_duration, 1),
            "blocked_count": by_status.get("BLOCKED", 0),
            "overdue_count": len([
                t for t in tasks
                if t.deadline and datetime.fromisoformat(t.deadline) < datetime.now()
                and t.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]
            ])
        }
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent action history."""
        return self._history[-limit:]
    
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    def clear_completed(self, older_than_days: int = 7) -> int:
        """
        Remove completed tasks older than specified days.
        
        Args:
            older_than_days: Remove tasks completed more than this many days ago
            
        Returns:
            Number of tasks removed
        """
        with self._lock:
            cutoff = datetime.now() - timedelta(days=older_than_days)
            to_remove = []
            
            for task_id, task in self._tasks.items():
                if task.status == TaskStatus.COMPLETED and task.completed_at:
                    try:
                        completed = datetime.fromisoformat(task.completed_at)
                        if completed < cutoff:
                            to_remove.append(task_id)
                    except (ValueError, TypeError):
                        pass
            
            for task_id in to_remove:
                del self._tasks[task_id]
            
            if to_remove:
                self._log_action("CLEAR_COMPLETED", "batch", {"count": len(to_remove)})
                self._save_data()
            
            return len(to_remove)
    
    def export_queue(self, filepath: Optional[Path] = None) -> str:
        """
        Export queue to JSON.
        
        Args:
            filepath: Optional file path (returns JSON string if not provided)
            
        Returns:
            JSON string of queue data
        """
        data = {
            "exported_at": datetime.now().isoformat(),
            "version": VERSION,
            "tasks": {k: v.to_dict() for k, v in self._tasks.items()},
            "agents": {k: v.to_dict() for k, v in self._agents.items()},
            "stats": self.get_stats()
        }
        
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def import_queue(self, data: Dict[str, Any], merge: bool = False) -> int:
        """
        Import tasks from exported data.
        
        Args:
            data: Exported queue data
            merge: If True, merge with existing. If False, replace.
            
        Returns:
            Number of tasks imported
        """
        with self._lock:
            if not merge:
                self._tasks.clear()
            
            tasks_data = data.get("tasks", {})
            count = 0
            
            for task_id, task_dict in tasks_data.items():
                if merge and task_id in self._tasks:
                    continue
                try:
                    self._tasks[task_id] = Task.from_dict(task_dict)
                    count += 1
                except (KeyError, ValueError):
                    continue
            
            self._update_blocked_status()
            self._save_data()
            return count


# ============================================================================
# CLI INTERFACE
# ============================================================================

def format_task(task: Task, verbose: bool = False) -> str:
    """Format a task for display."""
    status_icons = {
        TaskStatus.PENDING: "[PENDING]",
        TaskStatus.IN_PROGRESS: "[ACTIVE]",
        TaskStatus.BLOCKED: "[BLOCKED]",
        TaskStatus.COMPLETED: "[DONE]",
        TaskStatus.CANCELLED: "[CANCEL]",
        TaskStatus.FAILED: "[FAILED]",
    }
    
    priority_icons = {
        TaskPriority.CRITICAL: "[!!!]",
        TaskPriority.HIGH: "[!!]",
        TaskPriority.MEDIUM: "[!]",
        TaskPriority.LOW: "[.]",
        TaskPriority.BACKLOG: "[_]",
    }
    
    icon = status_icons.get(task.status, "[?]")
    pri_icon = priority_icons.get(task.priority, "[?]")
    
    line = f"{icon} {task.id} {pri_icon} {task.title}"
    
    if task.assigned_agent and task.assigned_agent != "ANY":
        line += f" @{task.assigned_agent}"
    
    if task.deadline:
        try:
            deadline = datetime.fromisoformat(task.deadline)
            if deadline < datetime.now():
                line += " [OVERDUE!]"
            else:
                delta = deadline - datetime.now()
                if delta.days > 0:
                    line += f" [Due: {delta.days}d]"
                else:
                    hours = int(delta.total_seconds() / 3600)
                    line += f" [Due: {hours}h]"
        except (ValueError, TypeError):
            pass
    
    if verbose:
        if task.description:
            line += f"\n    Description: {task.description}"
        if task.dependencies:
            line += f"\n    Depends on: {', '.join(task.dependencies)}"
        if task.tags:
            line += f"\n    Tags: {', '.join(task.tags)}"
        line += f"\n    Created: {task.created_at[:19]}"
        if task.notes:
            line += f"\n    Notes: {task.notes}"
    
    return line


def main():
    """CLI entry point."""
    # Fix Windows console encoding
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
    
    parser = argparse.ArgumentParser(
        description='PriorityQueue - Intelligent Task Prioritization for Team Brain',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add "Fix login bug" --priority HIGH --agent ATLAS
  %(prog)s add "Write tests" --depends-on abc123
  %(prog)s list --status PENDING
  %(prog)s next --agent ATLAS
  %(prog)s start abc123 --agent ATLAS
  %(prog)s complete abc123 --notes "Fixed in PR #42"
  %(prog)s stats

For more information: https://github.com/DonkRonk17/PriorityQueue
        """
    )
    
    parser.add_argument('--version', action='version', version=f'PriorityQueue v{VERSION}')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # ADD command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('title', help='Task title')
    add_parser.add_argument('--description', '-d', default='', help='Task description')
    add_parser.add_argument('--priority', '-p', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'BACKLOG'],
                          default='MEDIUM', help='Priority level')
    add_parser.add_argument('--category', '-c', 
                          choices=['DEVELOPMENT', 'DOCUMENTATION', 'TESTING', 'BUGFIX', 'FEATURE',
                                  'RESEARCH', 'COORDINATION', 'MAINTENANCE', 'URGENT', 'OTHER'],
                          default='OTHER', help='Task category')
    add_parser.add_argument('--agent', '-a', choices=AGENTS, default='ANY', help='Assigned agent')
    add_parser.add_argument('--deadline', help='Deadline (ISO format: 2026-01-25T17:00:00)')
    add_parser.add_argument('--depends-on', action='append', default=[], help='Dependency task ID')
    add_parser.add_argument('--tags', nargs='*', default=[], help='Tags')
    add_parser.add_argument('--duration', type=int, default=30, help='Estimated duration (minutes)')
    add_parser.add_argument('--created-by', default='', help='Creator name')
    
    # GET command
    get_parser = subparsers.add_parser('get', help='Get a task by ID')
    get_parser.add_argument('task_id', help='Task ID')
    get_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # LIST command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--status', '-s', choices=['PENDING', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'CANCELLED', 'FAILED'],
                           help='Filter by status')
    list_parser.add_argument('--agent', '-a', choices=AGENTS, help='Filter by agent')
    list_parser.add_argument('--priority', '-p', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'BACKLOG'],
                           help='Filter by priority')
    list_parser.add_argument('--limit', '-n', type=int, default=20, help='Maximum tasks to show')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # NEXT command
    next_parser = subparsers.add_parser('next', help='Get next highest priority task')
    next_parser.add_argument('--agent', '-a', choices=AGENTS, help='For specific agent')
    next_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # START command
    start_parser = subparsers.add_parser('start', help='Start working on a task')
    start_parser.add_argument('task_id', help='Task ID')
    start_parser.add_argument('--agent', '-a', choices=AGENTS, help='Agent starting the task')
    
    # COMPLETE command
    complete_parser = subparsers.add_parser('complete', help='Mark task as completed')
    complete_parser.add_argument('task_id', help='Task ID')
    complete_parser.add_argument('--notes', '-n', default='', help='Completion notes')
    
    # FAIL command
    fail_parser = subparsers.add_parser('fail', help='Mark task as failed')
    fail_parser.add_argument('task_id', help='Task ID')
    fail_parser.add_argument('--reason', '-r', default='', help='Failure reason')
    
    # CANCEL command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel a task')
    cancel_parser.add_argument('task_id', help='Task ID')
    cancel_parser.add_argument('--reason', '-r', default='', help='Cancellation reason')
    
    # DELETE command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('task_id', help='Task ID')
    
    # UPDATE command
    update_parser = subparsers.add_parser('update', help='Update a task')
    update_parser.add_argument('task_id', help='Task ID')
    update_parser.add_argument('--title', help='New title')
    update_parser.add_argument('--description', '-d', help='New description')
    update_parser.add_argument('--priority', '-p', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'BACKLOG'],
                              help='New priority')
    update_parser.add_argument('--agent', '-a', choices=AGENTS, help='New assigned agent')
    update_parser.add_argument('--deadline', help='New deadline')
    update_parser.add_argument('--notes', '-n', help='New notes')
    
    # DEPEND command
    depend_parser = subparsers.add_parser('depend', help='Add dependency')
    depend_parser.add_argument('task_id', help='Task ID to add dependency to')
    depend_parser.add_argument('depends_on', help='Task ID that must complete first')
    
    # SEARCH command
    search_parser = subparsers.add_parser('search', help='Search tasks')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', '-n', type=int, default=20, help='Maximum results')
    search_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # STATS command
    stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
    
    # AGENTS command
    agents_parser = subparsers.add_parser('agents', help='Show agent status')
    
    # EXPORT command
    export_parser = subparsers.add_parser('export', help='Export queue to JSON')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    # IMPORT command
    import_parser = subparsers.add_parser('import', help='Import tasks from JSON')
    import_parser.add_argument('file', help='JSON file to import')
    import_parser.add_argument('--merge', action='store_true', help='Merge with existing tasks')
    
    # CLEAR command
    clear_parser = subparsers.add_parser('clear', help='Clear completed tasks')
    clear_parser.add_argument('--older-than', type=int, default=7, help='Days old to clear')
    
    # HISTORY command
    history_parser = subparsers.add_parser('history', help='Show action history')
    history_parser.add_argument('--limit', '-n', type=int, default=20, help='Maximum entries')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Initialize queue
    queue = PriorityQueue()
    
    # Handle commands
    if args.command == 'add':
        task_id = queue.add(
            title=args.title,
            description=args.description,
            priority=TaskPriority[args.priority],
            category=TaskCategory[args.category],
            assigned_agent=args.agent,
            deadline=args.deadline,
            dependencies=args.depends_on,
            tags=args.tags,
            estimated_duration=args.duration,
            created_by=args.created_by
        )
        print(f"[OK] Task created: {task_id}")
        print(f"     Title: {args.title}")
        print(f"     Priority: {args.priority}")
        if args.depends_on:
            print(f"     Depends on: {', '.join(args.depends_on)}")
        return 0
    
    elif args.command == 'get':
        task = queue.get(args.task_id)
        if not task:
            print(f"[X] Task not found: {args.task_id}")
            return 1
        print(format_task(task, verbose=args.verbose))
        return 0
    
    elif args.command == 'list':
        status = TaskStatus[args.status] if args.status else None
        priority = TaskPriority[args.priority] if args.priority else None
        
        tasks = queue.get_queue(
            status=status,
            agent=args.agent,
            priority=priority,
            limit=args.limit
        )
        
        if not tasks:
            print("No tasks found matching criteria.")
            return 0
        
        print(f"Found {len(tasks)} task(s):\n")
        for task in tasks:
            print(format_task(task, verbose=args.verbose))
        return 0
    
    elif args.command == 'next':
        task = queue.get_next(agent=args.agent)
        if not task:
            print("No tasks available.")
            return 0
        print("Next task:\n")
        print(format_task(task, verbose=args.verbose))
        return 0
    
    elif args.command == 'start':
        if queue.start(args.task_id, args.agent):
            print(f"[OK] Task started: {args.task_id}")
            if args.agent:
                print(f"     Agent: {args.agent}")
            return 0
        else:
            print(f"[X] Could not start task: {args.task_id}")
            print("    (Task may be blocked or not found)")
            return 1
    
    elif args.command == 'complete':
        if queue.complete(args.task_id, args.notes):
            print(f"[OK] Task completed: {args.task_id}")
            return 0
        else:
            print(f"[X] Task not found: {args.task_id}")
            return 1
    
    elif args.command == 'fail':
        if queue.fail(args.task_id, args.reason):
            print(f"[OK] Task marked as failed: {args.task_id}")
            return 0
        else:
            print(f"[X] Task not found: {args.task_id}")
            return 1
    
    elif args.command == 'cancel':
        if queue.cancel(args.task_id, args.reason):
            print(f"[OK] Task cancelled: {args.task_id}")
            return 0
        else:
            print(f"[X] Task not found: {args.task_id}")
            return 1
    
    elif args.command == 'delete':
        if queue.delete(args.task_id):
            print(f"[OK] Task deleted: {args.task_id}")
            return 0
        else:
            print(f"[X] Task not found: {args.task_id}")
            return 1
    
    elif args.command == 'update':
        priority = TaskPriority[args.priority] if args.priority else None
        if queue.update(
            args.task_id,
            title=args.title,
            description=args.description,
            priority=priority,
            assigned_agent=args.agent,
            deadline=args.deadline,
            notes=args.notes
        ):
            print(f"[OK] Task updated: {args.task_id}")
            return 0
        else:
            print(f"[X] Task not found: {args.task_id}")
            return 1
    
    elif args.command == 'depend':
        if queue.add_dependency(args.task_id, args.depends_on):
            print(f"[OK] Dependency added: {args.task_id} -> {args.depends_on}")
            return 0
        else:
            print(f"[X] Could not add dependency (circular or not found)")
            return 1
    
    elif args.command == 'search':
        tasks = queue.search(args.query, limit=args.limit)
        if not tasks:
            print(f"No tasks found matching: {args.query}")
            return 0
        print(f"Found {len(tasks)} task(s):\n")
        for task in tasks:
            print(format_task(task, verbose=args.verbose))
        return 0
    
    elif args.command == 'stats':
        stats = queue.get_stats()
        print("=" * 50)
        print("PRIORITYQUEUE STATISTICS")
        print("=" * 50)
        print(f"\nTotal Tasks: {stats['total_tasks']}")
        print(f"Completed Today: {stats['completed_today']}")
        print(f"Blocked: {stats['blocked_count']}")
        print(f"Overdue: {stats['overdue_count']}")
        print(f"Avg Completion Time: {stats['avg_completion_minutes']} min")
        
        print("\nBy Status:")
        for status, count in stats['by_status'].items():
            if count > 0:
                print(f"  {status}: {count}")
        
        print("\nBy Priority:")
        for priority, count in stats['by_priority'].items():
            if count > 0:
                print(f"  {priority}: {count}")
        
        print("\nBy Agent:")
        for agent, count in stats['by_agent'].items():
            if count > 0:
                print(f"  {agent}: {count}")
        
        print("=" * 50)
        return 0
    
    elif args.command == 'agents':
        print("=" * 50)
        print("TEAM BRAIN AGENT STATUS")
        print("=" * 50)
        for name, status in queue._agents.items():
            avail = "[AVAILABLE]" if status.available else "[BUSY]"
            print(f"\n{avail} {name}")
            if status.current_task:
                print(f"  Current Task: {status.current_task}")
            print(f"  Completed Today: {status.completed_today}")
            print(f"  Capabilities: {', '.join(status.capabilities)}")
        print("=" * 50)
        return 0
    
    elif args.command == 'export':
        json_str = queue.export_queue(Path(args.output) if args.output else None)
        if args.output:
            print(f"[OK] Queue exported to: {args.output}")
        else:
            print(json_str)
        return 0
    
    elif args.command == 'import':
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count = queue.import_queue(data, merge=args.merge)
            print(f"[OK] Imported {count} tasks from: {args.file}")
            return 0
        except (IOError, json.JSONDecodeError) as e:
            print(f"[X] Error importing: {e}")
            return 1
    
    elif args.command == 'clear':
        count = queue.clear_completed(args.older_than)
        print(f"[OK] Cleared {count} completed tasks older than {args.older_than} days")
        return 0
    
    elif args.command == 'history':
        history = queue.get_history(args.limit)
        if not history:
            print("No history available.")
            return 0
        print(f"Last {len(history)} actions:\n")
        for entry in reversed(history):
            print(f"  {entry['timestamp'][:19]} | {entry['action']:10} | {entry['task_id']}")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
