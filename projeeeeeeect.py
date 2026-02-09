import csv
import pandas as pd
from datetime import datetime
from enum import Enum
from typing import List
import random


class SessionType(Enum):
    LECTURE = "Lecture"
    TUTORIAL = "Tutorial"
    LAB = "Lab"


class InstructorRole(Enum):
    PROFESSOR = "Professor"
    ASSISTANT_PROFESSOR = "Assistant Professor"


class Room:
    def __init__(self, building: str, space: str, capacity: int, room_type: str):
        self.building = building.strip()
        self.space = space.strip()
        self.capacity = capacity
        self.room_type = room_type.strip()
        self.is_lab = "Lab" in self.room_type
        self.full_name = f"{self.building} – {self.space}"

    def can_hold(self, student_count: int) -> bool:
        return self.capacity >= student_count


class Course:
    def __init__(self, course_id: str, name: str, credits: int, has_lecture: bool, has_tutorial: bool, has_lab: bool):
        self.course_id = course_id
        self.name = name
        self.credits = credits
        self.has_lecture = has_lecture
        self.has_tutorial = has_tutorial
        self.has_lab = has_lab


class Instructor:
    def __init__(self, instructor_id: str, name: str, role: InstructorRole, preferred_slots: str, qualified_courses: List[str]):
        self.instructor_id = instructor_id
        self.name = name
        self.role = role
        self.preferred_slots = preferred_slots
        self.qualified_courses = qualified_courses

    def can_teach(self, course_id: str) -> bool:
        return course_id in self.qualified_courses


class Section:
    def __init__(self, section_id: str, student_count: int, courses: List[str]):
        self.section_id = section_id
        self.student_count = student_count
        self.courses = courses

        if "_L1" in section_id:
            self.level = "L1"
            self.specialization = "Common"
        elif "_L2" in section_id:
            self.level = "L2"
            self.specialization = "Common"
        elif "_L3" in section_id:
            self.level = "L3"
            self.specialization = self._extract_specialization(section_id)
        elif "_L4" in section_id:
            self.level = "L4"
            self.specialization = self._extract_specialization(section_id)
        else:
            self.level = "Unknown"
            self.specialization = "Unknown"

    def _extract_specialization(self, section_id: str) -> str:
        if "_AID_" in section_id:
            return "AID"
        elif "_CNC_" in section_id:
            return "CNC"
        elif "_CSC_" in section_id:
            return "CSC"
        elif "_BIF_" in section_id:
            return "BIF"
        else:
            return "General"


class TimeSlot:
    def __init__(self, day: str, start_time: str, end_time: str, time_slot_id: str):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.time_slot_id = time_slot_id

    def start_time_obj(self):
        return datetime.strptime(self.start_time, "%I:%M %p").time()


class Assignment:
    def __init__(self, section_id: str, course_id: str, instructor_id: str, room_full_name: str, time_slot_id: str, session_type: SessionType):
        self.section_id = section_id
        self.course_id = course_id
        self.instructor_id = instructor_id
        self.room_full_name = room_full_name
        self.time_slot_id = time_slot_id
        self.session_type = session_type


