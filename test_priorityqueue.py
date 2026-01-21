#!/usr/bin/env python3
"""
Comprehensive test suite for PriorityQueue.

Tests cover:
- Task creation and management
- Priority scoring and ordering
- Dependency tracking and blocking
- Agent availability management
- Queue operations (get_next, reorder)
- Search functionality
- Status transitions
- Statistics and history
- Import/export functionality
- Edge cases and error handling

Run: python test_priorityqueue.py
"""

import unittest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from priorityqueue import (
    PriorityQueue,
    Task,
    TaskStatus,
    TaskPriority,
    TaskCategory,
    AgentStatus,
    AGENTS,
    VERSION
)


class TestTaskBasics(unittest.TestCase):
    """Test basic Task functionality."""
    
    def test_task_creation(self):
        """Test creating a task with required fields."""
        task = Task(id="test123", title="Test Task")
        self.assertEqual(task.id, "test123")
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, TaskPriority.MEDIUM)
    
    def test_task_with_all_fields(self):
        """Test creating a task with all fields."""
        task = Task(
            id="full123",
            title="Full Task",
            description="A complete task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            category=TaskCategory.DEVELOPMENT,
            assigned_agent="ATLAS",
            deadline="2026-01-25T17:00:00",
            dependencies=["dep1", "dep2"],
            tags=["urgent", "bugfix"],
            estimated_duration=60,
            notes="Important task"
        )
        self.assertEqual(task.description, "A complete task")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.assigned_agent, "ATLAS")
        self.assertEqual(len(task.dependencies), 2)
        self.assertEqual(len(task.tags), 2)
    
    def test_task_to_dict(self):
        """Test task serialization."""
        task = Task(id="dict123", title="Dict Test", priority=TaskPriority.HIGH)
        data = task.to_dict()
        self.assertEqual(data['id'], "dict123")
        self.assertEqual(data['priority'], 2)  # HIGH = 2
        self.assertEqual(data['status'], "PENDING")
    
    def test_task_from_dict(self):
        """Test task deserialization."""
        data = {
            'id': 'from123',
            'title': 'From Dict',
            'status': 'COMPLETED',
            'priority': 1,  # CRITICAL
            'category': 'BUGFIX'
        }
        task = Task.from_dict(data)
        self.assertEqual(task.id, 'from123')
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.priority, TaskPriority.CRITICAL)
        self.assertEqual(task.category, TaskCategory.BUGFIX)


class TestPriorityScoring(unittest.TestCase):
    """Test priority scoring calculations."""
    
    def test_base_priority_order(self):
        """Test that base priorities are ordered correctly."""
        critical = Task(id="c1", title="Critical", priority=TaskPriority.CRITICAL)
        high = Task(id="h1", title="High", priority=TaskPriority.HIGH)
        medium = Task(id="m1", title="Medium", priority=TaskPriority.MEDIUM)
        low = Task(id="l1", title="Low", priority=TaskPriority.LOW)
        backlog = Task(id="b1", title="Backlog", priority=TaskPriority.BACKLOG)
        
        # Lower score = higher priority
        self.assertLess(critical.calculate_score(), high.calculate_score())
        self.assertLess(high.calculate_score(), medium.calculate_score())
        self.assertLess(medium.calculate_score(), low.calculate_score())
        self.assertLess(low.calculate_score(), backlog.calculate_score())
    
    def test_urgency_boosts_priority(self):
        """Test that deadline proximity increases priority."""
        now = datetime.now()
        
        # Due in 30 minutes
        urgent = Task(
            id="u1", title="Urgent",
            priority=TaskPriority.MEDIUM,
            deadline=(now + timedelta(minutes=30)).isoformat()
        )
        
        # Due in 3 days
        not_urgent = Task(
            id="nu1", title="Not Urgent",
            priority=TaskPriority.MEDIUM,
            deadline=(now + timedelta(days=3)).isoformat()
        )
        
        # Urgent should have lower score (higher priority)
        self.assertLess(urgent.calculate_score(), not_urgent.calculate_score())
    
    def test_overdue_highest_priority(self):
        """Test that overdue tasks get highest priority."""
        now = datetime.now()
        
        # Overdue
        overdue = Task(
            id="od1", title="Overdue",
            priority=TaskPriority.LOW,  # Even low priority
            deadline=(now - timedelta(hours=1)).isoformat()
        )
        
        # High priority but not due yet
        high = Task(
            id="hp1", title="High Priority",
            priority=TaskPriority.HIGH,
            deadline=(now + timedelta(days=7)).isoformat()
        )
        
        # Overdue should still have lower score
        self.assertLess(overdue.calculate_score(), high.calculate_score())
    
    def test_blocked_tasks_deprioritized(self):
        """Test that blocked tasks have much higher score."""
        normal = Task(id="n1", title="Normal", priority=TaskPriority.HIGH)
        blocked = Task(id="b1", title="Blocked", priority=TaskPriority.HIGH, status=TaskStatus.BLOCKED)
        
        # Blocked should have much higher score (lower priority)
        self.assertGreater(blocked.calculate_score(), normal.calculate_score() * 5)


