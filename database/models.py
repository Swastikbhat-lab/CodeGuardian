"""
Database models for CodeGuardian

SQLAlchemy models for storing review data, issues, tests, and fixes.
"""
from datetime import datetime
from typing import List
import enum
import uuid

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy import Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()


# ============================================
# ENUMS
# ============================================
class ReviewStatus(str, enum.Enum):
    """Status of a code review"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IssueSeverity(str, enum.Enum):
    """Severity levels for issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, enum.Enum):
    """Categories of issues"""
    SECURITY = "security"
    LOGIC = "logic"
    STYLE = "style"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DUPLICATION = "duplication"
    COMPLEXITY = "complexity"


# ============================================
# MODELS
# ============================================
class CodeReview(Base):
    """
    Main code review record
    
    Tracks the overall review process and metadata
    """
    __tablename__ = "code_reviews"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source information
    repository_url = Column(String(500), nullable=True)
    branch = Column(String(100), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    pr_number = Column(Integer, nullable=True)
    
    # Review metadata
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Agent execution
    agents_used = Column(JSON)  # ["static_analysis", "security", ...]
    execution_plan = Column(JSON)  # Coordinator's plan
    
    # Metrics
    files_analyzed = Column(Integer, default=0)
    lines_of_code = Column(Integer, default=0)
    time_taken_seconds = Column(Float, nullable=True)
    total_cost = Column(Float, default=0.0)
    
    # Coverage metrics
    coverage_before = Column(Float, nullable=True)  # 0.0 to 1.0
    coverage_after = Column(Float, nullable=True)
    
    # Observability
    langfuse_trace_id = Column(String(100), nullable=True)
    
    # User (for multi-user setup)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    issues = relationship("Issue", back_populates="review", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="review", cascade="all, delete-orphan")
    fixes = relationship("Fix", back_populates="review", cascade="all, delete-orphan")
    metrics = relationship("AgentMetric", back_populates="review", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CodeReview {self.id} status={self.status}>"
    
    @property
    def duration_minutes(self) -> float:
        """Get review duration in minutes"""
        if self.time_taken_seconds:
            return round(self.time_taken_seconds / 60, 2)
        return 0.0
    
    @property
    def issue_counts(self) -> dict:
        """Get count of issues by severity"""
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return counts


class Issue(Base):
    """
    Code issue found by agents
    
    Represents bugs, vulnerabilities, code smells, etc.
    """
    __tablename__ = "issues"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Issue details
    agent_name = Column(String(50), nullable=False)  # Which agent found it
    severity = Column(SQLEnum(IssueSeverity), nullable=False)
    category = Column(SQLEnum(IssueCategory), nullable=False)
    
    # Location
    file_path = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=False)
    end_line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    
    # Description
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    
    # Metadata
    auto_fixable = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    cwe = Column(String(20), nullable=True)  # For security issues (e.g., "CWE-89")
    tool = Column(String(50), nullable=True)  # pylint, bandit, claude, etc.
    
    # Fix tracking
    fix_applied = Column(Boolean, default=False)
    fix_id = Column(UUID(as_uuid=True), ForeignKey("fixes.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    review = relationship("CodeReview", back_populates="issues")
    fix = relationship("Fix", foreign_keys=[fix_id], post_update=True)
    
    def __repr__(self):
        return f"<Issue {self.id} {self.severity} {self.category}>"


class Test(Base):
    """
    Generated test file
    
    Tracks tests created by the test generation agent
    """
    __tablename__ = "tests"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Test file info
    original_file_path = Column(String(500), nullable=False)
    test_file_path = Column(String(500), nullable=False)
    test_code = Column(Text, nullable=False)
    
    # Metadata
    test_framework = Column(String(50), default="pytest")
    functions_tested = Column(JSON)  # ["func1", "func2", ...]
    test_count = Column(Integer, nullable=True)
    
    # Coverage
    coverage_increase = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Execution results
    passed = Column(Boolean, nullable=True)
    failed = Column(Integer, default=0)
    execution_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    review = relationship("CodeReview", back_populates="tests")
    
    def __repr__(self):
        return f"<Test {self.id} {self.test_file_path}>"


class Fix(Base):
    """
    Generated code fix
    
    Tracks fixes created by the fix implementation agent
    """
    __tablename__ = "fixes"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    issue_id = Column(UUID(as_uuid=True), nullable=True)  # May fix multiple issues
    
    # Fix details
    file_path = Column(String(500), nullable=False)
    original_code = Column(Text, nullable=False)
    fixed_code = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    
    # Patch (git-style diff)
    patch = Column(Text, nullable=True)
    
    # Validation
    validation_status = Column(String(20), nullable=True)  # passed_tests, failed_tests, not_tested
    
    # Application
    auto_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    applied_by = Column(String(100), nullable=True)  # 'system' or user_id
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    review = relationship("CodeReview", back_populates="fixes")
    
    def __repr__(self):
        return f"<Fix {self.id} {self.file_path}>"


class AgentMetric(Base):
    """
    Metrics for agent execution
    
    Tracks performance, cost, and quality for each agent
    """
    __tablename__ = "agent_metrics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Agent info
    agent_name = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Resource usage
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    model_used = Column(String(100), nullable=True)
    
    # Results
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    items_processed = Column(Integer, nullable=True)  # Files, tests, etc.
    
    # Quality
    output_quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Observability
    langfuse_trace_id = Column(String(100), nullable=True)
    langfuse_observation_id = Column(String(100), nullable=True)
    
    # Relationships
    review = relationship("CodeReview", back_populates="metrics")
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds()
        return 0.0
    
    def __repr__(self):
        return f"<AgentMetric {self.agent_name} {self.duration_seconds:.2f}s>"


class UserFeedback(Base):
    """
    User feedback on reviews
    
    Tracks user satisfaction and false positives to improve quality
    """
    __tablename__ = "user_feedback"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=True)
    fix_id = Column(UUID(as_uuid=True), ForeignKey("fixes.id"), nullable=True)
    
    # Feedback
    is_helpful = Column(Boolean, nullable=False)
    is_false_positive = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5
    
    # User
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserFeedback {self.id} helpful={self.is_helpful}>"
