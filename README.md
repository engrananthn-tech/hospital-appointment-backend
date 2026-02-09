➤ Appointment Scheduling Backend (FastAPI + PostgreSQL)

This is a backend-only project.  

➤ Problem Scope (Intentionally Narrow)

● Doctors publish time slots
● Patients book, cancel appointments
● Doctors complete appointments
● Slots must not be double-booked
● Cancellations and completions must be consistent
● History must be traceable

➤ Decisions:

● 1. Slot booking is locked at the database level
Appointments and slots are modified inside transactions, with row-level locks.
Why:
• Application-level checks are not enough under concurrency
• Two requests arriving at the same time must not corrupt state
What this avoids:
• Double booking
• Cancel + complete race conditions
• Partial writes

● 2. State transitions are server-controlled
There is no generic "action" field sent by the client.

Endpoints are explicit:
• /appointments/{id}/cancel
• /appointments/{id}/complete
Why:
• Client choosing state transitions is unsafe
• Makes illegal transitions harder to introduce later

● 3. Database constraints

Examples:
• One active appointment per slot
• Enum-based states instead of free text
• Foreign keys with cascading rules

● 4. Audit trail for appointment state changes
Every cancel or complete action is recorded with:
• old state
• new state
• actor (doctor / patient)
• timestamp

● 5. JWT-based authentication with role separation
• Users authenticate via JWT
• Role (doctor / patient) is embedded in the token
• Role checks happen before hitting logic

● 6. Soft deactivation of doctors and patients
• Accounts are deactivated instead of deleted
• Deactivation is blocked if there are upcoming appointments
• Ensures appointment history remains consistent

➤ Tech Stack

• FastAPI – async-friendly, explicit request handling
• PostgreSQL – transactions, constraints, row locks
• SQLAlchemy ORM – explicit queries
• Alembic – schema migrations
• JWT – stateless auth
• Argon2 – password hashing

➤ Schema Evolution

The schema changes over time:
• Columns added
• Constraints changed
• Logic adjusted

This project uses Alembic migrations, not:
• Deleting tables
• Recreating schemas
• Manual DB edits

➤ Trade-offs (Intentional)

• No frontend  
  • This is a backend evaluation project
• Time-based logic uses app time  
  • Good enough for a single-instance system  
  • Database time can be swapped in later

➤ Limitations

  No soft deletes of data
  • Cancelled/completed rows pile up forever
  No rate limiting
  •Brute-force or spam not handled
  No pagination on heavy reads
  • Doctors with many appointments will suffer

➤ What I’d Improve With More Time

• Use DB time consistently for all temporal rules
• Add pagmentation(filters/limits)
• Add deletation of previous data(on request)


