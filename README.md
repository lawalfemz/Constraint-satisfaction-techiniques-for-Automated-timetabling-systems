University Timetable Generation using CSP & Greedy Search

This project implements a dynamic university timetable scheduler that models the scheduling problem as a Constraint Satisfaction Problem (CSP) and uses a Greedy Search heuristic to assign lectures, labs, tutorials, instructors, rooms, and time slots efficiently while satisfying strict academic constraints.

The system produces interactive, user-friendly web pages that reflect real university schedules, making it a practical tool for both academic planning and experimentation.

Features

Dynamic Scheduling: Update the Excel/CSV dataset and the timetable regenerates automatically.

Session Types: Handles courses with combinations of lecture, lab, and tutorial; some courses may have only one session type.

Constraint-Aware:

No overlapping assignments for instructors, rooms, or sections

Room type and capacity compatibility

Ensures all required sessions are scheduled

Soft Constraints (for future enhancements):

Minimizes student gaps

Balances instructor workloads

Interactive Output: 4 web pages

Main Timetable: Browse schedules by level, section, or specialization

Professors Page: View each professor’s weekly schedule

Assistant Professors Page: Check assistant professors individually

Rooms Page: Track room availability and bookings across the university

Dataset

Manually created based on real academic structures at Egypt-Japan University of Science and Technology (EJUST).

Stored in Excel/CSV for flexibility.

Matches real university scheduling, including multi-session courses.

Architecture

Python backend with modular design

Centralized constraint validation layer

Greedy Search–based assignment algorithm

Designed for future extensions: backtracking, advanced heuristics, and soft-constraint optimization

Tech Stack

Python

Pandas for data processing

CSP Modeling & Greedy Algorithms

HTML/CSS for interactive web output
