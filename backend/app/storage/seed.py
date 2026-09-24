from datetime import datetime, timedelta
import random
from app.models.schemas import User, Ticket, Activity, Notification, Escalation, SLAPolicy, PendingDetails, Attachment
from app.models.enums import UserRole, TicketStatus, Priority, SLAStatus, PendingReason, ActivityAction, DEFAULT_SLA_HOURS
from app.core.security import get_password_hash
from app.storage.memory import db

def seed_database(target_db=db):
    if len(target_db.users) > 0:
        return  # Already seeded

    # 1. SLA Policies
    for prio, hrs in DEFAULT_SLA_HOURS.items():
        target_db.sla_policies.append(SLAPolicy(
            priority=prio,
            response_hours=hrs,
            warning_threshold_percent=0.75
        ))

    # 2. Users (1 Admin, 2 Managers, 8 Staff, 30 Students)
    default_pass = get_password_hash("password123")

    # Admin
    admin = User(
        id=target_db.next_user_id(),
        name="System Administrator",
        email="admin@institution.edu",
        hashed_password=default_pass,
        role=UserRole.ADMIN,
        department="Campus Administration"
    )
    target_db.users.append(admin)

    # Managers
    m1 = User(
        id=target_db.next_user_id(),
        name="Dr. Sarah Jenkins",
        email="manager.finance@institution.edu",
        hashed_password=default_pass,
        role=UserRole.MANAGER,
        department="Finance"
    )
    m2 = User(
        id=target_db.next_user_id(),
        name="Prof. David Chen",
        email="manager.records@institution.edu",
        hashed_password=default_pass,
        role=UserRole.MANAGER,
        department="Registrar & Student Records"
    )
    target_db.users.extend([m1, m2])

    # Staff (8 staff members across departments)
    staff_specs = [
        ("Michael Scott", "staff.finance1@institution.edu", "Finance"),
        ("Angela Martin", "staff.finance2@institution.edu", "Finance"),
        ("Jim Halpert", "staff.records1@institution.edu", "Registrar & Student Records"),
        ("Pam Beesly", "staff.records2@institution.edu", "Registrar & Student Records"),
        ("Dwight Schrute", "staff.academic1@institution.edu", "Academic Affairs"),
        ("Stanley Hudson", "staff.academic2@institution.edu", "Academic Affairs"),
        ("Kelly Kapoor", "staff.support1@institution.edu", "Student Support Services"),
        ("Toby Flenderson", "staff.admin1@institution.edu", "Campus Administration"),
    ]
    staff_users = []
    for name, email, dept in staff_specs:
        s = User(
            id=target_db.next_user_id(),
            name=name,
            email=email,
            hashed_password=default_pass,
            role=UserRole.STAFF,
            department=dept
        )
        target_db.users.append(s)
        staff_users.append(s)

    # Students (30 students)
    student_names = [
        "Aarav Sharma", "Diya Patel", "Rohan Mehta", "Ananya Iyer", "Vikram Singh",
        "Ishita Roy", "Kabir Nair", "Sneha Rao", "Aditya Verma", "Pooja Kulkarni",
        "Alex Rivera", "Maya Lin", "Jordan Taylor", "Samira Khan", "Lucas Silva",
        "Emma Watson", "Liam Neeson", "Chloe Bennett", "Noah Centineo", "Olivia Rodrigo",
        "Karthik Subramanian", "Priya Das", "Nikhil Joshi", "Meera Pillai", "Arjun Reddy",
        "Fatima Zahra", "Daniel Kim", "Sophie Turner", "Marcus Brody", "Elena Rostova"
    ]
    student_users = []
    for i, name in enumerate(student_names):
        st = User(
            id=target_db.next_user_id(),
            name=name,
            email=f"{name.lower().replace(' ', '.')}@student.institution.edu",
            hashed_password=default_pass,
            role=UserRole.STUDENT,
            student_id_card=f"STU-2026-{1000 + i}"
        )
        target_db.users.append(st)
        student_users.append(st)

    # 3. Realistic Seed Tickets (55+ tickets covering diverse states)
    now = datetime.utcnow()

    ticket_templates = [
        # (category, subject, desc, dept, priority, status_blueprint, age_days, is_escalated)
        ("Fees", "Payment receipt not generated after bank wire transfer", "I made the semester tuition payment of $4,500 via wire transfer 10 days ago but my student portal shows overdue.", "Finance", Priority.HIGH, "BREACHED", 5, True),
        ("Fees", "Scholarship disbursement inquiry for Spring semester", "My merit scholarship adjustment has not been credited towards the tuition bill.", "Finance", Priority.MEDIUM, "IN_PROGRESS", 2, False),
        ("Fees", "Duplicate payment deduction on portal", "I clicked submit twice and got charged twice on my credit card. Please process refund.", "Finance", Priority.URGENT, "AT_RISK", 0.3, False),
        ("Fees", "Installment payment schedule request", "Requesting permission to split the remaining laboratory fee into two monthly installments.", "Finance", Priority.LOW, "RESOLVED", 6, False),
        ("Fees", "Late fee penalty waiver request due to hospital admission", "I was hospitalized during fee submission week. Attached medical certificate for penalty waiver.", "Finance", Priority.MEDIUM, "WAITING_FOR_STUDENT", 4, False),
        
        ("Attendance", "Attendance discrepancy in Computer Networks CS301", "I attended all labs on March 12 and 19 but the professor marked me absent.", "Academic Affairs", Priority.MEDIUM, "IN_PROGRESS", 1.5, False),
        ("Attendance", "Medical condonation for surgical leave", "Underwent appendectomy surgery. Submitting discharge summary for attendance shortage condonation.", "Academic Affairs", Priority.HIGH, "ASSIGNED", 0.5, False),
        ("Attendance", "On-Duty attendance for National Hackathon event", "Represented the university at the AI Hackathon from Sept 14-17. Dean approved permission letter attached.", "Academic Affairs", Priority.LOW, "RESOLVED", 8, False),
        ("Attendance", "Biometric scanner not recording morning check-in", "Scanner at Block B entrance frequently fails to read student cards between 8:30 AM and 9:00 AM.", "Academic Affairs", Priority.LOW, "NEW", 0.2, False),
        ("Attendance", "Exam hall ticket blocked due to attendance portal error", "My attendance is 78% but portal shows 64%, blocking my mid-term admit card tomorrow morning!", "Academic Affairs", Priority.URGENT, "BREACHED", 2.0, True),

        ("ID Card", "Lost student ID card during campus sports meet", "I misplaced my RFID ID card on the soccer field. Need replacement card urgently for library exam access.", "Registrar & Student Records", Priority.LOW, "ASSIGNED", 3, False),
        ("ID Card", "RFID chip malfunctioning at library turnstile gates", "The turnstile beeps red even though card has no physical damage. Re-encoding needed.", "Registrar & Student Records", Priority.LOW, "RESOLVED", 4, False),
        ("ID Card", "Name misspelling correction on smart ID badge", "My last name is spelled 'Mheta' instead of 'Mehta'. Please re-issue card.", "Registrar & Student Records", Priority.LOW, "WAITING_FOR_DOCUMENT", 5, False),
        ("ID Card", "Temporary visitor pass extension for thesis research", "Need student badge active until late evening for robotics lab access.", "Registrar & Student Records", Priority.MEDIUM, "IN_PROGRESS", 1, False),

        ("Certificates", "Urgent Bonafide certificate for passport renewal", "My passport appointment is scheduled for this Friday. Need signed bonafide with seal.", "Registrar & Student Records", Priority.URGENT, "AT_RISK", 0.25, False),
        ("Certificates", "Official Transcripts sealed envelope for Master's application", "Applying to graduate school in Canada. Need 3 sets of sealed official transcripts.", "Registrar & Student Records", Priority.MEDIUM, "IN_PROGRESS", 3, False),
        ("Certificates", "Provisional Degree Certificate request", "Completed all course credits in summer term. Employer requires provisional certificate immediately.", "Registrar & Student Records", Priority.HIGH, "BREACHED", 4, True),
        ("Certificates", "Medium of Instruction (English proficiency) certificate", "Require certificate stating undergraduate coursework was completed in English.", "Registrar & Student Records", Priority.LOW, "CLOSED", 15, False),
        ("Certificates", "Course completion verification letter for internship visa", "Consulate requires official letter verifying completion of 6th semester.", "Registrar & Student Records", Priority.HIGH, "REOPENED", 7, True),

        ("Documents", "Submission of pending 12th grade migration certificate", "Original migration certificate was delayed from State Board. Uploading scan now.", "Registrar & Student Records", Priority.MEDIUM, "WAITING_FOR_STUDENT", 6, False),
        ("Documents", "Attestation of degree grade cards for apostille", "Need university registrar signature on grade sheets for Ministry of External Affairs apostille.", "Registrar & Student Records", Priority.MEDIUM, "IN_PROGRESS", 2, False),
        ("Documents", "Recommendation letter request verification", "Dr. Jenkins submitted recommendation; waiting for registrar seal of authenticity.", "Registrar & Student Records", Priority.LOW, "RESOLVED", 10, False),

        ("General Administration", "Hostel room AC cooling defect during heatwave", "The split AC in Room 304 Block C stopped cooling completely since yesterday.", "Campus Administration", Priority.HIGH, "IN_PROGRESS", 0.8, False),
        ("General Administration", "Campus Wi-Fi connectivity dropping in Library 2nd floor", "Eduroam connection repeatedly disconnects every 5 minutes in silent study zone.", "Campus Administration", Priority.LOW, "NEW", 0.1, False),
        ("General Administration", "Lost laptop bag found in Auditorium Hall 1", "Found black Targus bag with engineering notebooks. Handed over to security desk.", "Campus Administration", Priority.MEDIUM, "CLOSED", 12, False),
        ("General Administration", "Parking sticker application for two-wheeler", "Submitting vehicle registration copy for East Gate student parking authorization.", "Campus Administration", Priority.LOW, "RESOLVED", 5, False),
    ]

    # Generate 55+ tickets by creating variations
    ticket_counter = 0
    for idx, (cat, subj, desc, dept, prio, kind, age_d, is_esc) in enumerate(ticket_templates * 3):
        ticket_counter += 1
        if ticket_counter > 55:
            break

        student = student_users[ticket_counter % len(student_users)]
        dept_staff_candidates = [s for s in staff_users if s.department == dept] or staff_users
        staff = dept_staff_candidates[ticket_counter % len(dept_staff_candidates)]

        t_id = target_db.next_ticket_id()
        t_num = f"TKT-2026-{t_id:05d}"
        created_time = now - timedelta(days=age_d, hours=random.randint(1, 10))
        sla_hours = DEFAULT_SLA_HOURS.get(prio, 48)

        # Map kind to status
        assigned_id = staff.id
        assigned_name = staff.name
        res_at = None
        closed_at = None
        res_summary = None
        reopen_cnt = 0
        pending_det = None
        paused_sec = 0

        if kind == "NEW":
            status = TicketStatus.NEW
            assigned_id = None
            assigned_name = None
            sla_due = created_time + timedelta(hours=sla_hours)
        elif kind == "ASSIGNED":
            status = TicketStatus.ASSIGNED
            sla_due = created_time + timedelta(hours=sla_hours)
        elif kind == "IN_PROGRESS":
            status = TicketStatus.IN_PROGRESS
            sla_due = created_time + timedelta(hours=sla_hours)
        elif kind == "WAITING_FOR_STUDENT":
            status = TicketStatus.WAITING_FOR_STUDENT
            sla_due = created_time + timedelta(hours=sla_hours)
            paused_sec = 86400  # 1 day paused
            pending_det = PendingDetails(
                reason=PendingReason.WAITING_FOR_STUDENT,
                since=now - timedelta(days=1),
                requested_action="Please provide fee transaction UTR number or bank statement screenshot.",
                requested_by=assigned_name
            )
        elif kind == "WAITING_FOR_DOCUMENT":
            status = TicketStatus.WAITING_FOR_STUDENT
            sla_due = created_time + timedelta(hours=sla_hours)
            pending_det = PendingDetails(
                reason=PendingReason.WAITING_FOR_DOCUMENT,
                since=now - timedelta(days=2),
                requested_action="Original passport affidavit copy is required.",
                requested_by=assigned_name
            )
        elif kind == "RESOLVED":
            status = TicketStatus.RESOLVED
            res_at = created_time + timedelta(hours=min(sla_hours - 2, 20))
            sla_due = created_time + timedelta(hours=sla_hours)
            res_summary = "Issue thoroughly investigated and resolved with registrar endorsement."
        elif kind == "CLOSED":
            status = TicketStatus.CLOSED
            res_at = created_time + timedelta(days=1)
            closed_at = created_time + timedelta(days=3)
            sla_due = created_time + timedelta(hours=sla_hours)
            res_summary = "Administrative verification completed and archival logged."
        elif kind == "REOPENED":
            status = TicketStatus.REOPENED
            reopen_cnt = 2
            sla_due = created_time + timedelta(hours=sla_hours)
        elif kind == "AT_RISK":
            status = TicketStatus.IN_PROGRESS
            # Make due date 1 hour from now
            sla_due = now + timedelta(hours=1, minutes=20)
        elif kind == "BREACHED":
            status = TicketStatus.IN_PROGRESS
            # Make due date in past
            sla_due = now - timedelta(hours=random.randint(4, 30))
        else:
            status = TicketStatus.IN_PROGRESS
            sla_due = created_time + timedelta(hours=sla_hours)

        ticket = Ticket(
            id=t_id,
            ticket_number=t_num,
            student_id=student.id,
            student_name=student.name,
            student_email=student.email,
            category=cat,
            subject=f"{subj} #{ticket_counter}",
            description=f"{desc} (Student ID: {student.student_id_card}). Please expedite if possible.",
            priority=prio,
            status=status,
            department=dept,
            assigned_staff_id=assigned_id,
            assigned_staff_name=assigned_name,
            created_at=created_time,
            updated_at=now - timedelta(hours=random.randint(1, 12)),
            sla_due_at=sla_due,
            total_paused_seconds=paused_sec,
            resolved_at=res_at,
            closed_at=closed_at,
            resolution_summary=res_summary,
            reopen_count=reopen_cnt,
            escalation_count=1 if is_esc else 0,
            is_escalated=is_esc,
            pending_details=pending_det,
            attachments=[
                Attachment(
                    id=f"att-{ticket_counter}",
                    filename="proof_document.pdf",
                    file_type="application/pdf",
                    size_bytes=248000,
                    data_url="data:application/pdf;base64,JVBERi0xLjQK..."
                )
            ]
        )
        target_db.tickets.append(ticket)

        # Seed activities for this ticket
        target_db.activities.append(Activity(
            id=target_db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=student.id,
            actor_name=student.name,
            actor_role=UserRole.STUDENT,
            action=ActivityAction.TICKET_CREATED,
            description=f"Ticket #{ticket.ticket_number} created with {ticket.priority.value} priority.",
            is_internal=False,
            created_at=created_time
        ))

        if assigned_id:
            target_db.activities.append(Activity(
                id=target_db.next_activity_id(),
                ticket_id=ticket.id,
                actor_id=m1.id,
                actor_name=m1.name,
                actor_role=UserRole.MANAGER,
                action=ActivityAction.TICKET_ASSIGNED,
                description=f"Ticket assigned to {assigned_name}.",
                is_internal=False,
                created_at=created_time + timedelta(minutes=15)
            ))

        # Add comment and internal note
        target_db.activities.append(Activity(
            id=target_db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=assigned_id or staff.id,
            actor_name=assigned_name or staff.name,
            actor_role=UserRole.STAFF,
            action=ActivityAction.INTERNAL_NOTE_ADDED,
            description="Verified student enrollment record against ERP database. Department clearance in review.",
            is_internal=True,
            created_at=created_time + timedelta(hours=1)
        ))

        target_db.activities.append(Activity(
            id=target_db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=assigned_id or staff.id,
            actor_name=assigned_name or staff.name,
            actor_role=UserRole.STAFF,
            action=ActivityAction.STAFF_REPLIED,
            description="We have received your request and cross-checked with the department logs. We are addressing it actively.",
            is_internal=False,
            created_at=created_time + timedelta(hours=2)
        ))

        if is_esc:
            esc = Escalation(
                id=target_db.next_escalation_id(),
                ticket_id=ticket.id,
                reason="SLA_BREACH" if kind == "BREACHED" else "URGENT_SLA_APPROACHING",
                previous_owner_id=staff.id,
                previous_owner_name=staff.name,
                new_owner_id=m1.id if dept == "Finance" else m2.id,
                new_owner_name=m1.name if dept == "Finance" else m2.name,
                notes="Automated escalation: Exceeded standard response threshold.",
                created_at=now - timedelta(hours=3)
            )
            target_db.escalations.append(esc)
            target_db.activities.append(Activity(
                id=target_db.next_activity_id(),
                ticket_id=ticket.id,
                actor_id=1,
                actor_name="Escalation Engine",
                actor_role=UserRole.ADMIN,
                action=ActivityAction.TICKET_ESCALATED,
                description=f"Ticket escalated to {esc.new_owner_name}. Reason: {esc.reason}.",
                is_internal=False,
                created_at=now - timedelta(hours=3)
            ))

        # Notification for student
        target_db.notifications.append(Notification(
            id=target_db.next_notification_id(),
            user_id=student.id,
            ticket_id=ticket.id,
            title="Ticket Status Update",
            message=f"Update available for Ticket #{ticket.ticket_number} ({ticket.status.value}).",
            is_read=random.choice([True, False]),
            event_type="STATUS_CHANGED",
            created_at=now - timedelta(hours=random.randint(1, 4))
        ))
