# AI FORMATTING RULES — Anna University B.E./B.Tech. Project Report

> **Purpose:** This file is a precise, machine-readable specification for any AI assistant
> to generate or format an Anna University project report. Follow every rule exactly.
> When a rule says "MUST", it is mandatory per official guidelines.
> When a rule says "SHOULD", it is strongly recommended based on sample reports.

---

## DOCUMENT TYPE

- University: Anna University, Chennai 600 025
- Degree: Bachelor of Engineering (B.E.) / Bachelor of Technology (B.Tech.)
- Document: Final Year Project Report
- Source guidelines: UG_REPORT_FORMAT.pdf (official), PROJECT REPORT - Chapter details.pdf

---

## PAGE SETUP

| Property       | Value                          | Mandatory |
|----------------|--------------------------------|-----------|
| Paper size     | A4 (210 mm x 297 mm)          | YES       |
| Top margin     | 32 mm (range: 30-35 mm)       | YES       |
| Bottom margin  | 27 mm (range: 25-30 mm)       | YES       |
| Left margin    | 37 mm (range: 35-40 mm)       | YES       |
| Right margin   | 22 mm (range: 20-25 mm)       | YES       |
| Orientation    | Portrait                       | YES       |
| Binding side   | Left (extra margin for binding)| YES       |

---

## FONT RULES

MUST use **Times New Roman** for ALL text in the document. No exceptions.

| Context                              | Size   | Style         |
|--------------------------------------|--------|---------------|
| Body text (all chapters)             | 14 pt  | Regular       |
| Project title (title page)           | 18 pt  | Bold          |
| "A PROJECT REPORT" (title page)      | 14 pt  | Bold          |
| "Submitted by" (title page)          | 14 pt  | Bold + Italic |
| Student names (title page)           | 16 pt  | Bold          |
| "in partial fulfillment..." (title)  | 14 pt  | Italic        |
| Degree name (title page)             | 16 pt  | Bold          |
| College name (title page)            | 14 pt  | Bold          |
| University name (title page)         | 16 pt  | Bold          |
| Month & Year (title page)            | 14 pt  | Regular       |
| "ANNA UNIVERSITY" (certificate)      | 18 pt  | Bold          |
| "BONAFIDE CERTIFICATE" (certificate) | 16 pt  | Bold          |
| Certificate body text                | 14 pt  | Regular       |
| Chapter heading ("CHAPTER X")        | 16 pt  | Bold          |
| Chapter title                        | 16 pt  | Bold          |
| Section heading (e.g., 1.1)          | 14 pt  | Bold          |
| Subsection heading (e.g., 1.1.1)     | 14 pt  | Bold          |
| Abstract text                        | 14 pt  | Regular       |
| Table/Figure captions                | 14 pt  | Bold label    |
| Code listings                        | 11 pt  | Monospace     |

---

## LINE SPACING

| Context                              | Spacing        |
|--------------------------------------|----------------|
| Body text (all chapters)             | 1.5 spacing    |
| Bonafide Certificate body            | Double spacing |
| Abstract                             | Double spacing |
| Table of Contents                    | 1.5 spacing    |
| List of Figures                      | 1.5 spacing    |
| List of Tables                       | 1.5 spacing    |
| List of Abbreviations                | 1.5 spacing    |
| References / Bibliography            | Single spacing |
| Footnotes                            | Single spacing |

---

## TEXT FORMATTING

- Alignment: Justified (both left and right edges aligned)
- Paragraph indent: 1.27 cm (0.5 inch) for the first line of each paragraph
- Paragraph spacing: No extra space between paragraphs (spacing comes from line spacing)
- Print color: Black only

---

## PAGE NUMBERING

| Pages                                | Style                        | Position         |
|--------------------------------------|------------------------------|------------------|
| Title page                           | No number displayed          | —                |
| Front matter (certificate onwards)   | Lowercase Roman (i, ii, iii) | Centered, bottom |
| Chapters and back matter             | Arabic (1, 2, 3)            | Centered, bottom |

- Arabic numbering MUST restart at 1 when chapters begin.
- No headers or running text at top of pages.
- No footers other than the page number.

---

## PAGE ORDER (MANDATORY SEQUENCE)