class WebTimetableCSP:
    def __init__(self):
        self.rooms = []
        self.courses = {}
        self.instructors = {}
        self.sections = []
        self.time_slots = []
        self.assignments = []
        self.missing_instructors = set()

    def load_data(self):
        print("Loading data from files...")
        self._load_rooms()
        self._load_courses_from_excel()
        self._load_instructors()
        self._load_sections()
        self._load_time_slots()
        print(f"Loaded {len(self.rooms)} rooms")
        print(f"Loaded {len(self.courses)} courses")
        print(f"Loaded {len(self.instructors)} instructors")
        print(f"Loaded {len(self.sections)} sections")
        print(f"Loaded {len(self.time_slots)} time slots")

    def _load_rooms(self):
        try:
            df = pd.read_excel('Bulding.xlsx', header=None)
            for i in range(len(df)):
                if pd.notna(df.iloc[i, 0]) and str(df.iloc[i, 0]).strip() != '':
                    header_row = i
                    break
            else:
                header_row = 0
            df = pd.read_excel('Bulding.xlsx', header=header_row)
            df.columns = ['Building', 'Space', 'Capacity', 'Type']
            for _, row in df.iterrows():
                bld = str(row['Building']).strip()
                spc = str(row['Space']).strip()
                if bld.lower() in ['nan', ''] or spc.lower() in ['nan', '']:
                    continue
                cap = int(row['Capacity']) if pd.notna(row['Capacity']) else 50
                typ = str(row['Type']).strip() if pd.notna(row['Type']) else "Lecture"
                self.rooms.append(Room(bld, spc, cap, typ))
        except Exception as e:
            print(f"Error loading rooms: {e}")
            self.rooms = [Room("Hall", "Blue", 150, "Lecture")]

    def _load_courses_from_excel(self):
        try:
            df = pd.read_excel('courses_edited.xlsx')
            for _, row in df.iterrows():
                cid = str(row['CourseID']).strip()
                if cid == 'nan':
                    continue
                name = str(row.get('CourseName', cid)).strip()
                credits = int(row.get('Credits', 3))
                has_lecture = str(row.get('Lecture', 'No')).strip().lower() == 'yes'
                has_tutorial = str(row.get('Tutorial', 'No')).strip().lower() == 'yes'
                has_lab = str(row.get('Lab', 'No')).strip().lower() == 'yes'
                self.courses[cid] = Course(cid, name, credits, has_lecture, has_tutorial, has_lab)
        except Exception as e:
            print(f"Error loading courses from courses_edited.xlsx: {e}")

    def _load_instructors(self):
        try:
            with open('Instructor.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    iid = row['InstructorID'].strip()
                    if not iid:
                        continue
                    name = row.get('Name', '').strip()
                    role = InstructorRole.PROFESSOR if row.get('Role', '').strip() == 'Professor' else InstructorRole.ASSISTANT_PROFESSOR
                    slots = row.get('PreferredSlots', 'Any time').strip()
                    q_courses = [c.strip() for c in row.get('QualifiedCourses', '').split(',') if c.strip()]
                    self.instructors[iid] = Instructor(iid, name, role, slots, q_courses)
        except Exception as e:
            print(f"Error loading instructors: {e}")

    def _load_sections(self):
        try:
            df = pd.read_csv('Sections.csv', encoding='utf-8-sig')
            valid_course_ids = set(self.courses.keys())

            for _, row in df.iterrows():
                sid = str(row['SectionID']).strip()
                if not sid or sid == 'nan':
                    continue

                try:
                    count = int(row['StudentCount'])
                except:
                    count = 20

                courses_str = str(row['Courses']).strip()
                if courses_str == 'nan':
                    courses = []
                else:
                    courses = [c.strip() for c in courses_str.split(',') if c.strip()]

                valid_courses = [cid for cid in courses if cid in valid_course_ids]
                dropped = [cid for cid in courses if cid not in valid_course_ids]
                if dropped:
                    print(f" Dropped from {sid}: {', '.join(dropped)}")

                if not valid_courses:
                    print(f" Skipping {sid} (no valid courses)")
                    continue

                self.sections.append(Section(sid, count, valid_courses))
            print(f"Loaded {len(self.sections)} sections")
        except Exception as e:
            print(f"Error loading sections: {e}")
            import traceback
            traceback.print_exc()

    def _load_time_slots(self):
        try:
            with open('TimeSlots.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    day = row['Day'].strip()
                    start = row['StartTime'].strip()
                    end = row['EndTime'].strip()
                    tid = row['TimeSlotID'].strip()
                    if day and start and end and tid:
                        self.time_slots.append(TimeSlot(day, start, end, tid))
        except Exception as e:
            print(f"Error loading time slots: {e}")

    def generate_timetable(self):
        print("\nGenerating timetable with Lecture + Tutorial + Lab...")
        if not self.sections or not self.instructors:
            print("ERROR: Missing data!")
            return False

        self.assignments = []

        for section in self.sections:
            for course_id in section.courses:
                course = self.courses[course_id]
                if course.has_lecture:
                    self._assign_session(section, course_id, SessionType.LECTURE)
                if course.has_tutorial:
                    self._assign_session(section, course_id, SessionType.TUTORIAL)
                if course.has_lab:
                    self._assign_session(section, course_id, SessionType.LAB)

        if self.missing_instructors:
            print("\n MISSING INSTRUCTORS — Add these to Instructor.csv:")
            for item in sorted(self.missing_instructors):
                print(f"  - {item}")

        print(f" Generated {len(self.assignments)} assignments")
        return True

    def _assign_session(self, section: Section, course_id: str, session_type: SessionType) -> bool:
        if course_id in {"AID414", "BIF410", "CNC414", "CSC413"}:
            required_role = InstructorRole.ASSISTANT_PROFESSOR
        else:
            required_role = InstructorRole.PROFESSOR if session_type == SessionType.LECTURE else InstructorRole.ASSISTANT_PROFESSOR

        suitable_instructors = [
            iid for iid, inst in self.instructors.items()
            if inst.can_teach(course_id) and inst.role == required_role
        ]

        if not suitable_instructors:
            fallback_id = f"UNKNOWN_{required_role.name}_{course_id}"
            self.instructors[fallback_id] = Instructor(
                fallback_id,
                "Unknown Instructor",
                required_role,
                "Any time",
                [course_id]
            )
            suitable_instructors = [fallback_id]
            self.missing_instructors.add(f"{course_id} ({session_type.value}) → {required_role.value}")

        suitable_rooms = []
        for r in self.rooms:
            if not r.can_hold(section.student_count):
                continue

            if session_type == SessionType.LAB:
                if r.is_lab:
                    suitable_rooms.append(r)
            elif session_type == SessionType.TUTORIAL:
                if r.capacity <= 25:
                    suitable_rooms.append(r)
            else:  
                if not r.is_lab:
                    suitable_rooms.append(r)

        if not suitable_rooms:
            return False

        if session_type == SessionType.LECTURE:
            suitable_rooms.sort(key=lambda r: -r.capacity)
        random.shuffle(suitable_rooms)
        shuffled_slots = self.time_slots[:]
        random.shuffle(shuffled_slots)

        for iid in suitable_instructors:
            for room in suitable_rooms:
                for ts in shuffled_slots:
                    new_assign = Assignment(
                        section.section_id, course_id, iid, room.full_name, ts.time_slot_id, session_type
                    )
                    if self._is_valid_assignment(new_assign):
                        self.assignments.append(new_assign)
                        return True
        return False

    def _is_valid_assignment(self, assignment: Assignment) -> bool:
        for a in self.assignments:
            if (a.instructor_id == assignment.instructor_id and a.time_slot_id == assignment.time_slot_id) or \
               (a.room_full_name == assignment.room_full_name and a.time_slot_id == assignment.time_slot_id) or \
               (a.section_id == assignment.section_id and a.time_slot_id == assignment.time_slot_id):
                return False
        return True

    def generate_main_timetable(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>E-JUST CSIT Timetable — {datetime.now().strftime('%Y-%m-%d')}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Segoe UI', sans-serif;
  background: #f8fafc;
  color: #1e293b;
  padding: 20px;
}}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header {{
  background: linear-gradient(135deg, #0f4c75, #3282b8);
  color: white;
  text-align: center;
  padding: 30px 20px;
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(15, 76, 117, 0.3);
  margin-bottom: 20px;
}}
.filters {{
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}}
select {{
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  font-size: 0.95em;
}}
.level-card {{
  background: white;
  border-radius: 16px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  overflow: hidden;
}}
.level-header {{
  background: linear-gradient(135deg, #00bfa5, #009688);
  color: white;
  padding: 16px 24px;
  font-size: 1.4em;
  font-weight: 700;
}}
.section-card {{
  margin: 15px;
  background: #f1f5f9;
  border-radius: 12px;
  overflow: hidden;
  display: none;
}}
.section-header {{
  background: #334155;
  color: white;
  padding: 12px 20px;
  font-size: 1.2em;
  font-weight: 600;
}}
.days-container {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  padding: 20px;
}}
.day-card {{
  background: white;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}}
.day-header {{
  font-weight: 700;
  font-size: 1.15em;
  color: #0f4c75;
  margin-bottom: 10px;
  padding-bottom: 4px;
  border-bottom: 2px solid #cbd5e1;
}}
.assignment {{
  background: #dbeafe;
  border-left: 4px solid #3b82f6;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 10px;
  font-size: 0.9em;
}}
.assignment.tutorial {{
  background: #ffecb3;
  border-left: 4px solid #ffa000;
}}
.assignment.lab {{
  background: #dcfce7;
  border-left: 4px solid #22c55e;
}}
.course-title {{
  font-weight: 700;
  color: #1e3a8a;
  display: block;
  margin-bottom: 4px;
}}
.details {{
  color: #475569;
  font-size: 0.85em;
  line-height: 1.4;
}}
.empty {{
  color: #94a3b8;
  font-style: italic;
  text-align: center;
  padding: 10px;
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🎓 E-JUST CSIT Timetable</h1>
    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
  </div>
  <div class="filters">
    <select id="levelFilter">
      <option value="all">All Levels</option>
      <option value="L1">Level 1</option>
      <option value="L2">Level 2</option>
      <option value="L3">Level 3</option>
      <option value="L4">Level 4</option>
    </select>
    <select id="specializationFilter">
      <option value="all">All Specializations</option>
      <option value="Common">Common</option>
      <option value="AID">AI & Data Science</option>
      <option value="CNC">Cybersecurity</option>
      <option value="CSC">Computer Science</option>
      <option value="BIF">Bioinformatics</option>
    </select>
    <select id="sectionFilter">
      <option value="all">All Sections</option>
    </select>
  </div>
"""

        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        time_slot_map = {ts.time_slot_id: ts for ts in self.time_slots}

        spec_names = {
            "AID": "Artificial Intelligence & Data Science",
            "CNC": "Cybersecurity",
            "CSC": "Computer Science",
            "BIF": "Bioinformatics"
        }

        def section_sort_key(sec):
            level_order = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
            spec_order = {"Common": 0, "AID": 1, "CNC": 2, "CSC": 3, "BIF": 4, "General": 5}
            sec_num = 0
            if "_L1" in sec.section_id:
                sec_num = int(sec.section_id.split('_')[0][1:])
            elif "_L2" in sec.section_id:
                sec_num = int(sec.section_id.split('_')[0][1:]) + 100
            elif "_L3" in sec.section_id:
                sec_num = int(sec.section_id.split('_')[0][1:]) + 200
            elif "_L4" in sec.section_id:
                sec_num = int(sec.section_id.split('_')[0][1:]) + 300
            return (level_order.get(sec.level, 99), spec_order.get(sec.specialization, 99), sec_num)

        sorted_sections = sorted(self.sections, key=section_sort_key)

        current_level = None
        for section in sorted_sections:
            sec_assigns = [a for a in self.assignments if a.section_id == section.section_id]
            if not sec_assigns:
                continue

            if section.level != current_level:
                if current_level is not None:
                    html += "</div>"
                html += f'<div class="level-card" data-level="{section.level}"><div class="level-header">Level {section.level}</div>'
                current_level = section.level

            spec_name = spec_names.get(section.specialization, section.specialization)
            section_number = section.section_id.split('_')[0][1:] 
            section_display = f"Section {section_number}"
            html += f'<div class="section-card" data-section="{section.section_id}" data-specialization="{section.specialization}">'
            html += f'<div class="section-header">{section_display} — {spec_name}</div>'
            html += '<div class="days-container">'

            for day in days:
                html += f'<div class="day-card"><div class="day-header">{day}</div>'
                day_assigns = [a for a in sec_assigns if time_slot_map[a.time_slot_id].day == day]

                if not day_assigns:
                    html += '<div class="empty">No classes</div>'
                else:
                    def get_start_time(assignment):
                        ts = time_slot_map[assignment.time_slot_id]
                        return datetime.strptime(ts.start_time, "%I:%M %p").time()
                    day_assigns.sort(key=get_start_time)

                    for a in day_assigns:
                        course = self.courses[a.course_id]
                        inst = self.instructors.get(a.instructor_id, type('obj', (object,), {'name': 'Unknown'}))
                        ts = time_slot_map[a.time_slot_id]
                        session_label = a.session_type.value
                        session_class = a.session_type.name.lower()

                        html += f"""
                        <div class="assignment {session_class}">
                          <span class="course-title">{course.name} ({a.course_id})</span>
                          <span class="details">
                            {ts.start_time} – {ts.end_time}<br>
                            👨‍🏫 {inst.name}<br>
                            📍 {a.room_full_name}<br>
                            {"📘 " + session_label}
                          </span>
                        </div>
                        """
                html += "</div>"
            html += "</div></div>"

        if current_level is not None:
            html += "</div>"

        html += """
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const levelFilter = document.getElementById('levelFilter');
    const specFilter = document.getElementById('specializationFilter');
    const sectionFilter = document.getElementById('sectionFilter');
    const sectionCards = document.querySelectorAll('.section-card');
    const allSections = Array.from(sectionCards).map(card => ({
        id: card.dataset.section,
        level: card.closest('.level-card').dataset.level,
        spec: card.dataset.specialization
    }));

    function populateSectionFilter() {
        sectionFilter.innerHTML = '<option value="all">All Sections</option>';
        const filtered = allSections.filter(s => 
            (levelFilter.value === 'all' || s.level === levelFilter.value) &&
            (specFilter.value === 'all' || s.spec === specFilter.value)
        );
        const unique = [...new Set(filtered.map(s => s.id))].sort();
        unique.forEach(id => {
            const opt = document.createElement('option');
            opt.value = id;
            // Simplify display: S1_L1 → Section 1
            const num = id.split('_')[0].substring(1);
            opt.textContent = `Section ${num}`;
            sectionFilter.appendChild(opt);
        });
    }

    function applyFilters() {
        const level = levelFilter.value;
        const spec = specFilter.value;
        const section = sectionFilter.value;

        sectionCards.forEach(card => {
            const cardLevel = card.closest('.level-card').dataset.level;
            const cardSpec = card.dataset.specialization;
            const cardSection = card.dataset.section;

            let show = true;
            if (level !== 'all' && cardLevel !== level) show = false;
            if (spec !== 'all' && cardSpec !== spec) show = false;
            if (section !== 'all' && cardSection !== section) show = false;

            card.style.display = show ? 'block' : 'none';
        });
    }

    levelFilter.addEventListener('change', () => {
        populateSectionFilter();
        applyFilters();
    });
    specFilter.addEventListener('change', () => {
        populateSectionFilter();
        applyFilters();
    });
    sectionFilter.addEventListener('change', applyFilters);

    populateSectionFilter();
});
</script>
</body></html>
"""
        with open("timetable.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Main timetable saved as 'timetable.html'")

    def generate_professors_timetable(self):
        professors = {iid: inst for iid, inst in self.instructors.items() if inst.role == InstructorRole.PROFESSOR}
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>E-JUST Professors Timetable</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Segoe UI', sans-serif;
  background: #f8fafc;
  color: #1e293b;
  padding: 20px;
}}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header {{
  background: linear-gradient(135deg, #0f4c75, #3282b8);
  color: white;
  text-align: center;
  padding: 30px 20px;
  border-radius: 16px;
  margin-bottom: 20px;
}}
.filters select {{
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  font-size: 0.95em;
  width: 300px;
  margin-bottom: 20px;
}}
.prof-card {{
  background: white;
  border-radius: 16px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  overflow: hidden;
  display: none;
}}
.prof-header {{
  background: #4f46e5;
  color: white;
  padding: 16px 24px;
  font-size: 1.4em;
  font-weight: 700;
}}
.days-container {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  padding: 20px;
}}
.day-card {{
  background: white;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}}
.day-header {{
  font-weight: 700;
  font-size: 1.15em;
  color: #0f4c75;
  margin-bottom: 10px;
  padding-bottom: 4px;
  border-bottom: 2px solid #cbd5e1;
}}
.assignment {{
  background: #dbeafe;
  border-left: 4px solid #3b82f6;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 10px;
  font-size: 0.9em;
}}
.course-title {{
  font-weight: 700;
  color: #1e3a8a;
  display: block;
  margin-bottom: 4px;
}}
.details {{
  color: #475569;
  font-size: 0.85em;
  line-height: 1.4;
}}
.empty {{
  color: #94a3b8;
  font-style: italic;
  text-align: center;
  padding: 10px;
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>👨‍🏫 E-JUST Professors Timetable</h1>
    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
  </div>
  <div class="filters">
    <select id="profFilter">
      <option value="all">Select Professor</option>
"""
        prof_list = sorted([(inst.name, iid) for iid, inst in professors.items()])
        for name, iid in prof_list:
            html += f'<option value="{iid}">{name}</option>'
        html += """
    </select>
  </div>
"""

        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        time_slot_map = {ts.time_slot_id: ts for ts in self.time_slots}

        for iid, inst in professors.items():
            prof_assigns = [a for a in self.assignments if a.instructor_id == iid]
            if not prof_assigns:
                continue

            html += f'<div class="prof-card" data-prof="{iid}">'
            html += f'<div class="prof-header">{inst.name}</div>'
            html += '<div class="days-container">'

            for day in days:
                html += f'<div class="day-card"><div class="day-header">{day}</div>'
                day_assigns = [a for a in prof_assigns if time_slot_map[a.time_slot_id].day == day]

                if not day_assigns:
                    html += '<div class="empty">Free</div>'
                else:
                    def get_start_time(assignment):
                        ts = time_slot_map[assignment.time_slot_id]
                        return datetime.strptime(ts.start_time, "%I:%M %p").time()
                    day_assigns.sort(key=get_start_time)

                    for a in day_assigns:
                        course = self.courses[a.course_id]
                        section = a.section_id
                        ts = time_slot_map[a.time_slot_id]
                        session_label = a.session_type.value

                        html += f"""
                        <div class="assignment">
                          <span class="course-title">{course.name} ({a.course_id})</span>
                          <span class="details">
                            {ts.start_time} – {ts.end_time}<br>
                            👥 {section}<br>
                            📍 {a.room_full_name}<br>
                            {"📘 " + session_label}
                          </span>
                        </div>
                        """
                html += "</div>"
            html += "</div></div>"

        html += """
</div>
<script>
document.getElementById('profFilter').addEventListener('change', function() {
    const selected = this.value;
    document.querySelectorAll('.prof-card').forEach(card => {
        card.style.display = (selected === 'all' || card.dataset.prof === selected) ? 'block' : 'none';
    });
});
</script>
</body></html>
"""
        with open("professors.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(" Professors timetable saved as 'professors.html'")

    def generate_assistants_timetable(self):
        assistants = {iid: inst for iid, inst in self.instructors.items() if inst.role == InstructorRole.ASSISTANT_PROFESSOR}
        # 🔹 Filter out "Unknown Instructor"
        assistants = {iid: inst for iid, inst in assistants.items() if inst.name != "Unknown Instructor"}

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>E-JUST Assistant Professors Timetable</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Segoe UI', sans-serif;
  background: #f8fafc;
  color: #1e293b;
  padding: 20px;
}}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header {{
  background: linear-gradient(135deg, #0f4c75, #3282b8);
  color: white;
  text-align: center;
  padding: 30px 20px;
  border-radius: 16px;
  margin-bottom: 20px;
}}
.filters select {{
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  font-size: 0.95em;
  width: 300px;
  margin-bottom: 20px;
}}
.assistant-card {{
  background: white;
  border-radius: 16px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  overflow: hidden;
  display: none;
}}
.assistant-header {{
  background: #0ea5e9;
  color: white;
  padding: 16px 24px;
  font-size: 1.4em;
  font-weight: 700;
}}
.days-container {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  padding: 20px;
}}
.day-card {{
  background: white;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}}
.day-header {{
  font-weight: 700;
  font-size: 1.15em;
  color: #0f4c75;
  margin-bottom: 10px;
  padding-bottom: 4px;
  border-bottom: 2px solid #cbd5e1;
}}
.assignment {{
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 10px;
  font-size: 0.9em;
}}
.assignment.tutorial {{
  background: #ffecb3;
  border-left: 4px solid #ffa000;
}}
.assignment.lab {{
  background: #dcfce7;
  border-left: 4px solid #22c55e;
}}
.course-title {{
  font-weight: 700;
  color: #1e3a8a;
  display: block;
  margin-bottom: 4px;
}}
.details {{
  color: #475569;
  font-size: 0.85em;
  line-height: 1.4;
}}
.empty {{
  color: #94a3b8;
  font-style: italic;
  text-align: center;
  padding: 10px;
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>👩‍🏫 E-JUST Assistant Professors Timetable</h1>
    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
  </div>
  <div class="filters">
    <select id="assistantFilter">
      <option value="all">Select Assistant Professor</option>
"""
        ass_list = sorted([(inst.name, iid) for iid, inst in assistants.items()])
        for name, iid in ass_list:
            html += f'<option value="{iid}">{name}</option>'
        html += """
    </select>
  </div>
"""

        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        time_slot_map = {ts.time_slot_id: ts for ts in self.time_slots}

        for iid, inst in assistants.items():
            ass_assigns = [a for a in self.assignments if a.instructor_id == iid]
            if not ass_assigns:
                continue

            html += f'<div class="assistant-card" data-assistant="{iid}">'
            html += f'<div class="assistant-header">{inst.name}</div>'
            html += '<div class="days-container">'

            for day in days:
                html += f'<div class="day-card"><div class="day-header">{day}</div>'
                day_assigns = [a for a in ass_assigns if time_slot_map[a.time_slot_id].day == day]

                if not day_assigns:
                    html += '<div class="empty">Free</div>'
                else:
                    def get_start_time(assignment):
                        ts = time_slot_map[assignment.time_slot_id]
                        return datetime.strptime(ts.start_time, "%I:%M %p").time()
                    day_assigns.sort(key=get_start_time)

                    for a in day_assigns:
                        course = self.courses[a.course_id]
                        section = a.section_id
                        ts = time_slot_map[a.time_slot_id]
                        session_label = a.session_type.value

                        html += f"""
                        <div class="assignment {a.session_type.name.lower()}">
                          <span class="course-title">{course.name} ({a.course_id})</span>
                          <span class="details">
                            {ts.start_time} – {ts.end_time}<br>
                            👥 {section}<br>
                            📍 {a.room_full_name}<br>
                            {"📘 " + session_label}
                          </span>
                        </div>
                        """
                html += "</div>"
            html += "</div></div>"

        html += """
</div>
<script>
document.getElementById('assistantFilter').addEventListener('change', function() {
    const selected = this.value;
    document.querySelectorAll('.assistant-card').forEach(card => {
        card.style.display = (selected === 'all' || card.dataset.assistant === selected) ? 'block' : 'none';
    });
});
</script>
</body></html>
"""
        with open("assistants.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Assistant Professors timetable saved as 'assistants.html'")

    def generate_rooms_timetable(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>E-JUST Rooms Timetable</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Segoe UI', sans-serif;
  background: #f8fafc;
  color: #1e293b;
  padding: 20px;
}}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header {{
  background: linear-gradient(135deg, #0f4c75, #3282b8);
  color: white;
  text-align: center;
  padding: 30px 20px;
  border-radius: 16px;
  margin-bottom: 20px;
}}
.filters {{
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}}
select {{
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  font-size: 0.95em;
}}
.building-card {{
  background: white;
  border-radius: 16px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  overflow: hidden;
  display: none;
}}
.building-header {{
  background: #8b5cf6;
  color: white;
  padding: 16px 24px;
  font-size: 1.4em;
  font-weight: 700;
}}
.room-card {{
  margin: 15px;
  background: #f1f5f9;
  border-radius: 12px;
  overflow: hidden;
  display: none;
}}
.room-header {{
  background: #7e22ce;
  color: white;
  padding: 12px 20px;
  font-size: 1.15em;
  font-weight: 600;
}}
.days-container {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  padding: 20px;
}}
.day-card {{
  background: white;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}}
.day-header {{
  font-weight: 700;
  font-size: 1.15em;
  color: #0f4c75;
  margin-bottom: 10px;
  padding-bottom: 4px;
  border-bottom: 2px solid #cbd5e1;
}}
.occupied {{
  background: #fee2e2;
  border-left: 4px solid #ef4444;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 10px;
  font-size: 0.9em;
}}
.free {{
  background: #dcfce7;
  border-left: 4px solid #22c55e;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 10px;
  font-size: 0.9em;
  color: #166534;
  font-weight: 500;
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🏢 E-JUST Rooms Timetable</h1>
    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
  </div>
  <div class="filters">
    <select id="buildingFilter">
      <option value="all">All Buildings</option>
"""
        buildings = sorted(set(r.building for r in self.rooms))
        for b in buildings:
            html += f'<option value="{b}">{b}</option>'
        html += """
    </select>
    <select id="roomFilter">
      <option value="all">All Rooms</option>
    </select>
  </div>
"""

        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        time_slot_map = {ts.time_slot_id: ts for ts in self.time_slots}

        rooms_by_building = {}
        for r in self.rooms:
            rooms_by_building.setdefault(r.building, []).append(r)
        for b in rooms_by_building:
            rooms_by_building[b].sort(key=lambda r: r.space)

        for building in sorted(rooms_by_building.keys()):
            html += f'<div class="building-card" data-building="{building}">'
            html += f'<div class="building-header">{building}</div>'

            for room in rooms_by_building[building]:
                html += f'<div class="room-card" data-room="{room.full_name}" data-building="{building}">'
                html += f'<div class="room-header">{room.space} ({room.capacity} seats)</div>'
                html += '<div class="days-container">'

                for day in days:
                    html += f'<div class="day-card"><div class="day-header">{day}</div>'
                    room_day_assigns = [
                        a for a in self.assignments
                        if a.room_full_name == room.full_name and time_slot_map[a.time_slot_id].day == day
                    ]
                    day_slots = [ts for ts in self.time_slots if ts.day == day]
                    day_slots.sort(key=lambda ts: datetime.strptime(ts.start_time, "%I:%M %p").time())

                    if not day_slots:
                        html += '<div class="free">No schedule</div>'
                    else:
                        used_slots = {a.time_slot_id for a in room_day_assigns}
                        for ts in day_slots:
                            if ts.time_slot_id in used_slots:
                                assign = next(a for a in room_day_assigns if a.time_slot_id == ts.time_slot_id)
                                course = self.courses[assign.course_id]
                                inst = self.instructors.get(assign.instructor_id, type('obj', (object,), {'name': 'Unknown'}))
                                html += f"""
                                <div class="occupied">
                                  {ts.start_time} – {ts.end_time}<br>
                                  {course.name} ({assign.course_id})<br>
                                  👨‍🏫 {inst.name} | 👥 {assign.section_id}
                                </div>
                                """
                            else:
                                html += f'<div class="free">{ts.start_time} – {ts.end_time} — FREE</div>'
                    html += "</div>"
                html += "</div></div>"
            html += "</div>"

        html += """
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const buildingFilter = document.getElementById('buildingFilter');
    const roomFilter = document.getElementById('roomFilter');
    const roomCards = document.querySelectorAll('.room-card');
    const allRooms = Array.from(roomCards).map(card => ({
        full: card.dataset.room,
        building: card.dataset.building
    }));

    function populateRoomFilter() {
        roomFilter.innerHTML = '<option value="all">All Rooms</option>';
        const filtered = allRooms.filter(r => 
            buildingFilter.value === 'all' || r.building === buildingFilter.value
        );
        const unique = [...new Set(filtered.map(r => r.full))].sort();
        unique.forEach(full => {
            const opt = document.createElement('option');
            opt.value = full;
            opt.textContent = full;
            roomFilter.appendChild(opt);
        });
    }

    function applyFilters() {
        const building = buildingFilter.value;
        const room = roomFilter.value;

        document.querySelectorAll('.building-card').forEach(card => {
            card.style.display = 'none';
        });

        roomCards.forEach(card => {
            const cardBuilding = card.dataset.building;
            const cardRoom = card.dataset.room;

            let show = true;
            if (building !== 'all' && cardBuilding !== building) show = false;
            if (room !== 'all' && cardRoom !== room) show = false;

            card.style.display = show ? 'block' : 'none';
            if (show) {
                card.closest('.building-card').style.display = 'block';
            }
        });
    }

    buildingFilter.addEventListener('change', () => {
        populateRoomFilter();
        applyFilters();
    });
    roomFilter.addEventListener('change', applyFilters);

    populateRoomFilter();
});
</script>
</body></html>
"""
        with open("rooms.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Rooms timetable saved as 'rooms.html'")

    def generate_all_reports(self):
        self.generate_main_timetable()
        self.generate_professors_timetable()
        self.generate_assistants_timetable()
        self.generate_rooms_timetable()


if __name__ == "__main__":
    system = WebTimetableCSP()
    system.load_data()
    if system.generate_timetable():
        system.generate_all_reports()
        print("\nAll timetables generated! Open:")
        print("  - timetable.html      (Main)")
        print("  - professors.html     (Professors)")
        print("  - assistants.html     (Assistant Professors)")
        print("  - rooms.html          (Rooms)")
    else:
        print("\nFailed to generate timetable.")