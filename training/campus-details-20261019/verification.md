# EGSPEC campus-detail verification (2026-10-19)

These answers use official institution pages. They describe what the college
publishes; they do not certify a student's personal campus experience or
guarantee placement.

| Fact | Official source |
| --- | --- |
| Campus environment, hostels, labs, block-to-department map | https://egspec.org/facilities/infrastructure |
| Institution vision and mission | https://www.egspec.org/about/vision-and-mission |
| Teaching/course structure | https://coe.egspec.org/admin/regulations/R2023UGRegulations.pdf |
| CO/PO/PSO example and mapping | https://coe.egspec.org/admin/syllabus/ug/01_Sem_UG_R2019/01_UG_AIDS_Sem1_R2019.pdf |
| Placement training | https://www.egspec.org/placements |
| CSE lab and faculty example | https://www.egspec.org/academics/departments/undergraduate/computer-science-and-engineering |
| Main focus and published motto | https://egspec.org/about/our-focus and https://www.egspec.org/about/message-from-the-principal |

## Contact data correction

The central admissions subpage mixes institution entries with contact values
that resemble placeholders. Those three college-specific values were removed
from the source QA and 65 generated QA rows instead of being treated as
verified simply because they appeared on an official domain.

| Institution | Source now used | Interpretation |
| --- | --- | --- |
| Arts and Science | https://egspasc.ac.in/public/ | Admission phone and published principal email on its own site |
| Polytechnic | https://egsppc.ac.in/ | College phone and email on its own site |
| Pharmacy | https://admissions.egspgroup.in/ | Only central group admissions contacts; pharmacy-specific details unverified |

Historic evaluation JSON files still record the old model's outputs and are
not a current source of truth. A future model training run must be built from
the corrected source data, not those evaluation reports.

Infrastructure wording on the official page is internally awkward: it says
"4 Academic Blocks and 2 Workshop Blocks" and separately names an Electrical
& Electronics Block. The answer preserves that distinction rather than
inventing a single total-building count. The exact room layout should be
confirmed with the campus office/map.

Bounded crawler checks made on this date:

- EGSPEC, 40 valid fetched URLs: 0 fetch failures; 17 malformed display-name
  URLs and 1 known-broken menu URL skipped and reported separately.
- Admissions site, 9 valid fetched URLs: 0 fetch failures; its `/engineering`
  link is a confirmed 404 and is skipped/reported separately.
- `egspgroup.in` and `www.egspgroup.in` currently return self-redirecting 308
  responses. This is a source-site problem and cannot truthfully be reported
  as successfully scraped. Other official sources and previously indexed data
  remain available.

These are bounded checks, not a claim that a future full crawl will have zero
failures. Future crawl output includes sample failed URLs plus counts for
expiring, malformed and known-broken links.