1. **Title Page** — no page number displayed
2. **Bonafide Certificate** — page i
3. **Acknowledgement** — page ii (optional but commonly included)
4. **Certificate of Evaluation** — page iii (optional, college-specific)
5. **Abstract** — next Roman numeral
6. **Table of Contents**
7. **List of Figures**
8. **List of Tables**
9. **List of Abbreviations / Symbols / Nomenclature**
10. **Chapter 1: Introduction** — page 1 (Arabic numbering starts here)
11. **Chapter 2: Literature Survey**
12. **Chapter 3: System Design**
13. **Chapter 4: System Architecture**
14. **Chapter 5: System Implementation**
15. **Chapter 6: Results and Coding**
16. **Chapter 7: Conclusion and Future Work**
17. **References**
18. **Appendices** (if any)

---

## HEADING FORMAT

### Chapter Headings

- MUST be centered on the page
- MUST be bold, 16 pt
- Format is TWO lines:
  - Line 1: `CHAPTER X` (where X is the chapter number)
  - Line 2: `CHAPTER TITLE IN ALL CAPS`
- Both lines centered, bold, 16 pt
- Example:
  ```
                    CHAPTER 1
                   INTRODUCTION
  ```

### Section Headings (e.g., 1.1)

- MUST be left-aligned
- MUST be bold, 14 pt
- MUST be in ALL CAPS
- Format: `1.1  SECTION TITLE`
- Example: `1.1  OVERVIEW`

### Subsection Headings (e.g., 1.1.1)

- MUST be left-aligned
- MUST be bold, 14 pt
- Use Title Case (NOT all caps)
- Format: `1.1.1  Subsection Title`
- Example: `3.1.1  Use Case Diagram`

### Table of Contents Entries

- Chapter entries: Bold, ALL CAPS
- Section entries: ALL CAPS
- Subsection entries: Title Case
- Dot leaders connecting title to page number

---

## TITLE PAGE LAYOUT

All content centered. Elements in this exact order from top to bottom:

1. Project title — 18 pt, Bold, ALL CAPS
2. "A PROJECT REPORT" — 14 pt, Bold
3. "Submitted by" — 14 pt, Bold Italic
4. Student name(s) with register numbers — 16 pt, Bold
   - Format: `STUDENT NAME (RegisterNumber)`
   - One student per line
5. "in partial fulfillment for the award of the degree" — 14 pt, Italic
6. "of" — 14 pt, Italic
7. Degree name (e.g., "BACHELOR OF ENGINEERING") — 16 pt, Bold
8. "in" — 14 pt
9. Branch name (e.g., "COMPUTER SCIENCE AND ENGINEERING") — 14 pt, Bold
10. College logo image — centered, ~2 cm height
11. College name — 14 pt, Bold
12. "(An Autonomous Institution)" if applicable — 14 pt
13. Anna University logo image — centered, ~2.5 cm height
14. "ANNA UNIVERSITY :: CHENNAI 600025" — 16 pt, Bold
15. Month and Year — 14 pt

---

## BONAFIDE CERTIFICATE LAYOUT

1. "ANNA UNIVERSITY : CHENNAI 600 025" — centered, 18 pt, Bold
2. University logo — centered
3. "BONAFIDE CERTIFICATE" — centered, 16 pt, Bold
4. Body text — 14 pt, Double spacing, Justified:
   > Certified that this project report "PROJECT TITLE" is the bonafide work of
   > "STUDENT NAME (RegNo)" and "STUDENT NAME (RegNo)" who carried out the
   > project work under my supervision.
5. Two signature blocks at bottom of page:
   - **Left block:** SIGNATURE, HOD Name with Qualification, "Professor & Head,", Department, College Name, Address
   - **Right block:** SIGNATURE, Guide Name with Qualification, "SUPERVISOR,", Designation, Department, College Name, Address

---

## CHAPTER CONTENT REQUIREMENTS

### Chapter 1: Introduction
- Sections: Overview, Problem Statement, Existing System, Proposed System
- Additional sections as needed

### Chapter 2: Literature Survey
- Each referenced paper gets its own paragraph
- Cite papers using numbered references [1], [2], etc.
- Discuss contributions AND limitations of each paper

### Chapter 3: System Design
- Section: Unified Modelling Language (UML diagrams)
- Subsections for each diagram type: Use Case, Class, Sequence, Activity, Component, Deployment
- Each diagram MUST have explanatory text above and below

### Chapter 4: System Architecture
- Architecture diagram with explanation
- Description of system components and their interactions

### Chapter 5: System Implementation
- Section: Module Description
- Subsections for each module
- Include algorithms as pseudocode where applicable

### Chapter 6: Results and Coding
- Section 6.1: Sample Code (actual project code snippets)
- Section 6.2: Sample Screenshots (application screenshots)
- Section 6.3: Results and Graph (performance metrics, comparison tables, charts)
- MUST start with tools/technologies description (max 1 page)

