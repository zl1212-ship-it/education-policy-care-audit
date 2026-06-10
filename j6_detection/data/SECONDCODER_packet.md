# Second-coder packet (intra-rater / test-retest reliability)

Code the ten institutions below WITHOUT looking at `policy_corpus.csv` (the codes of
record). For each institution read its policy text and choose one value per dimension.
There are no blank cells. When done, send the ten lines back (or fill
`data/policy_corpus_secondcoder.csv`); kappa is then computed by `analyze_kappa.py`.

## The five dimensions and their values

1. **detector_admissibility** -- is detector output usable as evidence of misconduct?
   - `prohibited` = a binding ban ("prohibits", "may not be used / may not be the basis").
   - `advisory`   = discredited but not banned ("instructors should refrain / avoid / are
     discouraged"; "not reliable proof").
   - `silent`     = no rule on using detector output as evidence (even if it merely notes
     that detection tools exist).
   - `admissible` = approved or encouraged to use ("the only detector approved for use",
     "faculty are encouraged to explore detectors").

2. **burden_of_proof** -- once a flag triggers a case, who must establish what?
   - `institution` = a binding rule that the flag cannot stand alone ("not the sole / single
     basis", "may not be the single measure", corroboration required).
   - `student`     = the student must rebut / prove authorship (e.g. produce drafts).
   - `unspecified` = anything else (DEFAULT; never leave blank).

3. **appeal_pathway** -- is there a route to contest a finding?
   - `formal`   = a named appeal / grievance process or body.
   - `informal` = mentions review / reconsideration but no formal route.
   - `none`     = no appeal described (DEFAULT; never leave blank).

4. **l2_protection** -- are multilingual / non-native writers acknowledged? (binary)
   - `explicit` = names multilingual / ELL / non-native / international writers, OR warns
     that detector output may misread writing by people whose first language is not English.
   - `none`     = otherwise (general fairness / equity / bias language with no link to
     language background counts as `none`).

5. **decision_locus** -- who SETS the rule on AI / detector use?
   - `institutional` = a binding institution-wide rule governs.
   - `delegated`     = the rule is left to instructors / syllabi.
   - `silent`        = neither. (A central honor/conduct office that only adjudicates cases is
     NOT, by itself, `institutional`.)

## How to record each institution
Write one line: `Institution: admissibility, burden, appeal, l2, locus`
e.g. `University of Iowa: advisory, unspecified, none, none, delegated`

---

## 1. University of Hawaii at Manoa

```
### PRIMARY https://manoa.hawaii.edu/ovpae/guidance-on-ai/
Guidance on AI | Office of the Vice Provost for Academic Excellence
Skip to Main Content
UHM Home
A-Z Index
Directory
Students
Faculty and Staff
Parents
Alumni
MyUH
Office of the Vice Provost for Academic Excellence
Menu 
Open Mobile Menu
Search 
About
About
Contacts
Policy
Academic Affairs Policies
Policy Review and Approval Process
Guidance on AI
Faculty
Academic Personnel
Departmental Personnel Documents
Contract Renewal
Tenure and Promotion
Periodic Review
Workload Policies
Chairs
UHM Leadership
Chair Handbook
Department Chair Boot Camp
Leadership Matters
Courses
Course Actions
Guidelines for Completing UHM Forms
UHM-1 Form Guide (Add a Course)
UHM-2 Form Guide (To Modify or Retire a Course)
Sample Syllabus
Scheduling Office
Programs
Program Approval & Review
Agreements
Assessment & Curriculum Support
Bachelor’s and Master’s (BAM) Combined Degree Pathways
Micro-credentials at Mānoa
Distance & Off-Campus Programs
Catalog
Training
Events
Faculty Development & Support
Leading with Excellence
NCFDD Curriculum
WeLead
Campus-wide
Academic Calendar
General Education
Graduate Division
Honors Program
Institutional Research
Interdisciplinary Studies
Search this site
Site search
Home
 Guidance on AI
Guidance on AI
Generative Artificial Intelligence (AI) holds promise in improving higher education, offering both opportunities and challenges for universities. AI-powered tools can provide new learning modes, personalize learning experiences, and enable students to receive tailored support and feedback. Additionally, AI can streamline administrative tasks, enhancing efficiency and potentially reducing operational costs. However, the integration of AI also raises important questions about data privacy, ethics, algorithmic bias, and the need for faculty and staff preparation. Balancing AI’s potential and addressing these challenges is important, as the advent of these tools is already reshaping aspects of higher education.
AI and Academic Integrity
The 
UHM student code of conduct (IV.B.1.a)
 addresses “Cheating, plagiarism, or other forms of academic dishonesty.” It gives the instructor authority over defining unauthorized assistance, authorized sources, and specifically prohibited behavior in classes. For this reason, instructors are strongly encouraged to:
Be specific about expectations and limitations on student use of AI in assignments,
Hold students responsible for the accuracy of facts and sources used in assignments, and to
Talk through scenarios with classes to provide clarity on expectations
Syllabi and class discussions should make instructor expectations clear with respect to use of AI tools. UHOIC maintains 
sample statements for adaptation
 in a syllabus or specific assignments.
Assignment and Assessment Redesign
The widespread availability of AI tools creates both challenges and opportunities for instructors. Similar to the reframing required at the onset of digital calculators (at least for math and science instruction) and internet search engines, assignments and assessments may need redesign to achieve our learning objectives.
Some useful redesign strategies are: 
Chunk assignments with due dates for individual elements
 that precede final submission: an outline, notes on research articles, and drafts.

Instructors might consider Google Docs version history and/or 
draftback
, a tool to record the writing process,  to review students’ writing progression. Versions of a document can be renamed to show stages of an assignment.
Replace a writing assignment with an audio file
, podcast, video, speech, drawing, diagram, or multimedia project. (make running to AI more work than it’s worth)
Incorporate AI. Ask students to generate a ChatGPT response to a question of their own choosing, then write an analysis of the strengths and weaknesses of the response.
Reference class materials or 
sources that are not available on the internet
Include visuals
 — images or videos that students need to respond to
Connect to 
current events or conversations in your field
Ask for 
application of personal knowledge
/experience
(Khan Academy’s, 
AI for Education
)
Additional strategies include:
Employ 
authentic and contextualized assessments
. Design to require critical thinking, analysis, and application of knowledge in real-world contexts. By tailoring assessments to specific scenarios or case studies, it is challenging for students to rely solely on AI for complete solutions
Use 
open-ended questions
 that prompt students to demonstrate their understanding, creativity, and ability to articulate ideas. These are less likely to have direct answers generated by AI tools, encouraging engagement in original thinking and reflection
Incorporate elements that 
evaluate the process students followed
 to arrive at solutions. This could include written explanations, justifications, or reflections alongside final submissions, demonstrating the individual thought processes and learning journeys
(
UH Recommendations
 on Assessment)
AI 
Resources for Teaching & Learning
Many resources can be found in this annotated listing maintained by 
UHOIC
, which includes sections on Accessibility, Assessment, References, Copyright, Educational Considerations, Ethics, Pedagogy, Classroom Policies, Prompting, Tools, and Supplemental Resources.
UH Recommendations
Learning About Generative AI
Experts agree that generative AI tools are here to stay. Teaching and learning about AI is one piece of a need to assist students in learning appropriate 21st century digital skills. Like other new technologies, there are challenges and concerns that come along. 
Faculty and students are encouraged to experiment with AI tools while staying within legal and ethical parameters
 to the best of their ability. Proliferation of AI-integrated tools is predicted, and university personnel should be aware of policies and procedures that relate to the adoption of new technologies, including:
EP 2.219
 Student Online Data Protection Requirements for Third Party Vendors
EP 2.215
 Institutional Data Governance
EP 2.210
 Use and Management of Information Technology Resources
And UH 
Approved 3rd-Party Online Tools
Photo by 
Hitesh Choudhary
 on 
Unsplash
Office of the Vice Provost for Academic Excellence

 2500 Campus Road

 Hawaiʻi Hall 209

 Honolulu, HI 96822

Contact Us
academic@hawaii.edu
Telephone: (808) 956-5244
Fax: (808) 956-7115
A-Z Index
Academic Calendar
Accessibility at UH
Accessibility Statement
Campus Directory
Campus Maps
Parking & Transportation
Visiting the Campus
Emergency Information
Campus Safety
Title IX
UH News & Media
Press Releases
Events
Work at UH
campusHELP
UH Email
MyUH
Giving to UH
Site Feedback
UH System

 The University of Hawaiʻi is an equal opportunity institution

 ©2020 University of Hawaiʻi at Mānoa • 2500 Campus Road • Honolulu, HI 96822 • (808) 956-8111
 
Back to top
```

**YOUR CODES (University of Hawaii at Manoa):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 2. University of Idaho

```
### PRIMARY https://ai.uidaho.edu/ai-academic-integrity/
AI + Academic Integrity – AI @ UI
Skip to content
Home
AI Execution Team
News & Events
Expand
News
Events
Policies & Guidance
Expand
Interim Guidance from OIT for Artificial Intelligence
AI Memo from OIT
AI White Paper
Deepseek Ban
Contact Us
Toggle Menu
Events
 | 
News
AI + Academic Integrity
November 10, 2025
November 10, 2025
Idaho AI Catalyst Webinar #3
Registration Details
Date/Time
: Monday, November 17, 2025 · 10:00–11:00 AM Mountain 
Format
 60 minutes · AI Catalyst Training · Live Q&A 
Where
 Zoom (registration required)
Register
After registering, you will receive a confirmation email with the join link.
This third installment in the Catalyst AI Foundations for Faculty is a supplement to the previous webinar on 
AI + Assessment
. As we improve our course design to become more AI-informed, we’re still faced with a major challenge: how do we handle academic integrity? Teaching has always required some level of enforcement and rigor, we’ve always had to hold students accountable for their work, but the rapid spread of ChatGPT and agentic browsers feels like it’s eroding our pre-2022 approach to academic integrity. This is particularly true of online and hybrid courses, but everyone feels it.
In Webinar 3, the Idaho AI Catalyst series will cover all things academic integrity and related ethical questions, such as whether faculty should even require students to use AI (or ban it?), how to select policies that work best for your situation, and whether process-tracking tools such as Grammarly Authorship or Google Docs History should be part of your grading toolkit. We’ll also provide tips for communicating your course expectations clearly and how to hold students accountable without compromising 
your
own
 integrity as an educator. The webinar will build on the work of former Idaho AI Fellows, Liza Long and Jason Blomquist, updated for Fall 2025 developments, such as the rise of agentic browsers. 
Joel Gladd (College of Western Idaho) will provide an overview of recent AI developments and how they impact academic integrity, as well as the different ethical models and strategies that relate to these discussions. Catalyst members Taylor Waring (North Idaho College), Heidi Tighe (College of Southern Idaho), and Abraham Romney (Idaho State University) will present examples and insights from their own experience as educators. 
Who this is for
Higher-ed faculty, staff, and administrators who engage with students and learning environments. Useful for instructors, program coordinators, student conduct leads, instructional designers, and department chairs.
What you’ll learn
How recent AI technologies are impacting academic integrity discussions 
How to communicate clear expectations for when and how AI use is permitted in your course
AI-use acknowledgement statements that support accountability 
Conversation strategies for responding when student work appears AI-generated
About the Idaho AI Catalysts
A statewide network across Idaho’s public colleges and universities, facilitated by the Idaho State Board of Education. We share practices, build AI literacy, pilot tools, and host open trainings. Our aim is to help faculty use AI effectively and ethically within a community of practice.
Post navigation
Previous
Previous
Graduate Writing Symposium – Crafting a Compelling Teaching Philosophy
Next
Continue
Reimagining Teaching with AI: Generative AI for Content CreationAI Series
Similar Posts
Events
 | 
News
Statewide Generative AI Drop-In Sessions
December 13, 2024
December 13, 2024
Statewide Generative AI Drop-In Sessions

 Read More
 Statewide Generative AI Drop-In Sessions
Continue
Events
Graduate Writing Symposium – Crafting a Compelling Teaching Philosophy
October 8, 2025
We will cover the various uses of generative AI in graduate level writing, as well as the ethics of using AI in your academic writing. Additionally, we will cover the new graduate school AI policy for academic writing to make students aware of the official university stance—this will include how improper use of AI will be identified and what actions can be taken against students who use AI improperly in their academic work while at UI. In the second session, we will cover the basics of what a teaching statement is and how to write one. 

 Read More
 Graduate Writing Symposium – Crafting a Compelling Teaching Philosophy
Continue
Events
Teaching AI Literacy, what is and isn’t working
October 28, 2024
October 28, 2024
Teaching AI Literacy, what is and isn’t working
Thursday, November 7

12:30-1:30 p.m. PT

Buchanan Engineering Lab 205

 Read More
 Teaching AI Literacy, what is and isn’t working
Continue
Events
One AI to Rule Them All: How to Build a Large Multimodal Model (LMM) that Handles Text, Images and Music
November 8, 2024
November 8, 2024
One AI to Rule Them All: How to Build a Large Multimodal Model (LMM) that Handles Text, Images and Music
Friday, December 6 2024

12:30-1:30 p.m. PT

Data Hub (Lib 107)

 Read More
 One AI to Rule Them All: How to Build a Large Multimodal Model (LMM) that Handles Text, Images and Music
Continue
Events
 | 
News
AI for Writing and Assessment of Writing
December 13, 2024
December 13, 2024
Discover how to harness genAI tools to transform writing instruction and assessment in higher education. This interactive workshop explores practical strategies and ethical considerations for using AI to enhance student learning and writing, featuring OER resources designed to empower both educators and students. It is designed for instructors who give writing assessments of any kind.  Come prepared to work on an assignment prompt that integrates AI in practical, productive, and ethical ways. 

 Read More
 AI for Writing and Assessment of Writing
Continue
Events
 | 
News
Using Machine Learning to Predict Patterns of Biodiversity
January 29, 2026
As the biodiversity crisis accelerates, the need arises to hasten the pace of biodiversity research. 

 Read More
 Using Machine Learning to Predict Patterns of Biodiversity
Continue
© 2026 AI @ UI

Powered by 
RCDS
Scroll to top
Scroll to top
Home
AI Execution Team
News & Events
Toggle child menu
Expand
News
Events
Policies & Guidance
Toggle child menu
Expand
Interim Guidance from OIT for Artificial Intelligence
AI Memo from OIT
AI White Paper
Deepseek Ban
Contact Us
```

**YOUR CODES (University of Idaho):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 3. University of Iowa

```
### PRIMARY https://teach.its.uiowa.edu/artificial-intelligence-tools-and-teaching
Artificial Intelligence Tools and Teaching | Office of Teaching, Learning, and Technology - The University of Iowa

 Skip to main content
 
The University of Iowa

 Office of Teaching, Learning, and Technology
 
Search
Submit Search
Search
Site Main Navigation
About Us
Academic Technology Advisory Council
Meet Our Staff
News
Events
Communities
Recorded Trainings
Initiatives
Instructional Services
Learning Spaces Technology
Research and Analytics
Breadcrumb
Home
Artificial Intelligence Tools and Teaching
The newest entry in a long line of technologies that promise to disrupt higher education are artificial intelligence (AI) tools like ChatGPT. In seconds these tools can use machine learning to generate text, video, or images, in response to users’ prompts.
The technology continues to advance, with features such as internet browser plugins that can generate answers to assessment and homework questions. Computer generated text does have its limitations. Users can’t rely on the tool to make qualitative judgments, such as determining if language is appropriate for a given context or rely on the accuracy of content citations.
These tools are widely available, and instructors will need to consider carefully how to adapt to these developments. Amid discussions and academic integrity concerns about these tools, the Office of Teaching Learning, and Technology and the Center for Teaching offer this brief guide to address some of the most frequently asked questions about ChatGPT and other AI tools.
These are new technologies, and the future is unknown as the availability and reliability of these tools are developing.
Request a one-on-one 
consultation with the Office of Teaching, Learning, and Technology
.
For more information or 
guidance on the role of AI in your teaching
, visit the Office of the Provost website or 
request a consultation with the Center for Teaching
.
Visit the ITS website for more information on 
AI at the University of Iowa in general
.
If you have questions about the 
risks related to security, privacy, and ethical considerations
 or how to assess a given implementation of AI, 
contact ITS Security
 What do I put in my syllabus about AI-generated and other externally generated content?
You may need to discuss using AI tools in a variety of contexts, including learning materials and campus, collegiate, and course policies related to academic integrity. Consult with your collegiate leadership about specific policies. In any case, providing transparent information about expectations for student use of AI tools and how these expectations align with course goals and scholarly values is crucial.
Remember that with any policy in your syllabus, it’s important to have ongoing conversations throughout the semester.  Some example language:
When AI is prohibited.
 [This course] assumes that work submitted by students—all process work, drafts, low-stakes writing, final versions, and all other submissions—will be generated by the students themselves, working individually or in groups. This means that the following would be considered violations of academic integrity: a student has another person/entity do the writing of any substantive portion of an assignment for them, which includes hiring a person or a company to write essays and drafts and/or other assignments, research-based or otherwise, and using artificial intelligence affordances like ChatGPT. 
(Excerpted from 
ChatGPT
 by University of California: Irvine Division of Teaching Excellence and Innovation)
When AI is allowed with attribution. 
In all academic work, the ideas and contributions of others must be appropriately acknowledged and work that is presented as original must be, in fact, original. Using an AI-content generator (such as ChatGPT) to complete coursework without proper attribution or authorization is a form of academic dishonesty. If you are unsure about whether something may be plagiarism or academic dishonesty, please contact your instructor to discuss the issue. Faculty, students, and administrative staff all share the responsibility of ensuring the honesty and fairness of the intellectual environment. 
(Excerpted from 
Constructing a Syllabus: A Checklist
 by Washington University in St. Louis Center for Teaching and Learning)
When AI is allowed with attribution. 
Use of AI tools, including ChatGPT, is permitted in this course for students who wish to use them. To be consistent with our scholarly values, students must cite any AI-generated material that informed their work and use quotation marks or other appropriate indicators of quoted material when appropriate. Students should indicate how AI tools informed their process and the final product, including how you validated any AI-generated citations, which may be invented by the AI. Assignment guidelines will provide additional guidance as to how these tools might be part of your process for each assessment this semester and how to provide transparency about their use in your work.
 When AI use is encouraged with certain tasks.
 Students are invited to use AI platforms to help prepare for assignments and projects (e.g., to help with brainstorming or to see what a completed essay might look like). I also welcome you to use AI tools to help revise and edit your work (e.g., to help identify flaws in reasoning, spot confusing or underdeveloped paragraphs, or to simply fix citations). When submitting work, students must clearly identify any writing, text, or media generated by AI. This can be done in a variety of ways. In this course, parts of essays generated by AI should appear in a different colored font, and the relationship between those sections and student contributions should be discussed in cover letters that accompany the essay submission. 
(
Based on 
Course Policies related to ChatGPT and other AI Tools
 by Joel Gladd
)
In addition to AI use in assignments, you may want to be clear in your syllabus about your policies regarding AI and exams. See the “
What do I need to know about AI glasses and other wearable 'smart' devices
” section of this page.
For more, Ryan Watkins, professor of Educational Technology Leadership, and Human-Technology Collaboration at George Washington University, offers 
suggestions to update your course syllabus and assignments
. For more ideas about communicating with students about generative AI in your syllabus and beyond, 
contact the Center for Teaching
.
 Can I use AI Detectors to check students’ work?
Instructors should refrain from using AI detectors on student work due to the inherent inaccuracies in these tools.
AI detectors can produce false positives, unfairly penalizing students who have not engaged in any academic misconduct. Moreover, using AI detectors shifts pedagogical focus to policing, undermining the trust between students and educators, and offers only a short-term solution as AI technology is rapidly evolving.
Instead, educators should focus on fostering open dialogue, providing clear guidelines and a variety of assessment methods to ensure academic integrity and support authentic student learning. As alternatives to AI detectors:
Create assignments that motivate students and help them understand how their work supports their learning. Incorporate course materials and require direct quotations from these materials to be included in students’ written answers.
Use multi-stage assignments with drafts and revisions.
Consider non-written formats like presentations or multimedia projects.
Design assignments with components that ask students to use their own voice and personal experiences.
Ask students metacognitive follow-up questions about their assignments to encourage reflection on their thought processes and confirm the authenticity of their work.
The Center for Teaching has resources available for instructors wishing to 
promote academic integrity
 or 
redesign assignments for future students
.
Learn more about the limitations of AI detection tools:
Abdali, S., Anarfi, R., Barberan, C. J., & He, J. (2024). Decoding the AI Pen: Techniques and Challenges in Detecting AI-Generated Text. 
arXiv
. 
https://doi.org/10.48550/arXiv.2403.05750
Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., & Feizi, S. (2024)1. Can AI-Generated Text be Reliably Detected? 
arXiv
. 
https://doi.org/10.48550/arXiv.2303.11156
Weber-Wulff, D., Anohina-Naumeca, A., Bjelobaba, S.
et al.
 Testing of detection tools for AI-generated text. 
International Journal for Educational Integrity, 19
, 1-39. (2023). 
https://doi.org/10.1007/s40979-023-00146-z
 How can I clearly communicate my expectations to my students about acceptable levels of generative AI use?
Students may have access to a variety of resources like calculators, Wikipedia, peers, hired tutors, and increasingly, AI tools to accomplish their course tasks and assignments. 
Instructors are encouraged to engage in discussions with their students about Iowa’s 
policy on Academic Misconduct
. Students benefit from transparent instructions about which tools and resources they can appropriately leverage in their work (e.g., Winkelmes et. al, 2016). They will also need guidance on how to cite or acknowledge the tools and individuals who contributed to their work. Although a policy in a course syllabus is a good way to start these conversations, the syllabus shouldn’t be the only time that the policy is discussed.
The Center for Teaching's Handbook for Teaching Excellence provides 
additional information on promoting academic integrity
.
Another resource available is the AI Assessment Scale (AIAS). 
Read this information from the University of Iowa Center for Teaching on how to use the AIAS
 to make intentional course design choices and clearly communicate expectations around generative AI.
 What are some examples of assessments that incorporate AI tools? 
Some instructors may want to incorporate AI tools into their assignments so that students develop the skills necessary to interact with it in the future. Depending on course goals, potential assignments could include:
Developing a question that will effectively elicit an AI-generated response that meets certain specifications.
Comparing and contrasting AI-generated text with other scholarly work.
Evaluating AI-generated text for missing or inaccurate information.
Using AI to generate examples or proofs of concept (
Warner, 2022
).
Like any technology tool, it is important to consider questions about student privacy, availability of technical troubleshooting, and accessibility prior to requiring use by students. Instructors can request consultations on the availability of alternative tools or alternative assignments for individual students who may not wish to use AI tools.
If you would like assistance with designing assessments for your own teaching context, 
contact the Center for Teaching
.
 How can you adapt and develop assessments to discourage student use of AI tools? 
Some instructors may be interested in preventing the student use of AI tools in their assessments. This may be a difficult task as Beth McMurtrie points out in a 
Chronicle of Higher Education’s Teaching Newsletter
, “If you want to make your assignments AI proof, that’s impossible," (
McMurtrie, 2023
). Effective assessments are closely aligned to course goals and allow students to demonstrate their learning in authentic ways. Assignments that are focused on the specific learning of the course and students’ own learning are also less suited to being written by AI or by another person who is not participating in the course.
Developing a specific prompt that requires students to leverage information learned in the course, including materials on ICON and in-class discussions.
Scaffolding the assignment to include several stages, such as a proposal, an outline, a rough draft, and a final draft. Depending on other factors, such as course size, an instructor might be able to include opportunities for students to receive and comment on peer/instructor feedback at these stages.
Including a metacognitive component in which students describe their research and writing process, what they learned from it, and how they would approach a similar task in the future.
Focusing assessments on current events and recent scholarship not yet included in the AI training data set.
Exploring how an AI responds to your assignment prompt. 
It is not recommended to simply replace existing high-stakes assignments with graded, hand-written, in-class assignments. This may have unintended consequences for students who use technology to provide accommodations and other legitimate assistance in completing coursework. (
CRLT, 2022
)
The Center for Teaching's Handbook for Teaching Excellence provides additional information on 
how to develop authentic assessments
. If you would like assistance with designing assessments for your own teaching context, 
contact the Center for Teaching
.
 What do I need to know about AI browsers and browser plugins? 
These programs are either web browsers or plugins for web browsers that bring generative AI into the same space a student is using to complete an assignment. They can read text displayed in a browser (this includes quiz questions from ICON, Top Hat, and other online platforms) and then suggest or automatically create or select an answer based on what the generative AI believes is the correct answer.
Here are the strategies you can use to adapt your teaching:
Include a statement about the use of these tools in your syllabi and assignments.
Consider alternative ways to assess students' learning that require them to complete tasks outside of or in addition to tasks in ICON, such as oral presentations, visual or multimodal projects, case studies, and journals.
Consider incorporating the use of alternative assessments, higher order questions, and flipped classroom approaches in your teaching.
Use a locked browser with any online quizzes or exams to prevent the use of other applications while testing.
All University of Iowa courses have access to 
Respondus Lockdown Browser
.
Select courses have 
access to Honorlock
.
Use 
Gradescope
 to assess paper-based quizzes and tests in a way that helps save time and gives students consistent feedback at scale.
ITS is monitoring developments in this space, escalating the AI browser topic with the instructional technology vendors we work with, adding a message to instructors in ICON’s quiz page, and blocking the installation of known plugins on university-managed machines that are located in Instructional Technology Centers and testing centers.
 What do I need to know about AI glasses and other wearable 'smart' devices?
Smart glasses offer functions comparable to those of smartphones, but with the appearance of typical glasses. They feature internet connectivity, integrated miniature cameras and speakers, as well as may use a lens-embedded display. Instructors who wish to prohibit smart glasses during assessments as part of standard proctoring practices should clearly communicate this prohibition to students in advance and also remind students immediately prior to the exam. It is important to note that because 
some students may have prescription smart glasses
 instructors should also add a statement like the following to their syllabus and/or assessment instructions at the beginning of the semester, to allow students with these smart glasses to procure alternative glasses before assessments are scheduled:
AI Wearables, such as AI glasses and other “smart” devices are not permitted during quizzes and exams, unless explicitly approved in advance. Students with prescription smart glasses must be prepared to bring standard prescription glasses to quizzes and exams.
Adapted from 
PennState Academic Integrity Resources
 What is agentic AI?
Beyond generative AI is agentic AI. While generative AI involves back and forth interactions between the user and the large language model, an AI agent can take a set of instructions from the user, and then independently complete actions on the user’s behalf. While agentic AI has positive uses, it may also create risks. 
Learn more about agentic AI and how to respond to it
.
The University of Iowa
Office of Teaching, Learning, and Technology
Office of Teaching, Learning, and Technology (OTLT)

2800 University Capitol Centre

Iowa City, IA 52242
319-335-5194
Admin Login
Footer primary
Contact us
Subscribe to our newsletter
Events
About
© 2026 The University of Iowa
Privacy Notice
UI Nondiscrimination Statement
Accessibility
```

**YOUR CODES (University of Iowa):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 4. University of Maine

```
### PRIMARY https://umaine.edu/communitystandards/resources-policies-and-forms/generative-ai-teaching-and-learning-guidelines/
Generative AI Teaching and Learning Guidelines - Community Standards, Rights, and Responsibilities - University of Maine
Skip to main navigation
Skip to site navigation
Skip to content
Apply to UMaine
A-Z
Calendar
Give
Map
News
Careers
myUMaine
Community Standards, Rights, and Responsibilities
Community Standards, Rights, and Responsibilities
Home
Resources, Policies, and Forms
Hazing Prevention
Freedom of Speech
Staff
About
Become a Student
Academics
Research
Athletics
Search...
Prospective Students
Current Student
Faculty & Staff
Community Member
myUMaine
A-Z Directory
News
Calendar
Careers
Map
Quicklinks
Search...
Home
Resources, Policies, and Forms
Hazing Prevention
Freedom of Speech
Staff
Generative AI Teaching and Learning Guidelines
Teaching, Learning, and Artificial Intelligence (AI)
Table of Contents
INTRODUCTION
PURPOSE AND SCOPE
GUIDELINES STATEMENT 
RESPONSIBILITIES
ACCESS AND EQUITY
DATA PRIVACY AND SECURITY
USE OF AI IN TEACHING AND LEARNING
CITATION AND REFERENCING
ACADEMIC INTEGRITY
PROFESSIONAL DEVELOPMENT
REVIEWING AND UPDATING THE GUIDELINES 
INTRODUCTION
In this document we discuss 
generative artificial intelligence
 (generative AI) services and tools. These tools and services can enhance and even automate the creation of content based on a body of existing data and queries. They can be used to create text, code, images, video, sounds, and more. These models use datasets and algorithms to discern patterns and structure to create new content that has a statistically similar structure. As we experiment with these new resources, we should also keep in mind associated privacy, security, legal, and ethical issues that may come with them.
Many industries use generative AI. In addition, software developers and online service providers are embedding AI in more and more products. A growing number of educators from middle school through doctoral programs now perceive roles for generative AI in teaching and learning, particularly, in developing instructional materials as well as in students’ completion of assignments and assessments.
I. PURPOSE AND SCOPE
This document establishes guidelines for the ethical, secure, and responsible use of generative artificial intelligence technologies in the context of teaching and learning at the University of Maine. It provides a framework for all members of the UMaine teaching and learning community, which includes UMaine leadership, instructors, administrative staff, and students.
II. GUIDELINES STATEMENT 
The University of Maine is committed to using AI technologies in an ethical, transparent, and responsible manner. We acknowledge that AI technologies have the potential to significantly enhance student learning and engagement, but we also recognize the importance of protecting student privacy and ensuring that the use of these technologies is consistent with ethical considerations. We are equally committed to preparing students to identify and critically evaluate biases or stereotypes that AI may propagate.
The use of AI technologies in our school aligns with our mission to provide a high-quality education that prepares our students for success in the 21st century. AI technologies have the potential to support personalized learning and help teachers identify areas where students need extra support. They can also support research and writing activities and provide opportunities for students to develop skills related to critical thinking, problem-solving, and digital literacy. The University recognizes that an education in the 21st century includes generative AI literacy as well as proficiency in the use of a range of generative AI systems.  
III. RESPONSIBILITIES 
The following individuals and groups are responsible for the implementation and maintenance of these guidelines:
UMaine leadership: responsible for providing resources, guidance, and support for the implementation of these guidelines
Instructors: responsible for implementing these guidelines in their courses, including providing clear instruction on the ethical and responsible use of AI technologies by their students and teaching assistants. 
Administrative staff: responsible for ensuring that AI technologies are used in compliance with these guidelines, including data privacy and security policies.
Students: responsible for using AI technologies in an ethical and responsible manner, as outlined in these guidelines and communicated to them by their instructors.
IV. ACCESS AND EQUITY 
Equal access to reliable and credible generative AI tools and services will be instrumental in creating an inclusive learning environment for all UMaine students. These tools empower instructors and students, and can enrich educational opportunities, but it is also important to note that these tools may also contain biased and erroneous information. Additionally, they have the potential to retain and reuse private information. (See 
Data Privacy and Security
, below.) 
Generative AI services for use in instruction may, with requisite evaluation and approval, be licensed by the University, college, department, or be assigned at the course level as an instructional resource via the UMaine Bookstore. 
It is also important to note that Generative AI can function as an accessibility resource, both for instructors and students. 
V. DATA PRIVACY AND SECURITY 
Existing University and University System data privacy and security policies also pertain to AI services when those services store or transmit information and data which may or should be protected. Consult Student Records for 
responsibilities relating to official educational records of students
. The UMS has a specific policy and guidelines with regard to: 
Safeguarding FERPA Information when Using Cloud-based Resources in a Course Environment
that governs the use of free and fee-based AI services as part of instruction. As vendors embed AI into their services, instructors must coordinate with UMS Information Technology (IT) to confirm that data protection protocols continue to be followed.
VI. THE USE OF AI IN TEACHING AND LEARNING 
Academic departments, programs, and faculty committees, such as the General Education Committee, should determine the ways in which to incorporate generative AI in the curriculum in accordance with their targeted course, major, and/or minor outcomes.
Instructors should make clear statements in syllabi and/or relevant areas of online course shells in their learning management system about the ways students will use AI in the course as well as the ways the instructor will use AI. For example, instructor expectations and curricula relative to AI could fall into one of these 
categories
:
Require students to use AI
Expect students to use AI to develop content and material to complete assignments
Expect students to use AI to help them generate ideas or approaches for assignments
Expect students to use AI as a means of studying AI in order to understand its capacities, identify the datasets it uses, evaluate its algorithms, etc.
Use minimally to proofread or copy edit assignments to check grammar, syntax, clarity, and consistency 
Forbid use of AI
Students must acknowledge the use of generative AI any time they use it in the context of their process. (See 
Citation and Referencing
, below.) As always, all student work should adhere to UMaine’s established academic honesty policy. (See 
Academic Integrity
, below)  
If an instructor will require or expect students to use generative AI services in a class, the syllabus should indicate the type of tools or mediums they will use. Instructors should be clear about the costs of the use of the tool (if any) as well as any data privacy concerns that may be associated with the use of the tool. 
Similarly, if the instructor uses generative AI services to prepare or teach any part of a course and/or to assess students’ assignments, the syllabus and/or the catalog description of the course should indicate the type of tools or mediums the instructor uses.
Instructors should inform students if they use an AI tool to assess students’ work, and students should have the ability to opt-out and receive direct feedback from the instructor. Any third party tools that use AI to assess student work should be properly vetted. 
VII. CITATION AND REFERENCING 
As mentioned in section 
VI. The Use of AI in Teaching and Learning
, when AI tools are used by a student or an instructor in the context of their teaching and learning, they should acknowledge that use and it should be appropriately cited. Additionally:
AI-generated material, whether it be quoted or paraphrased, should be cited according to the style assigned by the instructor. 
The most frequently used citation styles (MLA, APA, etc.) now include guidance on how to create citations for AI-generated materials. Fogler Library links to them on their 
How to Cite Your Sources Guide
. Students and instructors citing AI-generated material can contact Fogler Library for further guidance.
Failure to properly cite and acknowledge the use of AI-generated material will be considered plagiarism and subject to the disciplinary actions outlined in  the 
Academic Integrity Policy
.
As an addendum to any assignment, instructors may require students to submit a document that explains how the student used generative AI in their work. At the discretion of the instructor, this document may contain a description of the tools used, how each tool was used, specific prompts that were entered into the tool, how the tool and its resources were evaluated, how the work of the tool was incorporated into the final product submitted by the student, and any other relevant information. 
VIII. ACADEMIC INTEGRITY 
The 
UMS Academic Integrity Policy
 is the established and defensible process to manage accountability for academic integrity violations.  Coupled with the 
UMS Student Conduct Code
 (identifies serious or multiple violations), accountability and imposition of effective educational interventions can be fully satisfied.  
We also recognize that we work and study in an ever-changing educational landscape.  Technological advances, expectations to fully collaborate with research partners, and the blurred lines between collaboration and cheating are issues that require us to adapt.  Teaching and learning must adapt to account for the growing field of artificial intelligence, and we 
encourage the ethical and transparent use of artificial intelligence tools to support learning. 
Educational modules should be developed and deployed to assist students with violations in advancing their understanding of academic integrity related to AI.
IX. PROFESSIONAL DEVELOPMENT  
Investing in professional development for UMaine’s teaching and learning community is critical to ensure we have an effective integration of generative AI technologies into our teaching and learning practices. It will be important not only to provide equitable access to Generative AI technologies, but to teach our instructors and students how to use them in responsible ways. Issues of bias and fairness, privacy, transparency and social impact should be discussed throughout.
It is expected that professional development opportunities will be provided by the Center of Innovation in Teaching and Learning (CITL) for UMaine’s instructors.
Instructional opportunities for students can occur within their existing courses, but there should also be opportunities for students to learn how to work with these tools outside of class. Understanding how AI can be used as a tool for students within the context of their coursework will be important, but learning how AI will be incorporated into their discipline or future jobs will also be necessary. 
UMaine will need to provide a variety of resources and support in order to facilitate ongoing learning and development related to AI technologies. These may be best delivered through Fogler Library, IT or other campus resources.  
X. REVIEWING AND UPDATING THE GUIDELINES 
The University Teaching Council (UTC) is charged with keeping these guidelines current. At least once a year, the UTC, or a task force it forms, will assess these guidelines and, through any approach agreed upon by the UTC membership, determine if changes in services, practices, or some other variable has given cause for recommending to the Faculty Senate and the Provost amendments or updates to these guidelines. Between updates, members of the UMaine community are invited to share observations, concerns, or recommendations with the UTC. 
Community Standards, Rights, and Responsibilities
5748 Memorial Union, Rm 315
Orono, Maine
04469

 Tel: 
207.581.1406

 Fax: 
communitystandards@maine.edu
Home
Resources, Policies, and Forms
Hazing Prevention
Freedom of Speech
Staff
⨉
Facebook
LinkedIn
YouTube
Instagram
Apply
Student Resources
Nondiscrimination notice
Privacy Policy
Clery Safety and Security Report
Emergency
University of Maine
 | 
 
Orono
, 
ME
04469
 | 
 
207.581.1865
Top
```

**YOUR CODES (University of Maine):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 5. University of Missouri

```
### PRIMARY https://oai.missouri.edu/chatgpt-artificial-intelligence-and-academic-integrity/
ChatGPT, Artificial Intelligence, and Academic Integrity // Office of Academic Integrity
ChatGPT, Artificial Intelligence, and Academic Integrity
Skip to navigation
Skip to content
MU Logo
University of Missouri
Search
search
Office of Academic Integrity
menu
Home

 For Students
arrow_drop_down
Standard of Conduct
Policy and Procedures
Appeals
Student Resources

 For Instructors
arrow_drop_down
Encouraging Academic Honesty
Preventing Academic Dishonesty
Suspecting Dishonesty in Your Classroom
Faculty Resources
To Report
For Parents
Contact Us
ChatGPT, Artificial Intelligence, and Academic Integrity
ChatGPT, Artificial Intelligence, and Academic Integrity
Students who use ChatGPT and similar tools on assignments without permission, or who use them in improper ways, are violating the academic integrity rules of the University.
Since its launch by OpenAI in late 2022, ChatGPT has inspired many questions related to academic integrity. Like most tools, ChatGPT (and other artificial intelligence products) can be used for purposes both good and bad. There are legitimate ways to use these tools for research, and there are ways to use them to cheat on academic work. This page aims to explain how students can avoid committing academic dishonesty with chatbots and other online tools.
What Is ChatGPT?
According to its creators, ChatGPT is “a model … which interacts in a conversational way. The dialogue format makes it possible for ChatGPT to answer follow up questions, admit its mistakes, challenge incorrect premises, and reject inappropriate requests.”
For example, when preparing this page, the author prompted ChatGPT as follows: “In three sentences, please tell me why academic integrity is important.”
ChatGPT then responded, “Academic integrity is important because it upholds the principles of honesty, fairness, and trust in the academic community. Maintaining academic integrity ensures that students are evaluated based on their own merit and not on dishonest or unethical behavior. Additionally, it helps to preserve the integrity and reputation of academic institutions and the degrees they confer.”
As this exchange illustrates, ChatGPT can often answer relatively simple questions well.
May Students Use ChatGPT and Similar Tools for their Academic Work?
The answer is, “It depends.” If your professor allows you to use ChatGPT, and you use it as permitted, then you are not committing academic dishonesty. This is similar to use of a graphing calculator, which is acceptable as long as the instructor permits it.
Just like a graphing calculator, however, using ChatGPT on assignments is prohibited if the instructor does not allow its use. Students who use ChatGPT and similar tools without permission, or who use them in improper ways, are violating the academic integrity rules of the University.
In the University’s academic policies, we have an entry for “Academic Dishonesty.” You can find it in the 
Registrar’s Academic Calendar, Academic Policies, Academic Dishonesty
.
It states, in part: “Academic honesty is fundamental to the activities and principles of the University. All members of the academic community must be confident that each person’s work has been responsibly and honorably acquired, developed and presented. Any effort to gain an advantage not given to all students is dishonest whether or not the effort is successful.”
Students who use ChatGPT and similar programs improperly are seeking to gain an unfair advantage, which means they are committing academic dishonesty.
In addition, as of August 2023, the University of Missouri explicitly prohibits “unauthorized use of artificially generated content,” which includes, but is not limited to, both “use of artificial intelligence tools or other tools that generate artificial content in taking quizzes, tests, examinations, or other assessments without permission from the instructor” and “submitting work for evaluation as one’s own that was produced in material or substantial part through use of artificial intelligence tools or other tools that generate artificial content without permission from the instructor.”
Can Professors Tell if Students Use ChatGPT?
Sometimes. Tools exist that aim to detect text created by ChatGPT and similar programs. Chances are, the tools that create text will evolve over time, as will the tools designed to detect AI-created text. Students who use generative artificial intelligence improperly put themselves at risk because faculty may discover their behavior. More importantly, by undermining the purpose of assignments, students deny themselves the benefit of learning new material, which is the purpose of taking university courses in the first place.
What’s the Bottom Line?
If you think your instructor would object to your using ChatGPT (or a similar tool) in a certain way, you should not do it. If you are unsure, you should ask your instructor first. If the instructor approves your plan to use an AI tool, then you are not acting dishonestly. If you have any doubt, tell your instructor what tools you used and how you used them.
The Mizzou Honor Pledge states, “I strive to uphold the University values of respect, responsibility, discovery, and excellence. On my honor, I pledge that I have neither given nor received unauthorized assistance on this work.”
To uphold Mizzou’s values, students should commit to doing their own work, without “unauthorized assistance” from humans or machines.
Further Resources:
The University of Missouri Collected Rules and Regulations, 
Section 200.010 (Standard of Conduct)
 (containing a detailed definition of “academic dishonesty” at Section 200.010.C.1)
OpenAI, “Introducing Chat GPT,” at 
https://openai.com/blog/chatgpt
Kalley Huang, “Alarmed by A.I. Chatbots, Universities Start Revamping How They Teach,” N.Y. Times (Jan. 16, 2023), available at 
https://www.nytimes.com/2023/01/16/technology/chatgpt-artificial-intelligence-universities.html
Montclair State University, Office for Faculty Excellence, “Practical Responses to ChatGPT and Other Generative AI,” available at 
https://www.montclair.edu/faculty-excellence/practical-responses-to-chat-gpt/
Authorship:
Ben Trachtenberg, Director, Office of Academic Integrity, March 2023, updated August 2023
Contact us
Office of Academic Integrity
academicintegrity@missouri.edu
Mizzou is an 
equal opportunity employer
.
© 
2026
 — 
Curators of the University of Missouri
. All rights reserved.
Restrictions on Use of University Marks, Identifiers and Content
. 
DMCA/Copyright Information
. 
Accessibility
. 
Privacy policy
.


### SECONDARY https://teaching.missouri.edu/resources/artificial-intelligence-ai/generative-ai-faculty/generative-ai-classroom-guidelines
FETCH-FAILED: HTTP Error 404: Not Found
```

**YOUR CODES (University of Missouri):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 6. University of North Dakota

```
### PRIMARY https://und.edu/academics/provost/faculty-affairs/ai-and-emerging-technology-academic-integrity-resources.html
AI and Emerging Technology Academic Integrity Resources | University of North Dakota
Skip to main content
Open Menu
Close Menu
University of North Dakota
Open Search
Close Search
Close Menu
University of North Dakota
Info For
Admitted Students
Current Students
Families of Current Students
Faculty & Staff
Alumni
Logins
Email
Blackboard
Campus Connection
Employee Self-Service
Hawk Central
Degree Map
Zoom
Directory
Search
Search
Submit
Academics
Admissions
Student Life
Research
Athletics
Majors & Programs
About
Menu
University of North Dakota
Academics
Admissions
Student Life
Research
Athletics
Majors & Programs
About
Request Info
Visit
Apply
Search
Search
Submit
Request Info
Visit
Apply
Search
Submit
Home
Academics
Office of the Provost
Faculty Affairs
AI and Emerging Technology Academic Integrity Resources
Skip Section Navigation
Faculty Affairs
Faculty Affairs
Post-Tenure Review
University Senate
Faculty Forms & Resources
Show/hide children
Annual Evaluations
Course Resources
Conflict Management Services
Courtesy Appointments
Curriculum Resources
Department Chair Handbook
Developmental Leave
Honorary Degrees
Immigration
Promotion & Tenure
Faculty Awards & Recognition
Show/hide children
Fulbright Scholars
Faculty Fellowship Award Opportunities
Scholarships & Fellowships
UND Connect
Show/hide children
Previously Funded UND CONNECT Projects
Hawks in Harmony
New Faculty Resources
Show/hide children
New Faculty Orientation
Artificial Intelligence Use in the Classroom
Contact Us
AI and Emerging Technology Academic Integrity Resources
Before the Course Begins
Faculty should p
rovide clear expectations
regarding
academic integrity and AI. Clarify for students your expectations
regarding
using any generative AI tools or applications. State these expectations clearly on
 your course syllabus and
in
any assignment prompts. Explain the consequences for the students if your expectations
regarding
the use of generative AI tools are not met.
UND does not have an AI policy. If an instructor believes a student has used AI
for
an assignment or exam in violation of a
course
policy, it is addressed through
UND’s Academic Integrity Policy. Academic concerns may be reported via the 
Academic Integrity Concern Report
.  
Sample Syllabus Statement from UND
Please feel free to adapt these sample statements for your courses.
Open All
 Sections
Yes, AI Use is Always Allowed in the Course
(
Open
 this section)
I expect you to use AI (ChatGPT and image generation tools, at a minimum), in this
 class. In fact, some assignments will require it. Learning to use AI is an emerging
 skill, and I provide tutorials in Blackboard about how to use them. I am happy to
 meet and help with these tools during office hours or after class.
Be Aware of the Limits of ChatGPT:
If you provide minimum effort prompts, you will get low quality results. You will
 need to refine your prompts in order to get good outcomes. This will take work.
Don’t trust anything it says. If it gives you a number or fact, assume it is wrong
 unless you either know the answer or can check in with another source. You will be
 responsible for any errors or omissions provided by the tool. It works best for topics
 you understand.
AI is a tool, but one that you need to acknowledge using. Please include a paragraph
 at the end of any assignment that uses AI explaining what you used the AI for and
 what prompts you used to get the results. Failure to do so is in violation of the
 academic honesty policies.
Be thoughtful about when this tool is useful. Don’t use it if it isn’t appropriate
 for the case or circumstance.
Statement courtesy of Dr. Ethan Mollick, Wharton School, University of Pennsylvania
Yes, AI Use is Sometimes Allowed, But
(
Open
 this section)
Since we recognize the potential for enhancing the educational process, the use of
 AI-generated content in this class is acceptable in specific circumstances. The use
 of AI tools must be acknowledged just like the use of any other software package.
 For example, I used Grammarly to edit this syllabus. You might also use ChatGPT or
 help outline an essay or organize your notes.
However, because generative AI can copy work without using citations, students are
 still responsible for ensuring the originality, integrity, and accuracy of their work.
 Do not use AI-generated sources, as they are often formatted incorrectly or make up
 sources entirely. Violation of academic honesty standards, including plagiarism, is
 prohibited under the UND Code of Student Life.
UND does not have an AI policy because the use of AI is discipline and course-specific.
 The policy stated above applies only to the course. Please consult the syllabus for
 each of class for its AI Policy.
Statement courtesy of Dr. Jayne Kinney, Assistant Professor, IS 121 Introduction to
 American Indian Studies 
No, AI Use is Never Allowed
(
Open
 this section)
Plagiarism is an increasingly common form of academic misconduct. All the following
 are considered plagiarism:
Using any AI Software (e.g. Chat GPT) to write part or all of your assignment. NOTE:
 AI can be used to spellcheck and help with grammar. It should not be providing original
 thoughts.
Statement courtesy of Dr. Ashley Fansher, Assistant Professor of Criminal Justice
Resources
UND AI Assignment Repository
UND AI Guidance
"Student Assessment of Ethical AI Use"
 resource (Bertram Gallant, 2025)
"Generative AI and Policy Development: Guidance from the MLA-CCCC Task Force"
Frequently Asked Questions
I suspect a student used AI inappropriately. What should I do?
If you believe a student has used AI in a way that violates course or university policies,
 address the concern directly with the student and follow all departmental, college,
 and syllabus-based academic integrity policies. If you are unsure which policies apply,
 consult your department Chair. Instructors retain discretion over grade-related consequences.
Instructors are also encouraged to report the incident to the Community Standards
 & Care Network (CSCN) and provide any relevant documentation. CSCN can help advise
 on appropriate next steps.
What happens when I report a student to CSCN for AI-related academic integrity concerns?
Most first-time reports of inappropriate AI use do not result in formal conduct charges.
 CSCN typically notifies the student that a report has been received and explains that
 future incidents may result in a student conduct process.
If the AI misuse is particularly serious, a first-time report may be referred directly
 to student conduct.
Do I have to report AI misuse, or can I handle it myself?
Reporting to CSCN is not required. However, sharing even low-level or first-time AI-related
 concerns allows the University to identify patterns across courses and better support
 student learning and accountability. Handling cases only at the course or department
 level may unintentionally allow repeated misuse of AI across multiple classes.
What if a student repeatedly misuses AI after being reported?
Subsequent reports of academic dishonesty, including AI misuse, are typically referred
 to a student conduct process. This process is designed to be educational and supportive
 of student development. Possible outcomes may include academic integrity education
 and conduct probation. In rare cases, suspension may occur.
What is my responsibility to investigate suspected AI misuse?
Faculty should use professional judgment and follow departmental or college guidance
 when responding to suspected AI misuse. Any academic consequences should be based
 on clear evidence and documented justification. Students retain the right to pursue
 an academic grievance.
If a report results in formal conduct charges, CSCN staff are responsible for the
 investigation, with faculty collaboration playing an important role.
Questions
if you have questions on academic integrity and potential misuse of AI resources,
 please contact the 
Community Standards & Care Network
. 
Vice Provost for Faculty Affairs
O'Kelly Hall Room 8 
221 Centennial Drive Stop 8006
Grand Forks ND 58202-8006
P 701.777.4138
UND.facultyaffairs@UND.edu

 We use cookies on this site to enhance your user experience.
 

 By clicking any link on this page you are giving your consent for us
 to set cookies, 
Privacy Information
.
 
I Agree
 to cookie policy
Exit Site
Back to Top
Ready 
to Enroll?
Request Information
Schedule a Visit
Apply Now
UND.info@UND.edu
701.777.3000
Instagram
Facebook
LinkedIn
YouTube
TikTok
Contact UND
Campus Map
Events Calendar
Community & Belonging
Explore Programs
Employment
Make a Gift
Campus Safety (SafeUND)
University of North Dakota
©
 2026 University of North Dakota - Grand Forks, ND - Member of ND University System
 Accessibility & Website Feedback
Terms of Use & Privacy
Notice of Nondiscrimination
Student Disclosure Information
Title IX
©
```

**YOUR CODES (University of North Dakota):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 7. University of Rhode Island

```
### PRIMARY https://uri.libguides.com/ai/instructors
Resources for instructors - Understanding & Using AI - LibGuides @ URI at University of Rhode Island
Skip to Main Content
University of Rhode Island

 University Libraries 
Facebook
Twitter
YouTube
University of Rhode Island Libraries
LibGuides @ URI
Understanding & Using AI
Resources for instructors
Search for Databases and Guides

 Search
 
Understanding & Using AI: Resources for instructors
A brief introduction to generative artificial intelligence covering how it works, types of tools, and tips for responsible AI-use.
Getting Started
Cautions & caveats
How to use AI tools
Types of tools
Citing your use of AI tools
Where to learn more
Resources for instructors
Introduction
Faculty Senate Language on Faculty Copyright and AI
Crafting AI policies
Discussion prompts: Talking about AI in the classroom
What about AI detectors?
Suggested reading

 Need Help?
 

 Research Help
 
Email Me
Click on the black arrow to open the chat in a new window. 
If we're not online, please email us at researchhelp@uri.edu. Please allow 1-2 business days for a response.
Contact:
Kingston: (401) 874-2653 
Narragansett: (401) 874-6161
Social:
Facebook Page
Twitter Page
YouTube Page
Instagram Page

 Introduction
 
This page is specifically geared toward instructors; it collects resources to help you craft AI policies, discuss AI use with your students, and find further readings if you want to dive deeper. 

 Faculty Senate Language on Faculty Copyright and AI
 
In February 2026, URI's Faculty Senate and the Office of the General Counsel created a syllabus statement allowing instructors to prohibit the distribution of course content and audio- or video-recordings of course-related activities to others, including AI tools. For your convenience, the full document is linked below.

 URI Copyright Notice FINAL (2026)
 
This link opens in a new window
This is the final approved copyright language developed by the URI Faculty Senate Executive Committee and the Office of General Counsel, intended to be incorporated into syllabi as needed.

 Syllabus Statements & Design (URI Office for the Advancement of Teaching and Learning) 
This link opens in a new window
This link opens in a new window

 The Office for the Advancement of Teaching and Learning provides a variety of syllabus language examples that can be adapted as needed for courses. This includes language on AI use and language prohibiting providing access to course materials to AI tools.
 

 Crafting AI policies
 
Educators across disciplines are grappling with how to negotiate and set boundaries on AI-use in their classrooms. As you consider what policies, guidelines, and restrictions feel authentic and meaningful for your course context, you may find it helpful to browse language from other instructors for inspiration. Below, find URI's recommended language, as well as a collection of syllabus policies on AI use from instructors from across disciplines and around the world. 

 Syllabus Statements & Design (URI Office for the Advancement of Teaching and Learning) 
This link opens in a new window
This link opens in a new window

 On the "Optional Language for Your Syllabus" tab, there are several options for AI use policies, as well as a copyright policy statement if you wish to prohibit uploading of course materials to AI tools or other external services.
 

 Syllabus Policies for AI Generative Tools (Lance Eaton) 
This link opens in a new window

 A multidisciplinary collection of syllabus policies created by instructors across disciplines at a range of institutions. Collected by Lance Eaton, Senior Associate Director of AI in Teaching and Learning at Northeastern University.
 

 Discussion prompts: Talking about AI in the classroom
 
Having frank and open conversations with students about AI can be helpful in building consensus in your class community. Below, you'll find some prompts to help you begin engaging students in these conversations in your own classroom.
What does responsible AI-use mean to you? 
What skills does a person need to be able to use AI ethically and effectively? How would you define AI-literacy?
How (if at all) do you think AI should be incorporated into your college curriculum?
Have you used AI tools to help you learn or master new content? Share how you've leveraged these tools to help you learn.
In what ways do you see AI becoming relevant for your chosen career path or area of interest? How has this changed your perception of what skills you need to develop in order to succeed in your chosen career?
In your own use of AI tools what capacities and limitations have you noticed? What have you found that AI tools do really well and what shortcomings have you discovered?
What troubles you about AI? Do you have any concerns you've been grappling with? Jumping off points for discussion could include data privacy, algorithmic bias, labor, the digital divide, etc. 

 What about AI detectors?
 
As of June 2026, URI does not provide a subscription to any AI detection software. 
If you are considering AI detection tools, it's important to establish the following before proceeding:
Have you provided clear guidance to your students on the use of AI in your course?
 Making expectations clear is key to helping students understand what role(s) AI can play in their work in the course. It is helpful to include written guidance with each assignment so the information is readily accessible.
Acceptable levels of AI use
: What level of AI assistance will you accept? Is the use of AI-assisted grammar tools acceptable in your course? 
Reliability
: Has the AI detection tool been evaluated for effectiveness by other users or researchers? Search for articles discussing any tool's reliability before making a decision.
Protection of intellectual property
:
 
If you are planning on uploading student work to an AI detection tool, do you have permission to upload that work?
What happens to that student's work once it has been uploaded? Does it become part of the training data without the student's consent?
Protection of student information
: Has the content been anonymized to avoid conflicts with regulations?
Bias
: Much of AI's training data is from content written by English speakers, and the algorithms prioritize certain language based on the programmers' preferences. If English is not a student's first language, and/or if they have used certain features built into the tools they're using to write or translate their words, will this assistance show up as AI-generated? 
Evidence
: Does the tool provide clear evidence for its claims in the output?
Companies trying to sell AI detection software will make claims that may not be supported by evidence
. Thoroughly vet any tools' claims before proceeding, and make sure that your use of AI detectors doesn't compromise students' ownership of their work or violate University policy.

 Suggested reading
 

 AI Detectors Don’t Work. Here’s What to Do Instead. (n.d.). MIT Sloan Teaching & Learning Technologies. 
This link opens in a new window

 Baron, N. (2023, October 3). Advice | AI in the Classroom Is a Problem. Professors Are the Solution. The Chronicle of Higher Education. 
This link opens in a new window

 Darby, F. (2023, June 27). Advice | 4 Steps to Help You Plan for ChatGPT in Your Classroom. The Chronicle of Higher Education. 
This link opens in a new window

 Lo, L. S. (2023). The CLEAR path: A framework for enhancing information literacy through prompt engineering. The Journal of Academic Librarianship, 49(4), 102720. 
This link opens in a new window

 Mintz, S. (2023, December 4). Why Higher Ed Needs to Be Disrupted. Inside Higher Ed. Retrieved January 5, 2024 
This link opens in a new window

 Mollick, E. (2023, September 16). Assigning AI: Seven Ways of Using AI in Class. 
This link opens in a new window

 Pindell, N. (n.d.). The Challenge of AI Checkers | Center for Transformative Teaching | Nebraska. Retrieved December 8, 2025 
This link opens in a new window

 Salman, J. (2023, June 8). How educators are using AI in the classroom. The Hechinger Report. 
This link opens in a new window

 Young, J. R. (2023, October 10). How to Help Students Avoid Getting Duped Online—And by AI Chatbots—EdSurge News. EdSurge. 
This link opens in a new window
<< 
Previous:
 Where to learn more
Last Updated:
Jun 9, 2026 1:23 PM
URL:
https://uri.libguides.com/ai
 Print Page
Login to LibApps
Report a problem
Subjects: 
General & Reference
University
Leadership
Diversity and Inclusion
Global
Campuses
Safety
Campus Life
Housing
Dining
Athletics and Recreation
Health and Wellness
Events
Academics
Undergraduate
Graduate
Advising
Libraries
Internships
Facebook
Instagram
Twitter
YouTube
Copyright © 
University of Rhode Island
 | University of Rhode Island, Kingston, RI 02881, USA | 1.401.874.1000
URI is an equal opportunity employer committed to the principles of affirmative action. 
Work at URI
```

**YOUR CODES (University of Rhode Island):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 8. University of South Carolina

```
### PRIMARY https://sc.edu/about/offices_and_divisions/cte/teaching_resources/generative_ai/genai_teaching_guidelines/
Guiding Principles for AI Use in Teaching - Center for Teaching Excellence | University of South Carolina
Skip to Content
University of South Carolina Home
Search University of South Carolina
University of South Carolina Navigation
Search sc.edu
Gateways For: 
STUDENTS 
FACULTY & STAFF
ALUMNI
PARENTS & FAMILIES
Calendar
Map
Directory
Apply
Give
Search sc.edu
Search
Center for Teaching Excellence
About
Meet Our People
Meet Our Partners
News
2016 News Archive
2015 News Archive
2017 News Archive
Newsletter
Share Your Thoughts
Giving
Consultations
Workshops
Blackboard Learn Ultra Course View (UCV)
Teaching Week Sessions
Video Archives
Programs
Certificates of Completion
Entering Mentoring
EXCITE Active Learning
Fostering Proactive Learning Environments
Integrative and Experiential Learning
Mental Health and Well-being Competency
Teaching and Learning with Generative Artificial Intelligence
Teaching Towards Inclusive Excellence
Teaching with the Library
Understanding USC Student Populations
Communities of Practice
Coordinators and Instructors of Large Undergraduate Courses (CILUC CoP)
Generative Artificial Intelligence Community of Practice (GenAI CoP)
Universal Design for Learning Community of Practice (UDL CoP)
Virtual Environments Community of Practice (VE CoP)
Faculty in Focus Ambassadors
2025-2026 Faculty Ambassadors
Generative Artificial Intelligence (GenAI)
Agentic AI for Research, Teaching, and Operations Workshop Series
GenAI Design Studio
GenAI Community of Practice (GenAI CoP)
GenAI Showcase
Provost's AI Teaching Fellowship
Provost's AI Teaching Fellowship Application
Teaching and Learning with GenAI Webinar Series
Teaching with AI Course
Teaching with AI Course Enrollment Form
Graduate Teaching/Instructional Assistant (GTA/IA)Training
GTA/IA Orientation
GRAD 701
TA Training Frequently Asked Questions (FAQs)
GTA/IA Workshops
Video Archives
Grants
GTA/IAs Teaching Resource Development Grant
GTA/IA Teaching Resources Grant Application
Innovative Pedagogy Grant
Provost's AI Teaching Fellowship Grant
UDL Course (Re)Design Grant
Winter Session Online Course Development Grant
Past Grant Recipients
New Faculty Academy
New Faculty Academy 2025-2026 Presentations
Preparing Future Faculty
PFF Award Recipients
Short Courses
Designing and Delivering Effective Online Courses
Register For Designing and Delivering Effective Online Courses
Foster Student Learning Through Effective Teaching
Register for Foster Student Learning through Effective Teaching Course
Foundations of Online Teaching
Foundations for Online Teaching Short Course Application
Reflective Teaching Practices for Medical Educators (RTPforME)
RTPforME Summer 2026 Application
Technology for Online Teaching and Learning
Transforming Conflict Through Dialogue Learning Series
Universal Design for Learning in Practice
Teaching Recognition
Garnet Apple Award
2026 Award Winners
2025 Award Winners
2024 Award Winners
2023 Award Winners
2022 Award Winners
2021 Award Winners
2020 Award Winners
2019 Award Winners
2018 Award Winners
2017 Award Winners
2016 Award Winners
Thank-A-Teacher Program
Fall 2025 Recognition
Spring 2025 Recognition
Fall 2024 Recognition
Spring 2024 Recognition
Fall 2023 Recognition
Spring 2023 Recognition
Fall 2022 Recognition
Digital Accessibility Appreciation Program
Universal Design for Learning (UDL)
UDL in Practice Short Course
UDL Community of Practice
UDL Course (Re)Design Grant
UDL Workshops
Special Events
Adjunct Faculty Orientation
Adjunct Faculty Orientation 2025
Adjunct Faculty Orientation 2024
CAREolina
CAREolina Educator Toolkits
CAREolina Resources
First-Generation Symposium
GenAI Showcase
GTA/IA Orientation
New Faculty Orientation
New Faculty Video Library
New Faculty Orientation 2025 Presentations
Oktoberbest
Oktoberbest 2026 Call for Proposals
Oktoberbest Proposal Submission Form
Distributed (Online) Learning
Online Course Quality Review Initiative
Get Started Teaching Online
Online Course Design
Overview of HIDOC
Step 1: Learner Analysis
Step 2: Learning Outcomes
Step 3: Course Structure
Step 4: Assessments & Activities
Step 5: Instructional Materials
Step 6: Technology & Tools
Step 7: Online Learning Support
Step 8: Continuous Improvement
Online Course Development
Online Course Delivery
Quality Standards for Online Courses (QSOC)
Video and Multimedia Support
Video and Multimedia Support Request
Test Proctoring
Online Teaching Resources
Syllabus Templates and Sample Syllabus Statements
Teaching Online – Short Courses
Consultations
Blackboard Learn
Blackboard Ultra Course View (UCV) FAQs
Blackboard Learn and Technology Training Sessions
Blackboard Learn Ally
Digital Accessibility
Course Accessibility Checklist
Digital Accessibility Appreciation Program
Active Learning in Online Courses
Grading and Testing Online
Online Course Delivery Feedback
Resources for Online Learners
Frequently Asked Questions (FAQs)
Professional Memberships in Online Education
Quality Matters
Online Learning Consortium at USC
Graduate Student Teaching Development
Graduate Teaching/Instructional Assistant (GTA/IA) Training
Preparing Future Faculty
Consultations
Teaching Resources
Core Principles of Quality Teaching
Digital Accessibility
Blackboard Learn
Course Design, Development and Delivery
Course Design and Development
Active Learning
Examples of Active Learning Strategies
Active Learning in Online Courses
Digital Accessibility
Learning Outcomes
Program Specific Examples
Seven Principles for Good Practice in Undergraduate Education
Strategies to Effectively Teach First-Generation Students
Course Delivery
Classroom and Teaching Logistics
Handling Classroom Distractions
Help with Student Issues
Make Your Lab Run Smoothly
Manage Classroom Discussions
Manage Your Time 
Teaching Your First Class
Distributed (Online) Learning
Grading and Assessment Toolbox
USC Grading Standards and Guidelines
What is a Grade?
Grading as a Fair Teaching Tool
Before You Begin Grading
Techniques for Making Grading Efficient While Remaining Objective 
Rubrics: A Comprehensive Guide
Types of Rubrics
How to Create a Rubric
Best Practices
Blackboard Rubrics Tools
Examples and Resources
Importance of Providing Meaningful Student Feedback
Grading and Testing Online
Improving Fairness, Grade Challenges, and Late Work
Final Exam FAQs
Technology Tools and Resources
Designing and Delivering PowerPoint Presentations
Technology Tools and Resources
Universal Design for Learning (UDL)
Generative Artificial Intelligence (GenAI)
GenAI Teaching Guidelines
Applying Guiding Principles
GenAI Resources
GenAI Design Studio
Agentic AI for Research, Teaching, and Operations Workshop Series
Teaching and Learning with GenAI Webinar Series
Teaching with AI Course
GenAI Community of Practice (GenAI CoP)
Provost's AI Teaching Fellowship
GenAI Showcase
Classroom Feedback
Classroom Observation
Midterm Student Feedback
Peer Observation Training for Faculty
Syllabus Templates
Universal Design for Learning (UDL)
Virtual Environments
Virtual Reality Apps Library
Virtual Environments Equipment Request Form
Virtual Environments Accessibility Guidelines
Virtual Environments Community of Practice (VE CoP)
Connect with Us
Tools & Resources
Calendar
Map
Directory
Apply
Give
Student Gateway
Faculty & Staff Gateway
Parents & Families Gateway
Alumni Gateway
Center for 
Teaching Excellence
SC.edu
About
Offices and Divisions
Center for Teaching Excellence
Teaching Resources
Generative Artificial Intelligence (GenAI)
GenAI Teaching Guidelines
Center for Teaching Excellence
About
Consultations
Workshops
Programs
Special Events
Distributed (Online) Learning
Graduate Student Teaching Development
Teaching Resources
Connect with Us
Generative Artificial Intelligence (GenAI)
GenAI Teaching Guidelines
GenAI Resources
GenAI Design Studio
Agentic AI for Research, Teaching, and Operations Workshop Series
Teaching and Learning with GenAI Webinar Series
Teaching with AI Course
GenAI Community of Practice (GenAI CoP)
Provost's AI Teaching Fellowship
GenAI Showcase
Applying Guiding Principles
Guiding Principles for AI Use in Teaching
Artificial intelligence (AI) is rapidly changing the nature and work of teaching in
 higher education.
Drawing from the 
Provost’s 2024-2025 AI Task Force Report,
 the following principles provide a guide for ethical, effective, and human-centered
 use of AI in teaching.
They also reflect USC’s continued commitment to academic integrity, innovation, and
 providing students with high-quality and meaningful educational experiences.
Expand all
1. Use AI to support teaching, not replace engagement.
Effective teaching
 still depends on faculty presence, expertise, and interaction with students.
While AI tools can streamline and support certain instructional efforts, faculty should
 leverage their knowledge and judgment to determine whether, when, and how AI can best
 enrich student course experiences, critical thinking, and learning.
2. Communicate clear expectations for AI use in your courses.
At a minimum, faculty must convey in their 
course syllabi
 what is allowed or prohibited, as well as any responsibilities students have for
 documenting their AI use.
Given the varied types and ever-changing applications of AI, faculty should also encourage
 ongoing, context-specific, and frank conversations with students to provide necessary
 guidance and prevent confusion or misunderstanding.
3. Be transparent about your own use of AI.
Faculty can model self-reflective, responsible, and ethical AI practices for their
 students as well as their colleagues.
If AI was used to develop course materials, create assessments, or generate feedback,
 faculty should be forthcoming and prepared to discuss the rationale, scope, and implications
 of its use.
Transparency of this sort fosters trust and helps reinforce community norms about
 AI use.
4. Review and verify all AI generated content.
AI tools are powerful but imperfect.
They can introduce or be premised on errors, bias, and misinformation.
Faculty should always review and edit AI outputs before sharing them with students
 or relying on them in teaching to ensure their accuracy, quality, and appropriateness.
5. Protect student privacy and data.
Student work as well as personal and institutional data should never be uploaded into
 public AI tools, which may store or reuse this information.
AI use also elicits a number of social, legal, and ethical questions for education,
 research, and the workplace worthy of consideration.
University-approved AI tools satisfy privacy and security standards for faculty use,
 and the 
Garnet AI Foundry
 website maintains a current list of approved tools and integrations.
6. Promote critical awareness and responsible use of AI.
Rather than police and penalize AI use, help students develop AI literacy so they
 are equipped to scrutinize AI outputs, recognize potential errors or bias, and consider
 the appropriateness of AI within their disciplines and lives.
AI detection tools are notoriously unreliable, and the insights and skills associated
 with AI literacy will help students use AI responsibly in their academic and future
 professional contexts.
7. Continue building your own AI literacy.
By continuing to develop their own understanding of AI, faculty can better adapt their
 teaching and support their students.
The Center for Teaching Excellence offers 
professional development resources and sponsors communities of practice
 for AI users across campus.
Faculty should also explore opportunities for engagement through their professional
 associations as the possibilities, value, and implications of AI use vary across disciplines.
 
The 
Garnet AI Foundry
 serves as USC’s central hub for AI innovation, collaboration, and support
 for faculty, staff, and students
.
These guidelines provide a foundational framework for the appropriate use of AI in
 teaching at USC, recognizing that the technologies and considerations surrounding
 AI continue to evolve. Faculty and academic units are encouraged to adapt these guidelines
 to their particular circumstances and considerations. 
For practical strategies and examples to apply these principles, explore 
Applying the Guiding Principles
.
 Indeed, regular engagement of this sort is an essential part of creating the shared
 community and culture within which AI can be thoughtfully and effectively used.
Applying the Guiding Principles
Center for
 Teaching Excellence
Location
Contact
Give
Calendar
Social Media
USC Facebook
USC Instagram
USC X
Colleges & Schools
Arts and Sciences
Business
Education
Engineering and Computing
The Graduate School
Hospitality, Retail and Sport Management
Information and Communications
Law
Medicine
Medicine (Greenville)
Music
Nursing
Pharmacy
Public Health
Social Work
South Carolina Honors College
Palmetto College
Offices & Divisions
Employment
Undergraduate Admissions
Financial Aid and Scholarships
Bursar (fee payment)
Veterans and Military Services
Disability Resources
Access and Opportunity
Human Resources
Law Enforcement and Safety
University Libraries
All Offices and Divisions
Tools
Carolina Alert
Campus Email
my.sc.edu
Blackboard
Campus Safety and Wellness
PeopleSoft Finance
©
University of South Carolina
Privacy
Student Consumer Information
Student Consumer Information
Transparency Initiative
Civil Rights and Title IX
Digital Accessibility
Contact
Challenge the conventional. 
Create the exceptional. 
No Limits.
©


### SECONDARY https://sc.edu/about/offices_and_divisions/student_conduct_and_academic_integrity/academic_integrity/artificial_intelligence/
Artificial Intelligence and Academic Integrity at USC - Student Conduct and Academic Integrity | University of South Carolina
Skip to Content
University of South Carolina Home
Search University of South Carolina
University of South Carolina Navigation
Search sc.edu
Gateways For: 
STUDENTS 
FACULTY & STAFF
ALUMNI
PARENTS & FAMILIES
Calendar
Map
Directory
Apply
Give
Search sc.edu
Search
Student Conduct and Academic Integrity
Academic Integrity
Instructors
Promoting Academic Integrity
Students
Artificial Intelligence
Make a Report
Report Hazing
Records Check
Administrative Conferences and Hearings
Good Samaritan Policy
Conduct Administrative Conference
Honor Code Administrative Conference
Carolina Judicial Council Hearing
Virtual Conferences and Hearings
Student Organization Cases
Organization Violations
Attorneys and Advisors
Case Outcomes
Code of Conduct Outcomes
Honor Code Outcomes
Restorative Justice Conferences
Responsible With Diversion
Appeals
Interim Actions
About Us
Our Staff
Join Carolina Judicial Council
Location
Tools & Resources
Calendar
Map
Directory
Apply
Give
Student Gateway
Faculty & Staff Gateway
Parents & Families Gateway
Alumni Gateway
Student Conduct
 and 
Academic Integrity
SC.edu
About
Offices and Divisions
Student Conduct and Academic Integrity
Academic Integrity
Artificial Intelligence
Student Conduct and Academic Integrity
Academic Integrity
Make a Report
Records Check
Administrative Conferences and Hearings
Interim Actions
About Us
Instructors
Students
Artificial Intelligence
Artificial Intelligence and Academic Integrity at USC
Artificial Intelligence is an evolving technology that is being used in a variety
 of ways across numerous disciplines and industries. There are countless uses for artificial
 intelligence and as our community becomes more familiar with this technology this
 office seeks to help educate Gamecocks on how artificial intelligence impacts our
 standards of Academic Integrity as defined by the 
Honor Code
.
The University of South Carolina’s Honor Code is fully equipped to address academic
 integrity violations involving artificial intelligence. Existing policies apply regardless
 of the tools used, meaning the use of AI in ways that violate course rules or misrepresent
 authorship can be investigated and adjudicated under the current Code.
Artificial Intelligence and the Honor Code
Like all reported alleged violations of the Honor Code student behavior and assignment
 submissions are reviewed by the Office of Student Conduct and Academic Integrity to
 find whether it is more likely than not- by a preponderance of the evidence that the
 student's behavior or work violates one or more of the Honor Code's policies.
Syllabus statements and assignment directions may be used in addition to the language
 in the Honor Code to either support or negate a violation of the Honor Code.
Here are examples of rationales used when a student has violated the Honor Code by
 using artificial intelligence.
Expand all
Cheating
Defined as:
 Improper collaboration or unauthorized assistance in connection with any academic
 work.
Using a chatbot (ChatGPT, CoPilot, Gemini etc.) to complete a discussion post, essay,
 or research paper in its entirety.
Using a chatbot to solve an equation or generate a line of code without the permission
 to do so by the instructor of record.
Using an artificial intelligence powered editor (Grammarly, ChatGPT, CoPilot etc.)
 to edit an assignment submission in its entirety.
Plagiarism
Defined as: 
Use of work or ideas without proper acknowledgment of source. 
Using artificial intelligence to find sources for research without verfiying the source
 exists before using it in academic work.
Failing to correct a citation generated by artificial intelligence.
Using an editor like Grammarly to edit an entire document not realizing that it edited
 quotes and parapharsed statements making the information an inaccuarate representation
 of the source material.
Falsificaiton
Defined as: 
Misrepresenting or misleading others with respect to academic work or misrepresenting
 facts for an academic advantage.
Using artificial intelligence to fabricate a doctor's excuse and using it to justify
 an absence.
Using any artificial intelligence on an assignment in a course or on an assignment
 that specifically denotes artificial intelligence as an unauthorized resource.
Complicity
Defined as: 
Assisting or attempting to assist (through intentional or unintentional action) another
 in any violation of the Honor Code.
Failing to report another student after they share in a group chat that they used
 ChatGPT to generate their entire reflection essay.
Note: 
This is not an exhaustive list and some of these examples may be permissible in some
 courses or contexts. According to the Honor Code "When a student is uncertain as to
 whether conduct would violate this Honor Code, it is the responsibility of the student
 to seek clarification from the appropriate faculty member or instructor of record."
How We Investigate Artificial Intelligence Use for Violations of the Honor Code
Violations involving AI are reviewed under the 
same process
 as any other academic integrity case. This includes:
Instructor reporting the concern
Student receiving notice and a chance to respond
Fair review of evidence
Administrative and educational outcomes (if applicable) based on the nature of the
 violation
You can learn more about how the process works on the 
Academic Integrity Process page
.
What to Expect
Expand all
Questioning the Process
In our one on one meetings with students reported for alleged violations of the Honor
 Code regarding their use of artificial intelligence we focus our conversation on how
 the student did their work. We ask questions like, "Did you use any online assistance
 to complete your assignment?" or "How long did you work on this assignment? Was it
 in one sitting or over the course of several days?"
It can also be helpful to get an understanding of what the student used to edit their
 work or how they gathered resources. We may ask, "Did you use any software to edit
 your paper?" or "Could you walk me through your process so we can determine if a tool
 you used may have been powered by artificial intelligence?"
Document Version History
We encourage all students to use their Microsoft Office 365 accounts to complete their
 course work. This is a good practice to save work but, it also creates a version history
 that can help prove or disprove any wrongdoing.
It is common practice for this office to request original document access via a shared
 collaborator link from a student's work in Office 365. We review the version history
 with the student and look for patterns in the creation of the document that may give
 insight into the student's process. Large portions of text that have been copied and
 pasted for example could be cause for concern if the information copied and pasted
 is not cited or appears to be information generated elsewhere to be passed off as
 the student's work. 
Version history can also be helpful in showing a student's full working process. We
 can see how they edited their work, how long it took them to complete the work, and
 if information was typed by the student as opposed to being copied from somewhere
 else.
Comparison to Artificial Intelligence Samples
To get a sense of whether or not a student may have used artificial intelligence to
 complete their work we may consult with ChatGPT or CoPilot via chat (as these are
 currently licensed by the University of South Carolina and FERPA compliant if being
 used with a University of South Carolina account) to see how it would respond to the
 same prompts or questions as what the student was asked to do in an assignment not
 being reported for improper use of artificial intelligence. 
By doing this we can get a baseline for patterns, sources, phrasing, etc. that may
 show a strong correlation to a student's work which would warrant more questions to
 the student to figure out why and how these similarities exist. 
This is not a certain means to prove a student used artificial intelligence in their
 work but, it does provide a line of questions to get to a more certain finding either
 for or against a violation of the Honor Code.
Database of Artificially Generated Material
Each case in the Office of Student Conduct is FERPA protected, and no identifiable
 information is shared from one student to another or any other party without the written
 consent of each alleged student in each case.
Notes from every case, along with supporting documents, and student testimony are
 logged in our case management software and allow our staff to easily search for patterns
 within colleges, courses, majors, and other demographics. We log all cases related
 to artificial intelligence with tags that allow our staff to quickly pull information
 and compare students' work and accused use of artificial intelligence to that of past
 students who have also been accused.
We use this information to provide fair and consistent treatment under the authority
 of the Honor Code so that students reported for similar concerns receive similar outcomes.
Faculty Artificial Intelligence Resources
To reduce confusion and support academic honesty, we encourage instructors to set
 clear guidelines on AI use in syllabi and assignments. Here are some example statements:
“Use of AI tools like ChatGPT is allowed for brainstorming or grammar checks, but
 must be cited. Do not use AI to generate full answers or essays.”
“All work must be your own. The use of AI tools to complete or assist with assignments
 is not permitted.”
Need more support? Visit our 
Instructor Resource Page
 for sample policies, classroom strategies, and training materials.
If you have a question or concern not directly addressed on this webpage, contact
 us at 
osc@sc.edu
Faculty Frequently Asked Questions
Expand all
What happens to a student found Responsible for violating the Honor Code by using
 artificial intelligence?
Students found responsible for violating the Honor Code as it relates to artificial
 intelligence recieve outcomes consistent with those who violate the Honor Code in
 other aspects by receiving some combination of administrative and educational outcomes.
 
Most commonly students with only one violation of the Honor Code are placed on 6 months
 of Conduct Probation and must complete either the Academic Integrity Workshop or Artificial
 Intelligence Module.
Both the Workshop and the Module are free, asynchronus, online course administered
 via Blackboard. Both also feature several assignments that allow students the opportunity
 to reflect on their use or misuse of artificial intelligence and exposes them to some
 ethical questions to consider when they are debating their use as well as tips on
 how to avoid future violations of the Honor Code regarding their use of artificial
 intelligence as well as other types of violations.
For more examples of case outcomes related to Honor Code violations click 
here
.
What other resources exist to help me write a syllabus statement related to artificial
 intelligence?
The Center for Teaching Excellence has compiled a number of resources for faculty
 including best practices involving the inclusion of a syllabus statement that establish's
 the expectations that govern the use of artificial intelligence in a classroom. 
Below is information provided by CTE as well as an adaptation of 
ChatGPT and Generative AI Tools: Sample Syllabus Policy Statements
 by UT Austin’s 
Center for Teaching and Learning
. 
Find all this information as well as additional resources from CTE directly 
here
.  
Each section contains several possible ways of framing the instructor’s intent. Due
 to the nuance of generative artficial intelligence, the categories do not stand alone,
 so you may find areas of overlap. To that end, these statements are intended to spur
 your own thinking, and so you are welcome to use, edit, or adapt any of the selections
 below for your own purposes.
No use of generative Artificial Intelligence tools permitted
[4 Sample statements]
This course assumes that work submitted by students – all process work, drafts, brainstorming
 artifacts, final works – will be generated by the students themselves, working individually
 or in groups as directed by class assignment instructions. This policy indicates the
 following constitute violations of academic honesty: a student has another person/entity
 do the work of any substantive portion of a graded assignment for them, which includes
 purchasing work from a company, hiring a person or company to complete an assignment
 or exam, and/or using generative AI tools (such as ChatGPT).
In this course, every element of class assignments must be fully prepared by the student. 
 The use of generativeArtificial Intelligencetools for any part of your work will be
 treated as plagiarism. If you have questions, please contact me.
All assignments should be fully prepared by the student. Developing strong competencies
 in the skills associated with this course, from student-based brainstorming to project
 development, will prepare you for success in your degree pathway and, ultimately,
 a competitive career. Therefore, the use of generativeArtificial Intelligencetools
 to complete any aspect of assignments for this course is not permitted and will be
 treated as plagiarism. If you have questions about what constitutes a violation of
 this statement, please contact me.
This course assumes that work submitted for a grade by students – all process work,
 drafts, brainstorming artifacts, final works – will be generated by the students themselves,
 working individually or in groups as directed by class assignment instructions. This
 policy indicates the following constitute violations of academic honesty: a student
 has another person/entity do the work of any substantive portion of a graded assignment
 for them, which includes purchasing work from a company, hiring a person or company
 to complete an assignment or exam, and/or using generativeArtificial Intelligencetools
 (such as ChatGPT).
Generative Articial Intelligence is permitted in specific contexts and with acknowledgment
[6 sample statements]
The emergence of generative AI tools (such as ChatGPT and DALL-E) has sparked interest
 among many students in our discipline. The use of these tools for brainstorming ideas,
 exploring possible responses to questions or problems, and creative engagement with
 the materials may be useful for you as you craft responses to class assignments. While
 there is no substitute for working directly with your instructor, the potential for
 generativeArtificial Intelligencetools to provide automatic feedback, assistive technology
 and language assistance is clearly developing. Please feel free to reach out to me
 well in advance of the due date of assignments for which you may be using generativeArtificial
 Intelligencetools and I will be happy to discuss what is acceptable.
In this course, students shall give credit toArtificial Intelligencetools whenever
 used, even if only to generate ideas rather than usable text or illustrations. When
 usingArtificial Intelligencetools on assignments, add an appendix showing (a) the
 entire exchange, highlighting the most relevant sections; (b) a description of precisely
 whichArtificial Intelligencetools were used (e.g. ChatGPT private subscription version
 or DALL-E free version), (c) an explanation of how theArtificial Intelligencetools
 were used (e.g. to generate ideas, turns of phrase, elements of text, long stretches
 of text, lines of argument, pieces of evidence, maps of the conceptual territory,
 illustrations of key concepts, etc.); (d) an account of whyArtificial Intelligencetools
 were used (e.g. to save time, to surmount writer’s block, to stimulate thinking, to
 handle mounting stress, to clarify prose, to translate text, to experiment for fun,
 etc.). Students shall not use AI tools during in-class examinations, or assignments
 unless explicitly permitted and instructed. Overall, AI tools should be used wisely
 and reflectively with an aim to deepen understanding of subject matter.
It is a violation of university policy to misrepresent work that you submit or exchange
 with your instructor by characterizing it as your own, such as submitting responses
 to assignments that do not acknowledge the use of generative AI tools. Please feel
 free to reach out to me with any questions you may have about the use of generative
 AI tools before submitting any content that has been substantially informed by these
 tools.
In this course, we may use generative AI tools (such as ChatGPT) to examine the ways
 in which these kinds of tools may inform our exploration of the topics of the class.
 You will be informed as to when and how these tools will be used, along with guidance
 for attribution if/as needed. Any use of generative AI tools outside of these parameters
 constitutes plagiarism and will be treated as such.
Understanding how and when to use generative AI tools (such as ChatGPT, DALL-E) is
 quickly emerging as an important skill for future professions. To that end, you are
 welcome to use generative AI tools in this class as long as it aligns with the learning
 outcomes or goals associated with assignments. You are fully responsible for the information
 you submit based on a generative AI query (such that it does not violate academic
 honesty standards, intellectual property laws, or standards of non-public research
 you are conducting through coursework). Your use of generative AI tools must be properly
 documented and cited for any work submitted in this course.
To ensure all students have an equal opportunity to succeed and to preserve the integrity
 of the course, students are not permitted to submit text that is generated by artificial
 intelligence (AI) systems such as ChatGPT, Bing Chat, Claude, Google Bard, or any
 other automated assistance for any classwork or assessments. This includes using AI
 to generate answers to assignments, exams, or projects, or using AI to complete any
 other course-related tasks. Using AI in this way undermines your ability to develop
 critical thinking, writing, or research skills that are essential for this course
 and your academic success. Students may use AI as part of their research and preparation
 for assignments, or as a text editor, but text that is submitted must be written by
 the student. For example, students may use AI to generate ideas, questions, or summaries
 that they then revise, expand, or cite properly. Students should also be aware of
 the potential benefits and limitations of using AI as a tool for learning and research.
 AI systems can provide helpful information or suggestions, but they are not always
 reliable or accurate. Students should critically evaluate the sources, methods, and
 outputs of AI systems. Violations of this policy will be treated as academic misconduct.
 If you have any questions about this policy or if you are unsure whether a particular
 use of AI is acceptable, please do not hesitate to ask for clarification.
Students are encouraged to use generative Artificial Intelligence tools in coursework
[3 sample statements]
The use of generative AI is encouraged with certain tasks and with attribution: You
 can choose to use AI tools to help brainstorm assignments or projects or to revise
 existing work you have written. When you submit your assignment, I expect you to clearly
 attribute what text was generated by the AI tool (e.g., AI-generated text appears
 in a different colored font, quoted directly in the text, or use an in-text parenthetical
 citation).
Designers commonly use AI-content generation tools in their work. In this course,
 using AI-content generation tools is permitted and will be a normal and regular part
 of our creative process when it is used according to the below criteria. In this course,
 neglecting to follow these requirements may be considered academic dishonesty. (1)
 For each assignment, you are required to include a paragraph that explains what AI
 content- generation tool you used, the dates you used it, and the prompts you used
 to generate the content according to the MLA style guide. (2) During critique, it
 is important to describe the precedents you used and how any source content was transformed.
 When showing or presenting images or other content you generated using an AI-tool,
 cite that image or content following the MLA style guide. If you need help referencing
 your creative work, contact me to collaborate.
Students are invited to use AI platforms to help prepare for assignments and projects
 (e.g., to help with brainstorming or to see what a completed essay might look like).
 I also welcome you to use AI tools to help revise and edit your work (e.g., to help
 identify flaws in reasoning, spot confusing or underdeveloped paragraphs, or to simply
 fix citations). When submitting work, students must clearly identify any writing,
 text, or media generated by AI. This can be done in a variety of ways. In this course,
 parts of essays generated by AI should appear in a different colored font, and the
 relationship between those sections and student contributions should be discussed
 in cover letters that accompany the essay submission.
How can I as an instructor incorporate Artificial Intelligence into my lesson planning?
1. Prompt Competition​
a. Identify a major question or challenge in your field or discipline that chatGPT
 could write about. Preferably a question with no clear single right answer.​
b. Have students collaborate (in pairs or small teams) on developing 5 to 10 criteria
 for assessing chatGPT responses to the major question. For example, chatGPT’s output
 references more than one theoretical perspective.​
c. Ask students to individually write a prompt for chatGPT to answer the major question.​
d. Have students use their criteria to judge the responses of other students (in the
 pair or small team), and rate the chatGPT prompts/responses from best to worst.​
2. Reflect and Improve​
a. Ask students to individually identify a major question or challenge in your field
 or discipline that chatGPT could write about.​
b. Have students use chatGPT to write a response to their question or challenge.​
c. Ask students to reflect on chatGPT’s output (e.g., what is correct, incorrect,
 what they don’t know if it is correct or incorrect, what should they look up elsewhere
 to verify, what should they ask chatGPT next).​
d. Using Track Changes in MS Word or Suggesting in Google Docs, have students improve
 the output of chatGPT (e.g., correcting errors or misinformation, expanding on shallow
 content).​
e. Have students submit their prompt and the improved chatGPT response with their
 added content highlighted.​
3. Re-vision​
a. Ask students to individually identify a major question or challenge in your field
 or discipline that chatGPT could write about.​
b. Have students use chatGPT to write a response to their question or challenge.​
c. George Heard is attributed with saying “The true meaning of the word revision is
 this: to see again.” Have students revise (write again) chatGPT’s output from a different
 angel. For instance, take a different perspective, apply a critical lens, expand on
 a particular concept, or correct aspects of the output that could cause their peers
 to misunderstand or misinterpret.​
4. Dual Assignments​
a. Give students a choice between two versions of the same assignment. One version
 for those that want to use chatGPT and one for those who don’t.​
b. For those who choose to use chatGPT, they have to submit their prompt(s) and the
 chatGPT output. Using Track Changes in MS Word or Suggesting in Google Docs, have
 students add depth, clarify misinformation, offer alternative perspectives, and make
 other improvements to the chatGPT output.​
c. For those who choose to complete the assignment without chatGPT, they should complete
 the assignment and sign a statement that chatGPT was not used.​
d. Grade both assignments on how well students illustrate their depth of knowledge
 through either (a) their changes to chatGPT’s output, or (b) their original writing.​
5. Mind Maps​
a. Since chatGPT can’t natively make visual representations of content (see note below),
 have students create mind maps (aka, associative maps, spider map, process maps) to
 illustrate the connections between ideas, concepts, approaches, or theories in your
 field or discipline.​
b. The more details or levels that students add to their mind minds, the easier it
 will be for them to demonstrate their newly acquired knowledge and skills.​
6. Debates​
a. Have students debate a major question or challenge in your field or discipline.
 Even short debates can deepen learning and get students to look at topics from varied
 perspectives.​
b. You can choose if students are allowed to use chatGPT in their preparation for
 the debate’s opening statements.​
c. Debates can be done in different formats, and the length of times for speeches
 can vary depending on how much time and how many students are in your course.​
7. Videos or Podcasts​
a. Rather than written essays, have students make videos or audio recordings as the
 medium for sharing their knowledge.​
b. Using a video-based tool (such as VoiceThread, FlipGrid, or Zoom) can make the
 process easier for students.​
c. Students can also record audio podcasts on their phone or computer if visuals are
 not required for the content of the assignment.​
8. Explain Your Thinking​
a. Give the assignment as usual, but in addition require that students use Using Track
 Changes in MS Word or Suggesting in Google Docs to explain at least 8 to 10 steps
 of their thinking as comments added to the text.​
b. Students can describe, for instance, the steps in their logic, their problem solving
 or writing process, or the development of their theoretical path.​
c. Students could also document their thinking with audio recordings or videos.​
9. 2x2 Matrix​
a. Have students create a 2x2 matrix relating two concepts covered in the course.
 For instance, what are shared and different defining characteristics of concepts or
 processes.​
b. A simpler version of this assignment is to have students develop Venn Diagrams
 for comparing important concepts or processes.​
10. Next Time
​
a. Ask students to use chatGPT to answer an essay question about a major question
 or challenge in your field or discipline.​
b. Have students reflect on their learning about the topic based on using chatGPT,
 and to write down 5 things they learned about the topic from chatGPT.​
c. Have students design a new assignment that doesn’t allow for the use of chatGPT
 but that would allow them (or other students) to demonstrate their learning. For example,
 they might suggest a group project, or mind map assignment.​
Watkins, R. (2022, December 18). Update Your Course Syllabus for 
chatGPT
 [web log]. Retrieved January 31, 2023, from 
https://medium.com/@rwatkins_7167/updating-your-course-syllabus-for-chatgpt-965f4b57b003
.
Can I ban the use of artificial intelligence in my course?
As the course instructor you may restrict and use Artificial Intelligence as you deem
 fit based on 
the goals and objectives of your course. 
Artificial intelligence is becoming 
extremely
 intertwined with the technology we interact with every day
,
 so it may be difficult to 
eliminate
 its
’
 use 
in your classroom
.
Student Frequently Asked Questions
Expand all
What happens to a student found Responsible for violating the Honor Code by using
 artificial intelligence?
Students found responsible for violating the Honor Code as it relates to artificial
 intelligence recieve outcomes consistent with those who violate the Honor Code in
 other aspects by receiving some combination of administrative and educational outcomes.
 
Most commonly students with only one violation of the Honor Code are placed on 6 months
 of Conduct Probation and must complete either the Academic Integrity Workshop or Artificial
 Intelligence Module.
Both the Workshop and the Module are free, asynchronus, online course administered
 via Blackboard. Both also feature several assignments that allow students the opportunity
 to reflect on their use or misuse of artificial intelligence and exposes them to some
 ethical questions to consider when they are debating their use as well as tips on
 how to avoid future violations of the Honor Code regarding their use of artificial
 intelligence as well as other types of violations.
For more examples of case outcomes related to Honor Code violations click 
here
.
Does using Artificial Intelligence always violate the Honor Code?
No, but consider that the use of artificial intelligence websites and bots like ChatGPT
 may be a violation of the Cheating - Unauthorized Aid, Cheating - Improper Collaboration,
 Plagiarism - Copying Work, or Falsification - Violation of Classroom Rules policies.
 This is dependent on the nature of how the artificial intelligence service was used.
 As with any academic tool, it's your responsibility to make sure the use of AI is
 allowed by your instructor and that any AI-generated content is clearly cited or marked,
 so it's clear what work is yours and what was created by the technology.
For example, a student may be inclined to use ChatGPT to help brainstorm ideas for
 a topic of a research essay. In most cases, proper use of ChatGPT or other artificial
 intelligence services in this scenario would consist of the student first asking their
 professor if they were allowed to use ChatGPT to assist in the brainstorming process.
 If permitted by the instructor, the student could then use the service to brainstorm
 ideas. If at any point in this process, the student decides to use the service beyond
 this brainstorming process they would need to cite all statements or claims generated
 by the service so that it is clear what material in the final assignment submission
 was created by the student and what was created by the service much like citing any
 other source in a research essay.
Note: Professors have the right to not allow students to use Artificial Intelligence
 services in the completion of their assignments no differently than how professors
 often restrict access to other technologies such as calculators for certain examinations
 and homework assignments. In the same course, a calculator may be permitted for one
 assignment and not another. We encourage professors to make it clear if Artificial
 Intelligence was allowed on one assignment and not a following assignment but, ultimately,
 the student is responsible for asking if they plan to use Artificial Intelligence.
 Not knowing is not an excuse for a violation of the Honor Code
Can I use artificial intelligence bots like ChatGPT to help with my homework?
Ask your course instructor. When you ask
,
 be sure to explain exactly how you plan to use the 
platform
. The professor may restrict the use of artificial intelligence services
,
similarly to how
 a professor may restrict certain sources like Wikipedia when completing research
 assignments. If 
approved to
 use an artificial intelligence 
platform
, be sure to cite your work 
when taking
information
 from the 
platform
used in your assignment submission.
Should I use citations when using artifiical intelligence in my work?
Yes. When using artificial intelligence services to generate statements, figures,
 images, etc. be sure to cite the work both in text (if applicable) and in a works
 cited page. Remember that artificial intelligence is a new technology so citation
 guidelines are currently being developed and are subject to change.
How do I cite artificial intelligence in MLA, APA or Chicago Style?
Find out how here:  
MLA Style Center
Find out how here:  
APA Style
Find out how here:  
Chicago Manual of Style Online
Assessment Data
By the Numbers
34%
Roughly a third of all Honor Code cases reported in the 24-25 AY referenced the use
 of artificial intelligence. This is an increase of 100 individual cases from the 23-24
 AY totaling in 288 cases.
Let's Chat About AI
Request a Presentation
Request a presentation from the Office of Student Conduct and Academic Integrity to
 discuss ethical decision making in an effort to better understand when it may or may
 not be appropriate to use artificial intelligence and here from us about how we adjudicate
 Honor Code violations related to artificial intelligence.
Request a Presentation
Student Conduct 
and
 Academic Integrity
Location
USC Facebook
USC Instagram
USC X
Colleges & Schools
Arts and Sciences
Business
Education
Engineering and Computing
The Graduate School
Hospitality, Retail and Sport Management
Information and Communications
Law
Medicine
Medicine (Greenville)
Music
Nursing
Pharmacy
Public Health
Social Work
South Carolina Honors College
Palmetto College
Offices & Divisions
Employment
Undergraduate Admissions
Financial Aid and Scholarships
Bursar (fee payment)
Veterans and Military Services
Disability Resources
Access and Opportunity
Human Resources
Law Enforcement and Safety
University Libraries
All Offices and Divisions
Tools
Carolina Alert
Campus Email
my.sc.edu
Blackboard
Campus Safety and Wellness
PeopleSoft Finance
©
University of South Carolina
Privacy
Student Consumer Information
Student Consumer Information
Transparency Initiative
Civil Rights and Title IX
Digital Accessibility
Contact
Challenge the conventional. 
Create the exceptional. 
No Limits.
©
```

**YOUR CODES (University of South Carolina):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 9. University of South Dakota

```
### PRIMARY https://www.usd.edu/About/Artificial-Intelligence
Artificial Intelligence | University of South Dakota
Skip to main site navigation
Skip to main content
Apply
Visit
Request Information
Open the main 
Menu
Open the search panel
Search
Academics
Undergraduate Programs
Graduate Programs
USD – Sioux Falls
Colleges & Schools
USD – Online
Dual Credit
Accelerated Programs
Signature Programs
Continuing Education
Libraries
Academic Calendars
Admissions & Aid
Undergraduate Admissions
Graduate Admissions
International Admissions
Law School Admissions
Medical School Admissions
Military & Veterans' Admissions
Visit USD
Tuition & Costs
Financial Aid
Research
Undergraduate Research
Graduate Research
Research Compliance
Business & Entrepreneurship Research
Health & Medicine Research
Humanities & Culture Research
Learning & Leadership Research
Public Service & Law Research
Science & Technology Research
Faculty & Staff Directory
Student Life
Housing & Dining
Activities & Involvement
Health & Wellness
Academic & Campus Support
Career Services
Special Events & Traditions
Arts & Culture
Security & Safety
Athletics
About
At a Glance
Vermillion Campus & Community
Sioux Falls Campus & Community
Campus Maps, Directions & Parking
Mission & History
Purpose & Leadership
Artificial Intelligence
Departments, Offices & Resources
Accreditation & Consumer Information
Contact Us
Open the search panel
Search
Helpful Links
A-Z Index
myUSD
News & Stories
Calendars
Coyote OneStop
Academic Catalog
Campus Map
Coyote Athletics
Online Bookstore
Coyote Gear
Support USD
Resources For
Current Students
Faculty & Staff
Parents & Families
Apply
Visit
Request Information
Home
About
Artificial Intelligence
Artificial Intelligence 

 The University of South Dakota provides this central resource to guide students, faculty, and staff in the ethical and innovative use of generative AI across our campus community.
Understanding Generative AI: USD's Guidance and Commitment

As the state’s designated public liberal arts institution, the University of South Dakota is uniquely positioned to promote the ethical and responsible use of Generative AI (GenAI). GenAI is a type of artificial intelligence that uses large datasets to generate content, alongside the technical expertise needed to use these tool effectively.
Our students, faculty, staff and graduates live and operate in a world where using GenAI is a daily occurrence. We understand the role we must play in helping our stakeholders navigate this reality. 
The information below is intended to outline USD’s position on GenAI and provide guidance for using this resource.

At USD, we value original and creative thought. We educate for integrity, curiosity and critical thinking as we equip and inspire learners to create new ideas. We understand the importance of promoting technology literacy and setting our community up to be successful in the 21st century learning environment and workplace. To that end, USD teaches and empowers our students, faculty and staff to understand and, when appropriate, to utilize with care the latest developments in technology, including GenAI.

GenAI is an interactive set of tools that, when used, should serve as a supplement to human activity, not a replacement. USD encourages transparency, accuracy and fairness in the context of GenAI use, with final decisions and strategies reflecting human judgment. Responsible GenAI use includes exercising ethical judgment and restraint, with careful consideration of appropriate boundaries and potential impacts on individuals and communities. All members of the USD community are expected to maintain professional and academic integrity when using these tools.
NOTE: The information provided here should not be viewed as official policy; it is intended to provide guidance.
The Value and Potential Uses of GenAI at USD
Learning and Creativity
GenAI can help brainstorm, iterate, and explore multiple angles when individuals actively question, verify and refine outputs rather than accept them outright. 
Scientific Inquiry and Problem-Solving
GenAI can help explore scientific questions, identify patterns, test hypotheses and make sense of non-sensitive data, as part of the learning process. It remains important to use human judgment to verify sources and results and to treat sensitive data with care.
Interactivity as a Skill
Effective GenAI requires that users develop clear goals, craft well-structured prompts, fact check output and reflect on their use of technology. In situations where using GenAI is acceptable, we recommend individuals use their critical thinking skills to assess, question and refine the GenAI answers. These interactive habits mirror the scholarly process and are integral to digital fluency. 
Workforce Development
Across sectors, employers expect graduates to understand where GenAI can effectively assist and where human expertise must lead. USD prepares students to use GenAI ethically and competently alongside professional competencies such as analytical reasoning, effective communication, collaboration and creative problem-solving.
While preparing USD’s graduates to understand GenAI, USD uses Microsoft 365 Copilot as its approved GenAI chat, offering the power of GPT-4 and commercial data protection. We encourage faculty, staff and students to use this tool for GenAI chat functions. Individuals can view a list of AI tools approved for various uses and their security level in 
Coyote One Stop.
Independent Thought at USD
Independent thinking and academic freedom remain central to learning. 
The most meaningful learning emerges through analysis, synthesis and challenges. USD supports the freedom to explore, debate, critique and discuss ideas relevant to a course or field of study and expects that freedom to be exercised with professionalism and responsibility.
AI is a university resource, not a technology mandate. 
GenAI is a resource available to the university’s community, not a requirement for every academic or professional pursuit. Its role will vary across disciplines, courses, assignments and/or projects. USD’s priority is maintaining the integrity of learning and inquiry while upholding the academic standards and expectations of individual courses at USD.
Accuracy benefits from human judgment.
 Ethical and professional use of GenAI requires examining, verifying and reflecting on outputs according to discipline appropriate standards of evidence and inquiry. Treating GenAI as a drafting or exploratory partner, rather than an authority, strengthens habits of careful inquiry and scholarly rigor.
Continuous Review

GenAI presents new challenges to educational ethics and practice, requiring rigorous thought and ongoing conversation among educators. USD will review this guidance regularly and update it to reflect evolving technologies, BOR policy, scholarship, legal frameworks and stakeholder input.
Principles for Responsible AI Use at USD

1. Human-Centered Learning First
Independent thinking and deep learning emerge from the responsible and ethical use of information and technology to explore, debate and critique ideas that help with the acquisition of skills and generation of ideas.
2. Discipline-Guided Decisions
AI use will vary both between and within disciplines. Faculty should make this determination in collaboration with peers and academic leadership, guided by disciplinary norms, accreditation requirements and course outcomes.
3. Transparency and Attribution
When AI meaningfully contributes to academic work, students, faculty and staff should disclose how it was used and cite sources or models where relevant (consistent with instructor/program guidance).
4. Accuracy, Verification and Bias Awareness
AI can be incorrect or biased. Users must validate claims with credible sources, note limitations and avoid overreliance on AI for facts, analysis or authorship.
5. Privacy, Data Protection and Intellectual Property
Do not enter confidential, personally identifiable or proprietary information into AI tools without explicit authorization and appropriate safeguards. Respect creators’ rights and licensing.
6. Accessibility in Education
If used, AI should be deployed 
in ways that broaden access to all learning materials and support all learners.
7. Human Judgement and Oversight
AI outputs should not be considered a definitive conclusion. Users should treat AI
‑
generated judgments as starting points, apply professional judgment, consider context and remain accountable for final decisions.
Attribution
The first draft of this page was written with the assistance of GenAI to compile notes and meeting minutes into a continuous document. Content was reviewed and refined by USD faculty and staff over the course of several months through an iterative process and reviewed by the campus community and leadership to ensure accuracy and alignment with institutional priorities.

 Generative AI FAQ
 
Click to Open
What is Generative AI?
Generative Artificial Intelligence (GenAI) refers to tools that can generate content—such as text, images, code, audio or video—based on prompts or questions. Examples include ChatGPT, Microsoft Copilot, Google Gemini and others.

These tools can support learning, creativity and productivity, but they also require responsible and ethical use. At the University of South Dakota, we encourage students to explore AI as a 
learning partner
, not a replacement for their own thinking.
Click to Open
What AI Tools are Approved and Supported at USD?
While USD understands the need for innovation and improved outcomes, we must also uphold our commitment to security and regulatory compliance. GenAI tools must be reviewed and approved before use on campus. USD’s Information Technology Department provides information on which tools have passed review and what kinds of data or information are acceptable within each platform.

View the 
Coyote One Stop Article on approved GenAI Tools.
Microsoft Copilot is the only tool on USD’s campus that is approved for full, integrated use. Other tools may be used as standalone platforms or for non-restricted data.
Click to Open
How Can I Communicate Authentically with AI?
The USD community relies on trust, relationships and clear communication. While GenAI can help you start a draft or organize ideas, it cannot fully represent the nuance of human interaction.

To keep communication authentic and effective, do not send AI-generated text “as-is.” Review output for tone, clarity and rewrite output in your own voice. 
Student Information

 Check out USD's best practices to learn how to use AI responsibly and ethically in your coursework.
Learn More
Faculty Information

 Explore guidance on integrating generative AI into your teaching and research with USD’s ethical use frameworks.
Learn More
Staff & Administration Information

 Review USD’s recommendations for using generative AI efficiently and securely in your daily operations.
Learn More
414 E. Clark Street

Vermillion, SD 57069
877-COYOTES
877-269-6837
Contact Us
Maps & Directions
Social Media Links
Facebook
Instagram
LinkedIn
Twitter
YouTube
University Resources
Alumni
Artificial Intelligence
Employment
Directory
Policies
Legal
Accessibility
Compliance
Privacy
EOAA/Title IX
Terms of Use
Helpful Links
MYUSD portal
About USD
USD Athletics
Request Information
X

 Please review our website privacy policy.
 
Review Privacy Policy
Confirm
```

**YOUR CODES (University of South Dakota):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---

## 10. University of Tennessee Knoxville

```
### PRIMARY https://oit.utk.edu/ai/
Artificial Intelligence | Office of Innovative Technologies
Skip to content
Skip to main navigation
Report an accessibility issue
The University of Tennessee, Knoxville
Office of Innovative Technologies
GET 
HELP
Explore
Write
Chat
Call
Call
Visit the HelpDesk
Find Answers
Service Catalog
Main Menu
Main Menu
Home
All Services
A-Z Services Index
Accounts & Access Management
Application Development & Support
Artificial Intelligence
Audiovisual Technology
Backup & Recovery
Business Information Systems
Cable TV
Cloud Infrastructure
Computer Labs
Database Administration
Desktops, Laptops, & Mobile
Document Imaging & Management
Email, Calendars, & Instant Messaging
Faculty Information Systems
File Sharing & Storage
High Performance & Scientific Computing
Information Management & Analytics
Information Security
Instructional Support
IP Names & Addresses
IT Service Management
Network
OIT HelpDesk
OIT Research Services
Research Computing Support
Software/Hardware Procurement, Distribution, & Licensing
Student Information Systems
System Administration – Linux
System Administration – Windows
Teaching & Learning Technologies
Telephone
Training
Websites
Are You New?
On Campus Students
Online Students
All Employees
Graduate Students
Faculty
Researchers
Tech Guides
Technology & Teaching Modalities
Working & Teaching Remotely
Just for Students
UT Verse
Log Into...
Online@UT (Canvas)
LiveOnline@UT (Zoom)
UT Canvas Catalog
LinkedIn Learning
Microsoft 365
Google
MyUTK
UT Email/Volmail Account
Web Surveys
I Want...
Cable TV Lineup
Email Setup
Internet Connection
Password Management
Software Downloads
Training
News
Home
Artificial Intelligence
Artificial Intelligence
Service navigation
Explore
Related Links
Related Links
Artificial Intelligence Home
UT AI Hub
Get Started with UT AI Hub
UT AI Hub Guide
AI Tools at UT
Guidance Chart for Using AI Tools
UT Verse
What is UT Verse?
UT Verse Resources
Where do I begin?
AI Tools and Technologies
Introduction to Prompting
Guides and Tutorials
Frequently Asked Questions About UT Verse
AI Workshops and Events
UT Verse: AI Unplugged
Teaching and Learning with AI
Applications of AI in Education
Guidance on AI Adoption
Opportunities & Challenges
Resources
AI News
Log In
Related Logins
Related Logins
UT Verse
Copilot
Artificial intelligence (AI) is becoming a bigger part of daily life at UT. Even if you feel late to the game, you’re not alone. Learn to use AI securely and effectively at UT through these guidelines, resources, and tools.  
AI Guiding Principles
Mission-Driven Use of AI
: AI should support the university’s mission of education, research, and service—expanding access, advancing discovery, and solving real-world problems for the public good. 
Data Privacy and Stewardship
: AI must operate within legal and ethical boundaries and reflect the university’s commitment to security, transparency, and responsible management. 
Responsible Practices
: AI should be used with integrity, supporting fairness in outcomes, treating all individuals with respect, and ensuring decisions reflect the university’s educational and ethical standards. 
Transparency and Accountability
: AI systems must be explainable and governed responsibly, with clear human oversight to maintain trust, ensure fairness, and uphold institutional accountability. 
AI Tools at UT (managed and contracted)
Certain AI tools are centrally managed, contracted, and reviewed by the university and provide the security and stability necessary for university content. They include the following chat tools, as well as selected external AI tools for meeting summaries, academics, and research. 
UT AI Hub: 
A Generative AI (GenAI) gateway providing access to ChatGPT, Claude, Grok, and others in a secure environment.
UT Verse: 
A collection of AI tools developed by the University of Tennessee, Kno
xville, including UT Verse: AI Assistant and the UTVersal Translator. 
Microsoft Copilot:
 Microsoft’s AI-powered 
chat
 platform for searching for information, creating content, and communicating with others. 
Learn more about UT-managed and contracted AI tools
Teaching and Learning with AI 
Artificial Intelligence (AI) offers transformative opportunities to ethically and effectively further our institutional mission. The Office of Innovative Technologies is dedicated to actively educating UT’s academic community on teaching and learning with artificial intelligence, including: 
Applications of AI in Education 
Guidance on AI Adoption 
Opportunities and Challenges 
Prompting and AI Assistant Creation 
Additional Resources 
Watch OIT’s AI and Teaching video
 on the importance of guiding students in ethical AI use and integrating AI into classroom activities to foster a culture of inquiry and curiosity (2min 54sec). 
Learn more about teaching and learning with AI
Policies & Guidelines 
Everyone is responsible for understanding and following university policies and ethical guidelines when using AI. This means not sharing confidential information with AI tools and making sure work submitted is your own. 
Review the guidance chart
 to determine what types of data you can enter into these tools.
UT Policy on Artificial Intelligence
UT Health Science Center Acceptable Use of Generative AI
Acceptable Use of IT Resources Policy
Guidelines for Responsible Use 
Protect university and personal data 
Verify accuracy and do not assume AI output is correct 
Be cognizant of bias with inputs and outputs 
Maintain confidentiality and minimum necessary use 
Be transparent when using AI for official work 
Respect copyright, licensing, and intellectual property 
Use only approved or authorized AI services for sensitive data 
 A Risk-Based Approach Based on Data Classification 
Whether an AI tool may be used depends on the type of data you enter into it, not simply whether the tool is available or supported by IT. AI use is governed by UT’s Data Classification Standard and a risk-based decision model. Whether an AI tool may be used depends on:
The classification of the data
The contractual protections in place
The technical configuration of the AI service
The presence or absence of external data sharing (e.g., web search)**
This approach ensures that AI adoption supports innovation while maintaining compliance with FERPA, HIPAA, CUI, and other regulatory obligations.
 How to Determine If You Can Use an AI Tool
Before using any AI tool, ask:
What type of data am I entering?
What 
classification level does that data fall under
?
Is the AI tool 
UT-managed and contractually covered
?
Is web search or external sharing enabled?
Do I need to coordinate with campus IT or 
Cybersecurity Governance, Risk, and Compliance
 (GRC)?
Your answers determine whether the use is allowed.
Software Approval Process
Submit a request online
 to ask for consideration of an AI tool for departmental or university use. 
Resources 
Office of Innovative Technologies
Guides and Tutorials
Workshops and Events
Teaching and Learning with AI
UT Verse Vodcast
Teaching & Learning Innovation
Teaching with Generative Artificial Intelligence at UTK
 (requires UT login) 
Research, Innovation, & Economic Development
AI Tennessee Initiative
Guidance Available by Campus 
UT Chattanooga: 
utc.edu/ai
UT Health Science Center: 
uthsc.edu/its/ai/index.php
 (requires UTHSC login) 
UT Knoxville: 
oit.utk.edu/ai
 (this page)
Office of Innovative Technologies
CONNECT WITH US:
Follow OIT on X (Twitter)
Sign Up for IT Weekly
Read IT Weekly
 OIT Instruction & Research News
OIT on the UTK Employee Hub
About OIT
Employment
Technology Fee
Are You New?
See All Services
Policies
OIT HELPDESK
Commons North

2nd Floor Hodges
865-974-9900
Contact Form
Search Knowledge Base
Office of Innovative Technologies
University of Tennessee
The University of Tennessee, Knoxville
Knoxville, Tennessee 37996
865-974-1000
Search for:
Events
A-Z 
Apply
Privacy
Map
Directory
Give to UT
Accessibility
The flagship campus of 
the University of Tennessee System
 and partner in 
the Tennessee Transfer Pathway
.


### SECONDARY https://policy.tennessee.edu/policy/bt0035-policy-on-artificial-intelligence/
BT0035 - Policy on Artificial Intelligence - UT System Policies
Skip to content
Search
Search
BT0035 – Policy on Artificial Intelligence
System-wide Policy:
BT0035 – Policy on Artificial Intelligence
Version: 1
Effective Date: 02/28/2025
AUTHORITY
Pursuant to Tennessee Public Chapter 550 (2024),* the Board of Trustees (“Board”) of The 
University
 of Tennessee (the “University”) is responsible for adopting a policy pertaining to the use of artificial intelligence technology by students, 
faculty
, and staff for instructional and assignment purposes. Additionally, the Board is responsible for approval of policies governing, among other things: (i) student conduct,** and (ii) the general welfare and success of students.***
DEFINITIONS
For purposes of this policy, capitalized terms used herein shall have the meanings set forth below:
“Artificial Intelligence” 
or 
“AI” 
means a machine-based system that can, for a given set of human-defined objectives, make predictions, recommendations, or decisions influencing real or virtual environments and that is capable of using machine and human- based inputs to perceive real and virtual environments, abstract such perceptions into models through analysis in an automated manner, and use model inference to formulate options for information or action.****
“
Campus
” 
means The University of Tennessee at Chattanooga (UT Chattanooga), The University of Tennessee Health Science Center (UTHSC), The University of Tennessee, Knoxville (UT Knoxville), The University of Tennessee at Martin (UT Martin), The University of Tennessee Southern (UT Southern), and any other campus that is or becomes a part of The University of Tennessee system. For purposes of this policy, the University of Tennessee Institute of Agriculture (UTIA) and the University of Tennessee Space Institute are recognized as component units of the UT Knoxville campus.
“Faculty” 
or 
“Faculty Member” 
means any faculty member (regardless of rank or title) employed by the University engaged primarily in academic instruction, research, or service.
“Staff” or “Staff Member” 
means exempt and non-exempt staff members employed by the University not engaged primarily in academic instruction, research, or service, including but not limited to professional staff and executive/
administrative staff
.
“Student” 
or 
“Students” 
shall include person(s) enrolled or registered for study at the University, either full-time or part-time, pursuing undergraduate, graduate, or professional studies, as well as non-degree and non-credit programs and courses to the extent they are so defined in a Campus’ student code of conduct or similar University rule (e.g., student rights and responsibilities), as applicable.
PURPOSE
The University’s mission is to serve “
all Tennesseans and beyond through education, discovery and outreach that enables strong economic, social and environmental well-being.
” Pursuant to the Be One UT values, the University strives to: (i) be bold and impactful, (ii) inspire creative and transformational action, and (iii) foster 
integrity
 through openness, accountability, and stewardship. Consistent with the University’s mission and core values, the Board recognizes that AI technologies will continue to evolve and that it is imperative for Students, Faculty, and Staff to have the opportunity to succeed and thrive in a world transformed by AI.
Through this policy, the Board aims to balance the innovative potential of AI with the need to uphold academic integrity, protect 
sensitive information
, and comply with applicable laws, rules, and regulations. This policy is intended to provide a framework of broad systemwide expectations while maintaining the necessary flexibility for the Campuses to issue academic procedures, guidelines, and/or restrictions pertaining to the responsible and ethical use of AI for instructional and assignment purposes in a dynamic landscape.
SCOPE AND APPLICABILITY
This policy applies systemwide to all Students, Faculty, and Staff with respect to the use of AI technology for instructional and assignment purposes in connection with all academic courses offered by the Campuses.
POLICY STATEMENT AND GUIDING PRINCIPLES
The University embraces the use of AI as a powerful tool for the purpose of enhancing human learning, creativity, analysis, and innovation within the academic context.
Each Faculty or Staff Member (to the extent responsible for the delivery of a course) shall consider whether, when, and how AI may be used, if at all, for instructional and assignment purposes associated with a course, including independent study, clinical, and/or research activities.
Faculty/Staff Members responsible for the delivery of a course are expected to clearly communicate to Students the permitted use(s), if any, of AI technology in connection with a course and the extent to which AI technology and derived content may be used as part of a Student’s academic work.
Students are responsible for adhering to the requirements set by Faculty/Staff Members with respect to the permitted use of AI technology in each of their courses. Students should be made aware that the use of AI technology may vary by course, discipline, and by Faculty/Staff Member. Students who are uncertain of the permitted use of AI technology are encouraged to seek further clarification from the respective Faculty/Staff Member.
AI generated results may contain 
data
, images, and other information protected under intellectual property or other ownership rights, including copyright. Authors shall be fully responsible for ensuring the allowed use of any AI generated data and information contained in their academic work.
AI technology is to be used in accordance with: (i) academic and student codes of conduct/honor codes; (ii) any ethical and professional standards applicable to a particular course or program; (iii) academic standards pertaining to attribution and citations; (iv) University/Campus policies, procedures, and other guidelines; and (v) applicable laws, rules, or regulations.
VI. 
CAMPUS PROCEDURES
Each Campus shall establish academic procedures and guidance as may be necessary to provide transparency and clarity regarding the responsibilities of Students, Faculty, and Staff with respect to the appropriate use of AI technology for instructional and assignment purposes, which shall, at a minimum, address the following items:
Course-related Communication. Communication of Faculty/Staff expectations regarding the permitted use of AI technology by Students for a course shall occur through at least one of the following modalities: (i) course syllabus; (ii) course materials; (iii) assignment instructions; (iv) research guidelines; (v) a learning management system (LMS); and/or (vi) other standard forms of course-related communications, including in-person and electronic methods of communication (online, email, etc.) provided to Students.
Types of Permitted Use. Course-related communication shall address the context(s) in which a Student may employ AI technology with respect to a course and/or particular assignments. Three possible options include, but are not limited to, the following:

Unrestricted Use 
– Students may use AI technology for any learning, creation, or analysis, without restriction.
Mixed Use 
– Students may use AI technology for some learning, creation, or analysis, with specifics provided in a clear and timely manner.
Total Prohibition 
– Students may not use AI technology for any learning, creation, or analysis.
In describing any limitations (or lack thereof) on the use of AI technology in course-related communications, Faculty/Staff shall consider, among other things, the following use cases:
Learning 
– AI can provide definitions, facts, names, dates, or summaries of larger topics.
Creating 
– AI can generate a text work (from a single word up to an entire long-form text), an image (from a simple still image up through an entire video), and possibly other creations.
Analyzing 
– AI can examine patterns, gain insights, and make informed decisions of quantitative or qualitative data.
Academic Integrity. Course-related communications pertaining to the use of AI technology shall: (i) affirm the importance of academic honesty; and (ii) inform Students that the unpermitted use of AI technology is a form of academic misconduct, which violations are subject to the Campus’ student code of conduct.
AI Detection Tools. The Campus academic procedures and/or guidance shall provide Faculty/Staff with advice as to the acceptable use, if any, of AI detection tools for instructional and assignment purposes. Notwithstanding the foregoing, under no circumstances shall the results of AI detection tools be the single measure for determining the academic performance of or misconduct by a Student.
Campus procedures may include more stringent requirements provided that such procedures do not conflict with or lower the requirements set forth in this policy.
Additionally, Campuses are encouraged to provide: (i) Faculty/Staff members with examples, templates, and/or standard language for course-related communication based on multiple types of AI use, which can be adopted for instructional and assignment purposes; and (ii) education and training concerning the potential benefits, risks, and responsibilities associated with the use of AI technology.
VII. 
AI TECHNOLOGY RESOURCES/DATA PROTECTION
The use of AI technology is subject to the University’s policies and procedures pertaining to information technology, including the University’s policy on Acceptable Use of Information Technology Resources (IT0002).
As with the use of any type of information technology, Students, Faculty, and Staff must be cognizant of information security and data protection obligations (e.g., intellectual property rights, personally identifiable information, protected health information, contractual and other legal obligations, etc.) that may apply. 
Protected University Data
 shall not be entered into AI technology that has not been reviewed by the University’s Chief Information Officer (or designee) and authorized for use. The University shall maintain a list of approved AI technology resources available for use. Faculty, Staff, and Students are free to use any AI technology for instructional purposes so long as Protected University Data is not entered into such systems. “Protected University Data” shall have the meaning set forth in the University’s General Statement on Information Technology Policy (IT0001).
VIII. 
ADMINISTRATIVE RESPONSIBILITIES
The Vice President for Academic Affairs, Research, and Student Success, in consultation with the appropriate subject matter experts, shall be responsible for providing advice and support to the Campuses with respect to the requirements of this policy. The Chancellor of each Campus shall be responsible for ensuring the establishment of the Campus procedures, guidelines, and/or other resources consistent with this policy.
IX. 
COMPLIANCE AND OVERSIGHT
The Office of Institutional Compliance shall be responsible for reviewing the Campuses’ procedures, guidelines, and other efforts to promote compliance with the provisions of this policy. The Office of Institutional Compliance shall prepare reports regarding the implementation and ongoing compliance with this policy as may be requested by the Audit and Compliance Committee.
History:
Adopted 02/28/2025
* Tennessee Code Annotated § 49-7-185.
** Tennessee Code Annotated § 49-9-209(d)(1)(I).
*** Education, Research, and Service Committee Charter.
**** Tennessee Code Annotated § 49-7-185(a).
Policy Details:
BT0035 – Policy on Artificial Intelligence
Version: 1 // Effective: January 2, 2028
 Downloadable PDF
Related Policies:
IT0001 – General Statement on Information Technology Policy
IT0002 – Acceptable Use of Information Technology Resources
Menu
Home
Updates
UT System Policies
General Policies
Board of Trustees Policies
Fiscal Policies
Human Resources Policies
Information Technology Policies
Research Policies
Health & Safety / Emergency Management Policies
Campus/Institute Procedures
UT System (UTSA) Procedures
UT Knoxville Handbooks & Procedures
UT Chattanooga Handbooks & Procedures
UT Southern Handbooks & Procedures
UT Martin Handbooks & Procedures
UT Health Science Center Handbooks & Procedures
Institute of Agriculture Procedures
Institute for Public Service (IPS) Procedures
Bylaws of The University of Tennessee Board of Trustees
Guidance Documents
Forms and Templates
Statement of Need and Impact
Forms
Policy Template
Procedure Template
Committees
Responsible Officials
General Policy Committee Members
Fiscal Policy Committee Members
Human Resources Policy Committee Members
IT Security Policy Committee Members
Research Policy Committee Members
Safety Policy Committee Members
Campus Procedure Contacts
Tennessee Rules & Regulations
FAQs
General Policy
Board of Trustees Policy
Fiscal Policy
Health & Safety / Risk Management Policy
Human Resources
Information Technology Policy
Research
Policy Details
Policy Details:
BT0035 – Policy on Artificial Intelligence
Version: 1 // Effective: January 2, 2028
 Downloadable PDF
Related Policies:
IT0001 – General Statement on Information Technology Policy
IT0002 – Acceptable Use of Information Technology Resources
<
 go back to main policy page
The University of Tennessee Office of the General Counsel • 400 W. Summit Hill Dr. SW, Knoxville, TN 37902 • (865) 974-3245
© 2026 The University of Tennessee System
```

**YOUR CODES (University of Tennessee Knoxville):** admissibility=____  burden=____  appeal=____  l2=____  locus=____

---
