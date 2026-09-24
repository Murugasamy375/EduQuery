from enum import Enum

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class TicketStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_STUDENT = "WAITING_FOR_STUDENT"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"

class PendingReason(str, Enum):
    WAITING_FOR_STUDENT = "WAITING_FOR_STUDENT"
    WAITING_FOR_STAFF = "WAITING_FOR_STAFF"
    WAITING_FOR_DEPARTMENT = "WAITING_FOR_DEPARTMENT"
    WAITING_FOR_DOCUMENT = "WAITING_FOR_DOCUMENT"

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class SLAStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    BREACHED = "BREACHED"
    PAUSED = "PAUSED"

class Category(str, Enum):
    FEES = "Fees"
    ATTENDANCE = "Attendance"
    ID_CARD = "ID Card"
    DOCUMENTS = "Documents"
    CERTIFICATES = "Certificates"
    GENERAL_ADMIN = "General Administration"

class Department(str, Enum):
    FINANCE = "Finance"
    ACADEMIC = "Academic Affairs"
    REGISTRAR = "Registrar & Student Records"
    ADMINISTRATION = "Campus Administration"
    STUDENT_SERVICES = "Student Support Services"

class ActivityAction(str, Enum):
    TICKET_CREATED = "TICKET_CREATED"
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    TICKET_REASSIGNED = "TICKET_REASSIGNED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"
    STATUS_CHANGED = "STATUS_CHANGED"
    STUDENT_REPLIED = "STUDENT_REPLIED"
    STAFF_REPLIED = "STAFF_REPLIED"
    INTERNAL_NOTE_ADDED = "INTERNAL_NOTE_ADDED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    SLA_WARNING = "SLA_WARNING"
    SLA_BREACHED = "SLA_BREACHED"
    TICKET_ESCALATED = "TICKET_ESCALATED"
    TICKET_RESOLVED = "TICKET_RESOLVED"
    TICKET_REOPENED = "TICKET_REOPENED"
    TICKET_CLOSED = "TICKET_CLOSED"

# Valid state transitions mapping
ALLOWED_TRANSITIONS = {
    TicketStatus.NEW: [TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS],
    TicketStatus.ASSIGNED: [TicketStatus.IN_PROGRESS, TicketStatus.WAITING_FOR_STUDENT],
    TicketStatus.IN_PROGRESS: [TicketStatus.WAITING_FOR_STUDENT, TicketStatus.RESOLVED, TicketStatus.ASSIGNED],
    TicketStatus.WAITING_FOR_STUDENT: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED],
    TicketStatus.REOPENED: [TicketStatus.IN_PROGRESS, TicketStatus.ASSIGNED],
    TicketStatus.RESOLVED: [TicketStatus.CLOSED, TicketStatus.REOPENED],
    TicketStatus.CLOSED: []  # Terminal state
}

# SLA Hours per priority
DEFAULT_SLA_HOURS = {
    Priority.LOW: 72,
    Priority.MEDIUM: 48,
    Priority.HIGH: 24,
    Priority.URGENT: 8
}

CATEGORY_DEPARTMENT_MAP = {
    Category.FEES: Department.FINANCE,
    Category.ATTENDANCE: Department.ACADEMIC,
    Category.ID_CARD: Department.REGISTRAR,
    Category.DOCUMENTS: Department.REGISTRAR,
    Category.CERTIFICATES: Department.REGISTRAR,
    Category.GENERAL_ADMIN: Department.ADMINISTRATION
}
