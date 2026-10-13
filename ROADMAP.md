# CampusMind Product Roadmap

**Current Version:** 2.1.x (Ultimate Advanced)  
**Last Updated:** 2026-10-10  
**Status:** Living document — tracks planned capabilities beyond the current audit-hardened baseline.

This roadmap consolidates every major enhancement identified after the full project audit. Features are grouped into delivery phases with priority, effort estimate, dependencies, and success criteria.

---

## Vision

CampusMind should evolve from a high-quality grounded RAG assistant into a complete **institutional intelligence platform** that:

- Serves students, faculty, and administrators with role-appropriate knowledge
- Continuously improves from real usage and feedback
- Proactively surfaces important information
- Remains fully deployable on college infrastructure (one-command, privacy-first)

---

## Phase Overview

| Phase | Theme | Target Version | Timeline (indicative) |
|-------|-------|----------------|-----------------------|
| **Phase 1** | Visibility & Control | 2.2 | Short-term |
| **Phase 2** | Access Control & Trust | 2.3 | Short–Medium |
| **Phase 3** | Continuous Improvement | 2.4 | Medium |
| **Phase 4** | Proactive & Connected | 3.0 | Medium–Long |
| **Phase 5** | Scale & Intelligence | 3.x+ | Long-term |

---

## Phase 1 — Visibility & Control (v2.2)

**Goal:** Give administrators clear insight and operational control without requiring code access.

### 1.1 Admin Dashboard (Web UI)
- **Priority:** Critical
- **Effort:** Medium
- **Description:** Authenticated web dashboard showing:
  - Real-time chat volume & active sessions
  - Recent feedback (thumbs up/down + comments)
  - Knowledge base status (last sync, document count, failed ingestions)
  - System health (ready/live, model status, vector DB health)
  - Top unanswered / low-confidence questions
- **Dependencies:** Existing admin role + JWT auth, analytics module
- **Success Criteria:** Admin can diagnose “why is the bot not answering X?” without SSH or logs

### 1.2 Chat Export & Report Generator
- **Priority:** High
- **Effort:** Low–Medium
- **Description:**
  - Export single conversation or date-range as PDF / Markdown
  - Optional institutional header/footer
  - One-click “Share with Counsellor / HOD”
- **Dependencies:** Existing chat logging + message_id
- **Success Criteria:** Student or admin can download a clean, citable conversation record

### 1.3 Document Change Timeline
- **Priority:** High
- **Effort:** Medium
- **Description:** Visual timeline of website/PDF changes detected by the monitor
  - Diff summary or “what changed”
  - Link to affected questions that may need re-answering
- **Dependencies:** Existing OfficialSourcesMonitor + hashing
- **Success Criteria:** Admin sees “Circular published 2 days ago” and can force re-ingest

---

## Phase 2 — Access Control & Trust (v2.3)

**Goal:** Deliver the right information to the right role while increasing answer reliability.

### 2.1 Role-based Knowledge Access
- **Priority:** Critical
- **Effort:** Medium
- **Description:**
  - Tag documents / chunks with visibility roles (student, faculty, hostel-manager, admin)
  - Retrieval and answer generation respect the caller’s role
  - Public/anonymous users receive only public knowledge
- **Dependencies:** Existing role system (student/faculty/hostel-manager/admin)
- **Success Criteria:** Faculty circulars never appear in student answers

### 2.2 Continuous Evaluation Dashboard
- **Priority:** High
- **Effort:** Medium
- **Description:**
  - Track grounding rate, hallucination flags, retrieval hit-rate, latency
  - Weekly quality scorecard
  - Automatic flagging of declining topics
- **Dependencies:** Existing evaluation scripts + feedback API
- **Success Criteria:** Quality trends visible without running offline reports manually

### 2.3 Offline Mode Improvements
- **Priority:** Medium
- **Effort:** Low–Medium
- **Description:**
  - Clear “Last synced” indicator in UI
  - Graceful degradation messaging when models or vector store are unavailable
  - Optional local-only FAQ cache for critical questions
- **Dependencies:** Existing readiness endpoints + response cache
- **Success Criteria:** Users understand system state even during network/model issues

---

## Phase 3 — Continuous Improvement (v2.4)

**Goal:** Close the loop between real usage and knowledge quality.

### 3.1 Feedback → Training / Review Loop
- **Priority:** High
- **Effort:** Medium
- **Description:**
  - Admin queue of down-voted or low-confidence answers
  - Ability to mark chunks as “needs review / outdated / incorrect”
  - Optional auto-suggestion of better source documents
- **Dependencies:** Feedback API + message_id + admin dashboard
- **Success Criteria:** Bad answers are systematically corrected rather than ignored

