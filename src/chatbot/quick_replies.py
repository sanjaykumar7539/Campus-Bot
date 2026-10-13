from typing import List
import re

class QuickReplies:
    def __init__(self):
        self.intent_map = {
            r"(fee|payment|tuition|cost)": ["Fee Structure", "Payment Deadlines", "Scholarship Info"],
            r"(exam|test|schedule|timetable)": ["Exam Schedule", "Syllabus", "Results"],
            r"(faculty|teacher|professor|staff)": ["Faculty Directory", "Contact Faculty", "Office Hours"],
            r"(admission|apply|enroll|join)": ["Admission Process", "Required Documents", "Contact Admissions"],
            r"(hostel|accommodation|room|stay)": ["Hostel Rules", "Hostel Fees", "Mess Menu"],
            r"(placement|job|recruit|company)": ["Placement Records", "Past Recruiters", "Training Programs"]
        }

    def get_replies(self, query: str) -> List[str]:
        query_lower = query.lower()
        replies = []
        for pattern, suggestions in self.intent_map.items():
            if re.search(pattern, query_lower):
                replies.extend(suggestions)
        if not replies:
            replies = ["Academic Calendar", "Fee Structure", "Faculty Directory", "Admissions"]
        return replies[:4]
