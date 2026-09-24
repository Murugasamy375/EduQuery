export type UserRole = 'STUDENT' | 'STAFF' | 'MANAGER' | 'ADMIN';

export type TicketStatus =
  | 'NEW'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'WAITING_FOR_STUDENT'
  | 'RESOLVED'
  | 'CLOSED'
  | 'REOPENED';

export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type SLAStatus = 'ON_TRACK' | 'AT_RISK' | 'BREACHED' | 'PAUSED';

export type PendingReason =
  | 'WAITING_FOR_STUDENT'
  | 'WAITING_FOR_STAFF'
  | 'WAITING_FOR_DEPARTMENT'
  | 'WAITING_FOR_DOCUMENT';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  department?: string;
  student_id_card?: string;
  is_active: boolean;
}

export interface Attachment {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  data_url?: string;
  uploaded_at: string;
}

export interface PendingDetails {
  reason: PendingReason;
  since: string;
  requested_action: string;
  requested_by: string;
}

export interface SLADisplay {
  status: SLAStatus;
  is_breached: boolean;
  is_at_risk: boolean;
  is_paused: boolean;
  remaining_seconds: number;
  overdue_seconds: number;
  display_text: string;
  due_at: string;
}

export interface AgeingDisplay {
  age_seconds: number;
  age_display: string;
  bucket: string;
}

export interface Ticket {
  id: number;
  ticket_number: string;
  student_id: number;
  student_name: string;
  student_email: string;
  category: string;
  subject: string;
  description: string;
  priority: Priority;
  status: TicketStatus;
  department: string;
  assigned_staff_id?: number;
  assigned_staff_name?: string;
  created_at: string;
  updated_at: string;
  sla_due_at: string;
  sla_status: SLAStatus;
  resolved_at?: string;
  closed_at?: string;
  resolution_summary?: string;
  reopen_count: number;
  escalation_count: number;
  is_escalated: boolean;
  pending_details?: PendingDetails;
  attachments: Attachment[];
  sla: SLADisplay;
  ageing: AgeingDisplay;
  last_activity_at?: string;
}

export interface Activity {
  id: number;
  ticket_id: number;
  actor_id: number;
  actor_name: string;
  actor_role: UserRole;
  action: string;
  description: string;
  is_internal: boolean;
  metadata: Record<string, any>;
  created_at: string;
}

export interface NotificationItem {
  id: number;
  user_id: number;
  ticket_id?: number;
  title: string;
  message: string;
  is_read: boolean;
  event_type: string;
  created_at: string;
}

export interface AIClassifyResponse {
  category: string;
  priority: Priority;
  department: string;
  summary: string;
  confidence: number;
  source: string;
}

export interface StudentDashboard {
  my_open_tickets: number;
  in_progress: number;
  waiting_for_response: number;
  resolved: number;
  recent_tickets: Ticket[];
}

export interface StaffWorkloadItem {
  staff_id: number;
  name: string;
  active_tickets: number;
  breached_tickets: number;
}

export interface StaffDashboard {
  my_open_tickets: number;
  due_soon: number;
  sla_breached: number;
  waiting_for_student: number;
  workload: StaffWorkloadItem[];
  priority_distribution: Record<string, number>;
  oldest_tickets: Ticket[];
  recently_assigned: Ticket[];
}

export interface ManagerDashboard {
  total_open: number;
  unassigned: number;
  sla_at_risk: number;
  sla_breached: number;
  escalated: number;
  avg_resolution_hours: number;
  tickets_by_category: Record<string, number>;
  tickets_by_priority: Record<string, number>;
  tickets_by_status: Record<string, number>;
  staff_workload: StaffWorkloadItem[];
  ageing_distribution: Record<string, number>;
  oldest_unresolved_tickets: Ticket[];
}