class TestPriorityQueue(unittest.TestCase):
    """Test PriorityQueue class functionality."""
    
    def setUp(self):
        """Set up test queue with temp directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_add_task(self):
        """Test adding a task."""
        task_id = self.queue.add("Test Task", priority=TaskPriority.HIGH)
        self.assertIsNotNone(task_id)
        self.assertEqual(len(task_id), 8)  # Short UUID
        
        task = self.queue.get(task_id)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.priority, TaskPriority.HIGH)
    
    def test_add_task_with_options(self):
        """Test adding a task with all options."""
        task_id = self.queue.add(
            "Full Task",
            description="Complete description",
            priority=TaskPriority.CRITICAL,
            category=TaskCategory.BUGFIX,
            assigned_agent="ATLAS",
            tags=["urgent", "fix"],
            estimated_duration=120
        )
        
        task = self.queue.get(task_id)
        self.assertEqual(task.description, "Complete description")
        self.assertEqual(task.category, TaskCategory.BUGFIX)
        self.assertEqual(task.assigned_agent, "ATLAS")
        self.assertIn("urgent", task.tags)
    
    def test_get_task(self):
        """Test getting a task by ID."""
        task_id = self.queue.add("Get Test")
        
        task = self.queue.get(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.title, "Get Test")
        
        # Non-existent
        missing = self.queue.get("nonexistent")
        self.assertIsNone(missing)
    
    def test_update_task(self):
        """Test updating a task."""
        task_id = self.queue.add("Original", priority=TaskPriority.LOW)
        
        result = self.queue.update(
            task_id,
            title="Updated",
            priority=TaskPriority.HIGH,
            notes="Changed"
        )
        self.assertTrue(result)
        
        task = self.queue.get(task_id)
        self.assertEqual(task.title, "Updated")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.notes, "Changed")
    
    def test_update_nonexistent(self):
        """Test updating non-existent task."""
        result = self.queue.update("nonexistent", title="New")
        self.assertFalse(result)
    
    def test_delete_task(self):
        """Test deleting a task."""
        task_id = self.queue.add("Delete Me")
        
        result = self.queue.delete(task_id)
        self.assertTrue(result)
        
        task = self.queue.get(task_id)
        self.assertIsNone(task)
        
        # Delete again should fail
        result = self.queue.delete(task_id)
        self.assertFalse(result)


class TestStatusTransitions(unittest.TestCase):
    """Test task status transitions."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_start_task(self):
        """Test starting a task."""
        task_id = self.queue.add("Start Test")
        
        result = self.queue.start(task_id, "ATLAS")
        self.assertTrue(result)
        
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task.assigned_agent, "ATLAS")
        self.assertIsNotNone(task.started_at)
    
    def test_start_blocked_task_fails(self):
        """Test that starting a blocked task fails."""
        dep_id = self.queue.add("Dependency")
        task_id = self.queue.add("Depends", dependencies=[dep_id])
        
        # Task should be blocked
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.BLOCKED)
        
        # Starting should fail
        result = self.queue.start(task_id)
        self.assertFalse(result)
    
    def test_complete_task(self):
        """Test completing a task."""
        task_id = self.queue.add("Complete Test")
        self.queue.start(task_id, "ATLAS")
        
        result = self.queue.complete(task_id, "All done!")
        self.assertTrue(result)
        
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.notes, "All done!")
    
    def test_fail_task(self):
        """Test failing a task."""
        task_id = self.queue.add("Fail Test")
        self.queue.start(task_id)
        
        result = self.queue.fail(task_id, "Something went wrong")
        self.assertTrue(result)
        
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIn("FAILED:", task.notes)
    
    def test_cancel_task(self):
        """Test cancelling a task."""
        task_id = self.queue.add("Cancel Test")
        
        result = self.queue.cancel(task_id, "No longer needed")
        self.assertTrue(result)
        
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.CANCELLED)
        self.assertIn("CANCELLED:", task.notes)