### Chapter 7: Conclusion and Future Work
- NO sections or subsections allowed — write in paragraphs only
- Paragraph 1: Summary of accomplishments
- Paragraph 2: Key findings and contributions
- Paragraph 3: Limitations
- Paragraph 4: Future enhancements

---

## TABLES AND FIGURES

| Rule                              | Specification                                    |
|-----------------------------------|--------------------------------------------------|
| Table caption position            | ABOVE the table                                  |
| Figure caption position           | BELOW the figure                                 |
| Table numbering                   | Chapter.Sequence (e.g., Table 2.1, Table 2.2)   |
| Figure numbering                  | Chapter.Sequence (e.g., Figure 3.1, Figure 3.2) |
| Caption label style               | Bold (e.g., **Figure 3.1:** description)         |
| Placement                         | Near the text that references them               |
| Isolation                         | NEVER place a figure/table alone on a page       |
| Cross-reference                   | ALL figures and tables MUST be cited in text      |

- "Table" = tabulated numerical data only
- "Figure" = all non-text material (charts, graphs, diagrams, screenshots, photos)

---

## REFERENCES / BIBLIOGRAPHY

- Heading: "REFERENCES" — centered, bold, treated as an unnumbered chapter
- Listed in **alphabetical order** by first author's surname
- **Single spacing** within each reference entry
- Left-justified
- Numbered list: 1., 2., 3., ...
- Format: `Author(s) (Year) 'Title', Publication Details.`
- All references MUST be cited at least once in the text using [number]

---

## ABSTRACT

- Heading: "ABSTRACT" — centered, bold, 16 pt
- Body: ONE paragraph only
- Length: ONE page maximum
- Spacing: Double spacing
- Content must cover: problem addressed, methodology, key technologies, main results, significance

---

## ACKNOWLEDGEMENT

- Heading: "ACKNOWLEDGEMENT" — centered, bold, 16 pt
- Spacing: 1.5 (same as body text)
- Thank in this order:
  1. Chairman (with full name, qualifications)
  2. Managing Director (with full name, qualifications)
  3. Executive Director (with full name, qualifications)
  4. Principal (with full name, qualifications)
  5. Head of Department (with full name, qualifications)
  6. Project Guide/Supervisor (with full name, qualifications)
  7. Teaching and non-teaching staff of the department

---

## APPENDICES

- Labeled as: Appendix A, Appendix B, etc.
- Each appendix MUST have a title
- Appendix titles MUST appear in the Table of Contents
- Tables/figures in appendices follow the same numbering rules

---

## COMMON MISTAKES TO AVOID

1. Do NOT use any font other than Times New Roman
2. Do NOT use single spacing for body text (must be 1.5)
3. Do NOT place table captions below the table (must be above)
4. Do NOT leave figures/tables without text above and below
5. Do NOT use headers or running text at the top of pages
6. Do NOT use lowercase for chapter/section headings (must be ALL CAPS)
7. Do NOT add sections to Chapter 7 (paragraphs only)
8. Do NOT start code/tool description in Chapter 6 beyond 1 page
9. Do NOT place page numbers anywhere other than centered bottom
10. Do NOT skip the "CHAPTER X" line above the chapter title
11. Do NOT use Arabic numbers in front matter (must be Roman)
12. Do NOT forget to restart page numbering at 1 for Chapter 1

---

## COLLEGE-SPECIFIC DETAILS (St. Joseph's Institute of Technology)

| Field                  | Value                                              |
|------------------------|----------------------------------------------------|
| College Name           | St. Joseph's Institute of Technology               |
| Autonomous Status      | (An Autonomous Institution)                        |
| Address                | Old Mamallapuram Road, Chennai - 600 119           |
| University             | Anna University :: Chennai 600025                  |
| Chairman               | Dr. B. Babu Manoharan, M.A., M.B.A., Ph.D.        |
| Managing Director      | Mr. B. Sashi Sekar, M.Sc.                         |
| Executive Director     | Mrs. S. Jessie Priya, M.Com.                      |
| Principal              | Dr S Arivazhagan, M.E., Ph.D.                     |
| HOD (CSE)              | Dr. J. Dafni Rose, M.E., Ph.D.                    |
| Department             | Computer Science and Engineering                   |
| Degree                 | Bachelor of Engineering                            |
| Semester               | VIII                                               |

> **Note:** Guide/Supervisor details are project-specific and must be provided by the student.