### 3.2 Automatic FAQ Generation
- **Priority:** Medium
- **Effort:** Medium
- **Description:**
  - Cluster most frequent questions
  - Propose canonical answers grounded in current knowledge
  - Admin can promote FAQ entries into the high-priority retrieval set
- **Dependencies:** Chat analytics + hybrid retriever
- **Success Criteria:** Top 20 recurring questions have curated, high-confidence answers

### 3.3 PWA / Installable Experience
- **Priority:** Medium
- **Effort:** Low–Medium
- **Description:**
  - Full Progressive Web App manifest + service worker
  - “Add to Home Screen” on mobile
  - Basic offline shell
- **Dependencies:** Existing responsive UI
- **Success Criteria:** Students install CampusMind like a native campus app

---

## Phase 4 — Proactive & Connected (v3.0)

**Goal:** Move from reactive Q&A to proactive institutional assistance.

### 4.1 Proactive Notifications
- **Priority:** High
- **Effort:** Medium–High
- **Description:**
  - Detect high-importance changes (exam schedules, fee deadlines, circulars)
  - Push or in-app notifications to relevant roles
  - Optional email / WhatsApp gateway (college-controlled)
- **Dependencies:** Document Change Timeline + role system
- **Success Criteria:** Students learn about critical dates without having to ask

### 4.2 LMS Integration (Moodle / Google Classroom)
- **Priority:** High
- **Effort:** High
- **Description:**
  - Pull announcements, assignments, and calendar events
  - Ground answers in live LMS data when available
  - Respect LMS permissions
- **Dependencies:** Role-based access + secure credential storage
- **Success Criteria:** “When is the next assignment due?” answered from live LMS data

### 4.3 Calendar & Academic Events Integration
- **Priority:** Medium
- **Effort:** Medium
- **Description:**
  - Ingest college academic calendar
  - Answer date/time questions with structured event data
  - Visual calendar cards in responses
- **Dependencies:** Existing visual response system (Leaflet already present)
- **Success Criteria:** Event questions return structured, verified dates

---

## Phase 5 — Scale & Advanced Intelligence (3.x+)

**Goal:** Multi-institution readiness and deeper intelligence.

### 5.1 Multi-campus / Multi-tenant Mode
- **Priority:** Medium–High (for productization)
- **Effort:** High
- **Description:**
  - Fully isolated knowledge bases, users, and configuration per tenant
  - Shared product core with tenant-specific branding and data
- **Dependencies:** Current product/tenant separation already started
- **Success Criteria:** One deployment can safely serve multiple independent colleges

### 5.2 Fine-tuned Institute SLM
- **Priority:** Medium
- **Effort:** High
- **Description:**
  - Domain-adapted small language model trained on verified institutional content
  - Lower latency and higher factual consistency for common campus queries
- **Dependencies:** High-quality grounded dataset + evaluation harness
- **Success Criteria:** Measurable reduction in hallucination rate on campus-specific questions

### 5.3 Voice Wake-word (“Hey CampusMind”)
- **Priority:** Low–Medium
- **Effort:** Medium
- **Description:** Always-listening or push-to-talk wake word for hands-free use in labs / libraries
- **Dependencies:** Existing voice streaming pipeline
- **Success Criteria:** Reliable activation with low false-positive rate

### 5.4 Sentiment & Early-Warning Analytics
- **Priority:** Medium
- **Effort:** Medium
- **Description:**
  - Aggregate sentiment on student conversations (privacy-preserving)
  - Flag emerging issues (hostel, transport, exam stress) for counsellor review
- **Dependencies:** Chat logging + admin dashboard
- **Success Criteria:** Actionable signals without exposing individual private chats

---

## Cross-Cutting Principles (apply to every phase)

1. **Privacy-first** — No external telemetry by default; all analytics local or college-controlled.
2. **Grounding remains mandatory** — New features must not weaken citation / confidence requirements.
3. **One-command startup preserved** — `python main.py` continues to work.
4. **Role & security model respected** — Every new surface inherits existing JWT + role checks.
5. **Backward compatible** — Existing deployments can upgrade without data loss.
6. **Measurable** — Every major feature ships with clear success metrics and test coverage.

---

## Suggested Immediate Next Steps

1. Implement **Admin Dashboard** (Phase 1.1) — highest operational leverage.
2. Add **Role-based Knowledge Access** (Phase 2.1) — critical for trust.
3. Ship **Chat Export** (Phase 1.2) — quick win for students and staff.
4. Extend the existing evaluation scripts into a live **Continuous Evaluation** view.

---

## How to Use This Roadmap

- Treat each feature card as a candidate epic.
- Break into GitHub issues / milestones when ready to implement.
- Update the “Status” column (Planned → In Progress → Done) as work proceeds.
- Revisit priorities after each major release based on real user feedback.

---

*This roadmap is derived from the post-audit feature analysis and is intended to guide the next major product iterations of CampusMind.*