class TestDependencies(unittest.TestCase):
    """Test dependency tracking."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_task_blocked_by_dependency(self):
        """Test that tasks with incomplete deps are blocked."""
        dep_id = self.queue.add("Dependency Task")
        task_id = self.queue.add("Main Task", dependencies=[dep_id])
        
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.BLOCKED)
    
    def test_task_unblocked_when_dep_completes(self):
        """Test that completing dependency unblocks task."""
        dep_id = self.queue.add("Dependency")
        task_id = self.queue.add("Waiting", dependencies=[dep_id])
        
        # Initially blocked
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.BLOCKED)
        
        # Complete dependency
        self.queue.start(dep_id)
        self.queue.complete(dep_id)
        
        # Now should be pending
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.PENDING)
    
    def test_add_dependency(self):
        """Test adding dependency to existing task."""
        dep_id = self.queue.add("Dependency")
        task_id = self.queue.add("Main Task")  # No dependency initially
        
        # Should be pending
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.PENDING)
        
        # Add dependency
        result = self.queue.add_dependency(task_id, dep_id)
        self.assertTrue(result)
        
        # Should now be blocked
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.BLOCKED)
        self.assertIn(dep_id, task.dependencies)
    
    def test_circular_dependency_prevented(self):
        """Test that circular dependencies are prevented."""
        task_a = self.queue.add("Task A")
        task_b = self.queue.add("Task B", dependencies=[task_a])
        
        # Trying to make A depend on B should fail (circular)
        result = self.queue.add_dependency(task_a, task_b)
        self.assertFalse(result)
    
    def test_remove_dependency(self):
        """Test removing a dependency."""
        dep_id = self.queue.add("Dependency")
        task_id = self.queue.add("Main", dependencies=[dep_id])
        
        # Remove dependency
        result = self.queue.remove_dependency(task_id, dep_id)
        self.assertTrue(result)
        
        # Should now be pending
        task = self.queue.get(task_id)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertNotIn(dep_id, task.dependencies)


class TestQueueOperations(unittest.TestCase):
    """Test queue operations."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_get_next(self):
        """Test getting next highest priority task."""
        low = self.queue.add("Low Priority", priority=TaskPriority.LOW)
        high = self.queue.add("High Priority", priority=TaskPriority.HIGH)
        critical = self.queue.add("Critical", priority=TaskPriority.CRITICAL)
        
        next_task = self.queue.get_next()
        self.assertEqual(next_task.id, critical)
    
    def test_get_next_for_agent(self):
        """Test getting next task for specific agent."""
        self.queue.add("Any Task", assigned_agent="ANY")
        atlas_id = self.queue.add("Atlas Task", assigned_agent="ATLAS")
        forge_id = self.queue.add("Forge Task", assigned_agent="FORGE")
        
        # Atlas should get atlas task or any task
        atlas_task = self.queue.get_next(agent="ATLAS")
        self.assertIn(atlas_task.assigned_agent, ["ATLAS", "ANY"])
        
        # Forge should not get atlas task
        forge_task = self.queue.get_next(agent="FORGE")
        self.assertNotEqual(forge_task.assigned_agent, "ATLAS")
    
    def test_get_next_empty_queue(self):
        """Test get_next on empty queue."""
        result = self.queue.get_next()
        self.assertIsNone(result)
    
    def test_get_queue_with_filters(self):
        """Test getting queue with various filters."""
        self.queue.add("Pending 1")
        self.queue.add("Pending 2", priority=TaskPriority.HIGH)
        task_id = self.queue.add("In Progress")
        self.queue.start(task_id)
        
        # Filter by status
        pending = self.queue.get_queue(status=TaskStatus.PENDING)
        self.assertEqual(len(pending), 2)
        
        in_progress = self.queue.get_queue(status=TaskStatus.IN_PROGRESS)
        self.assertEqual(len(in_progress), 1)
        
        # Filter by priority
        high = self.queue.get_queue(priority=TaskPriority.HIGH)
        self.assertEqual(len(high), 1)
    
    def test_get_pending(self):
        """Test get_pending helper."""
        self.queue.add("Task 1")
        self.queue.add("Task 2")
        task_id = self.queue.add("Task 3")
        self.queue.start(task_id)
        
        pending = self.queue.get_pending()
        self.assertEqual(len(pending), 2)
    
    def test_search(self):
        """Test search functionality."""
        self.queue.add("Login bug fix", description="Fix the login button")
        self.queue.add("Signup feature", tags=["frontend", "auth"])
        self.queue.add("Database migration")
        
        # Search by title
        results = self.queue.search("login")
        self.assertEqual(len(results), 1)
        self.assertIn("Login", results[0].title)
        
        # Search by tags
        results = self.queue.search("auth")
        self.assertEqual(len(results), 1)
        
        # Search by description
        results = self.queue.search("button")
        self.assertEqual(len(results), 1)


