# Sample report

Real output of `python examples/run_audit.py` on the demo case (seed 20261121, case-001):

```
[history]
- first ambulation: 2 days before surgery.
- antibiotic start: 3 days before surgery.
[hospital_course]
- consult placed: hospital day 7.
[operative]
- fever onset: post-op day 9.
[discharge_plan]
- symptom onset: 12 days after discharge.

note_date: MAE 5.20 days, exact 0.00, catastrophic 0.20
  off by +5 days: '2 days before surgery' (true anchor procedure, assumed note)
  off by +5 days: 'post-op day 9' (true anchor procedure, assumed note)
  off by +1 days: '12 days after discharge' (true anchor discharge, assumed note)
  off by +5 days: '3 days before surgery' (true anchor procedure, assumed note)
  off by +10 days: 'hospital day 7' (true anchor admission, assumed note)
section_aware: MAE 0.00 days, exact 1.00, catastrophic 0.00
```