class TestAgentManagement(unittest.TestCase):
    """Test agent availability management."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_default_agents_initialized(self):
        """Test that default agents are created."""
        status = self.queue.get_agent_status("FORGE")
        self.assertIsNotNone(status)
        self.assertTrue(status.available)
    
    def test_set_agent_available(self):
        """Test setting agent availability."""
        result = self.queue.set_agent_available("ATLAS", False)
        self.assertTrue(result)
        
        status = self.queue.get_agent_status("ATLAS")
        self.assertFalse(status.available)
    
    def test_agent_busy_when_working(self):
        """Test that agent becomes busy when starting task."""
        task_id = self.queue.add("Test Task")
        self.queue.start(task_id, "ATLAS")
        
        status = self.queue.get_agent_status("ATLAS")
        self.assertFalse(status.available)
        self.assertEqual(status.current_task, task_id)
    
    def test_agent_free_when_complete(self):
        """Test that agent becomes free when completing task."""
        task_id = self.queue.add("Test Task")
        self.queue.start(task_id, "ATLAS")
        self.queue.complete(task_id)
        
        status = self.queue.get_agent_status("ATLAS")
        self.assertTrue(status.available)
        self.assertIsNone(status.current_task)
        self.assertEqual(status.completed_today, 1)
    
    def test_get_available_agents(self):
        """Test getting available agents."""
        # All should be available initially
        available = self.queue.get_available_agents()
        self.assertGreater(len(available), 0)
        
        # Make one busy
        task_id = self.queue.add("Test")
        self.queue.start(task_id, "ATLAS")
        
        available = self.queue.get_available_agents()
        atlas_available = any(a.name == "ATLAS" for a in available)
        self.assertFalse(atlas_available)
    
    def test_get_agent_tasks(self):
        """Test getting tasks for an agent."""
        self.queue.add("Atlas Task 1", assigned_agent="ATLAS")
        self.queue.add("Atlas Task 2", assigned_agent="ATLAS")
        self.queue.add("Forge Task", assigned_agent="FORGE")
        
        atlas_tasks = self.queue.get_agent_tasks("ATLAS")
        self.assertEqual(len(atlas_tasks), 2)


class TestStatistics(unittest.TestCase):
    """Test statistics functionality."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_get_stats(self):
        """Test getting queue statistics."""
        self.queue.add("Task 1", priority=TaskPriority.HIGH)
        self.queue.add("Task 2", priority=TaskPriority.LOW)
        task_id = self.queue.add("Task 3")
        self.queue.start(task_id)
        self.queue.complete(task_id)
        
        stats = self.queue.get_stats()
        
        self.assertEqual(stats['total_tasks'], 3)
        self.assertEqual(stats['by_status']['PENDING'], 2)
        self.assertEqual(stats['by_status']['COMPLETED'], 1)
        self.assertEqual(stats['by_priority']['HIGH'], 1)
        self.assertEqual(stats['completed_today'], 1)
    
    def test_history(self):
        """Test action history."""
        task_id = self.queue.add("Test")
        self.queue.start(task_id)
        self.queue.complete(task_id)
        
        history = self.queue.get_history()
        
        actions = [entry['action'] for entry in history]
        self.assertIn('ADD', actions)
        self.assertIn('START', actions)
        self.assertIn('COMPLETE', actions)


class TestImportExport(unittest.TestCase):
    """Test import/export functionality."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_export_queue(self):
        """Test exporting queue to JSON."""
        self.queue.add("Task 1")
        self.queue.add("Task 2")
        
        json_str = self.queue.export_queue()
        data = json.loads(json_str)
        
        self.assertIn('tasks', data)
        self.assertIn('agents', data)
        self.assertIn('stats', data)
        self.assertEqual(len(data['tasks']), 2)
    
    def test_export_to_file(self):
        """Test exporting to file."""
        self.queue.add("Task 1")
        
        export_path = self.temp_dir / "export.json"
        self.queue.export_queue(export_path)
        
        self.assertTrue(export_path.exists())
        
        with open(export_path) as f:
            data = json.load(f)
        self.assertIn('tasks', data)
    
    def test_import_queue(self):
        """Test importing queue from data."""
        # Create export data
        self.queue.add("Original Task")
        json_str = self.queue.export_queue()
        data = json.loads(json_str)
        
        # Create new queue and import
        new_dir = Path(tempfile.mkdtemp())
        try:
            new_queue = PriorityQueue(config_dir=new_dir)
            count = new_queue.import_queue(data)
            
            self.assertEqual(count, 1)
            tasks = new_queue.get_pending()
            self.assertEqual(len(tasks), 1)
        finally:
            shutil.rmtree(new_dir)
    
    def test_import_merge(self):
        """Test importing with merge."""
        task_id = self.queue.add("Existing Task")
        
        # Create import data with different tasks
        import_data = {
            'tasks': {
                'new123': {
                    'id': 'new123',
                    'title': 'Imported Task',
                    'status': 'PENDING',
                    'priority': 3,
                    'category': 'OTHER',
                    'dependencies': [],
                    'tags': [],
                    'assigned_agent': 'ANY',
                    'created_by': '',
                    'created_at': datetime.now().isoformat(),
                    'estimated_duration': 30,
                    'metadata': {}
                }
            }
        }
        
        count = self.queue.import_queue(import_data, merge=True)
        
        self.assertEqual(count, 1)
        # Should have both tasks
        pending = self.queue.get_pending()
        self.assertEqual(len(pending), 2)


class TestClearCompleted(unittest.TestCase):
    """Test clearing completed tasks."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_clear_completed(self):
        """Test clearing completed tasks."""
        # Add and complete tasks
        task1 = self.queue.add("Task 1")
        task2 = self.queue.add("Task 2")
        task3 = self.queue.add("Task 3 (pending)")
        
        self.queue.start(task1)
        self.queue.complete(task1)
        self.queue.start(task2)
        self.queue.complete(task2)
        
        # Manually set old completion date
        self.queue._tasks[task1].completed_at = (datetime.now() - timedelta(days=10)).isoformat()
        self.queue._tasks[task2].completed_at = (datetime.now() - timedelta(days=3)).isoformat()
        self.queue._save_data()
        
        # Clear tasks older than 7 days
        count = self.queue.clear_completed(older_than_days=7)
        
        self.assertEqual(count, 1)  # Only task1 should be cleared
        self.assertIsNone(self.queue.get(task1))
        self.assertIsNotNone(self.queue.get(task2))
        self.assertIsNotNone(self.queue.get(task3))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test queue."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.queue = PriorityQueue(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
    
    def test_empty_queue_operations(self):
        """Test operations on empty queue."""
        self.assertIsNone(self.queue.get_next())
        self.assertEqual(len(self.queue.get_pending()), 0)
        self.assertEqual(len(self.queue.search("anything")), 0)
    
    def test_operations_on_nonexistent_tasks(self):
        """Test operations on non-existent tasks."""
        self.assertIsNone(self.queue.get("nonexistent"))
        self.assertFalse(self.queue.update("nonexistent", title="New"))
        self.assertFalse(self.queue.delete("nonexistent"))
        self.assertFalse(self.queue.start("nonexistent"))
        self.assertFalse(self.queue.complete("nonexistent"))
        self.assertFalse(self.queue.fail("nonexistent"))
        self.assertFalse(self.queue.cancel("nonexistent"))
    
    def test_special_characters_in_title(self):
        """Test tasks with special characters."""
        task_id = self.queue.add("Test [with] special <chars> & symbols!")
        task = self.queue.get(task_id)
        self.assertIn("special", task.title)
    
    def test_empty_string_fields(self):
        """Test tasks with empty strings."""
        task_id = self.queue.add("")
        task = self.queue.get(task_id)
        self.assertEqual(task.title, "")
    
    def test_very_long_description(self):
        """Test task with very long description."""
        long_desc = "A" * 10000
        task_id = self.queue.add("Long Task", description=long_desc)
        task = self.queue.get(task_id)
        self.assertEqual(len(task.description), 10000)
    
    def test_many_dependencies(self):
        """Test task with many dependencies."""
        deps = []
        for i in range(20):
            dep_id = self.queue.add(f"Dep {i}")
            deps.append(dep_id)
        
        task_id = self.queue.add("Main Task", dependencies=deps)
        task = self.queue.get(task_id)
        self.assertEqual(len(task.dependencies), 20)
        self.assertEqual(task.status, TaskStatus.BLOCKED)
    
    def test_persistence(self):
        """Test that data persists across queue instances."""
        task_id = self.queue.add("Persistent Task")
        
        # Create new queue instance with same directory
        queue2 = PriorityQueue(config_dir=self.temp_dir)
        
        task = queue2.get(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.title, "Persistent Task")
    
    def test_reorder_doesnt_affect_completed(self):
        """Test that reorder only affects pending tasks."""
        task1 = self.queue.add("Task 1")
        task2 = self.queue.add("Task 2")
        self.queue.start(task1)
        self.queue.complete(task1)
        
        reordered = self.queue.reorder()
        
        # Only pending tasks returned
        self.assertEqual(len(reordered), 1)
        self.assertEqual(reordered[0].id, task2)


class TestVersion(unittest.TestCase):
    """Test version constant."""
    
    def test_version_format(self):
        """Test version is proper format."""
        parts = VERSION.split('.')
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit())


def run_tests():
    """Run all tests with nice output."""
    print("=" * 70)
    print("TESTING: PriorityQueue v{}".format(VERSION))
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestTaskBasics,
        TestPriorityScoring,
        TestPriorityQueue,
        TestStatusTransitions,
        TestDependencies,
        TestQueueOperations,
        TestAgentManagement,
        TestStatistics,
        TestImportExport,
        TestClearCompleted,
        TestEdgeCases,
        TestVersion,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"RESULTS: {total} tests")
    print(f"[OK] Passed: {passed}")
    if result.failures:
        print(f"[X] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[X] Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
