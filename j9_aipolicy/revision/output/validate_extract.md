# Clean extractor: audit of 16 endpoint pages (4 per system, seed 0)

Rules: (1) drop nav/header/footer/aside/form and ARIA navigation, banner, contentinfo, menu, complementary, search, toolbar, dialog; (2) drop elements whose id/class marks them as navigation, menus, footers, sidebars, breadcrumbs, cookie bars, social links, pagination, unless the element holds half or more of the remaining page; (3) prefer the declared main-content region when it holds 150+ words; (4) drop remaining link-dense blocks (anchor share above 0.8 and under 80 words, or above 0.6 and under 25 words) whose links average under 10 words, so menus go but linked summary cards and paragraphs with inline links stay. PDFs stored as pages are read with pypdf.


## US | University of California-Irvine | ai | 20260414003055

URL: dtei_uci_edu_generative_ai  
raw words 487, clean words 355, content rule `//*[@id='main-content']`


Clean text (first 400 chars): Generative AI for Teaching and Learning DTEI Events on Generative AI In Spring 2025, DTEI hosted a speed round-style pitch competition in which several faculty shared their ideas on how AI can be leveraged by faculty and departments to make teaching more efficient and effective. Watch the videos below to learn more about innovative uses of AI to enhance teaching! On May 21st, 2025, DTEI hosted a p


Structural blocks removed (3):

- `<header>` : Calendar | Contact Us Professional Development Consultations Drop-in Hours Resources Accessibility Teaching Accessibility Guide Digital Accessibility Support & 
- `<nav>` : Professional Development Consultations Drop-in Hours Resources Accessibility Teaching Accessibility Guide Digital Accessibility Support & Help Research The PERI
- `<footer>` : Location The Division of Teaching Excellence and Innovation is located on the 3rd floor of the Anteater Instruction and Research Building (AIRB). Address: AIRB 

Link-dense blocks removed (6):

- `<div>` share=0.78 words=9: Watch video: UC Irvine Scholarly Values, AI and Teaching
- `<div>` share=0.78 words=9: Watch video: UC Irvine Scholarly Values, AI and Teaching
- `<div>` share=0.78 words=9: Watch video: UC Irvine Scholarly Values, AI and Teaching
- `<div>` share=0.78 words=9: Watch video: UC Irvine Scholarly Values, AI and Teaching
- `<div>` share=0.78 words=9: Watch video: UC Irvine Scholarly Values, AI and Teaching
- `<p>` share=0.78 words=9: Watch video: UC Irvine Scholarly Values, AI and Teaching

## US | Arizona State University | integrity | 20260511211254

URL: provost_asu_edu_academic_integrity  
raw words 342, clean words 242, content rule `//main`


Clean text (first 400 chars): Academic Integrity At Arizona State University, we place great value on the research and scholarship of our students and faculty and are committed to a culture of academic integrity and scholarly ethics. We welcome you into our culture of academic excellence and integrity and hope you will help foster and promote ethical and honest behavior in connection with your scholarly work and interactions w


Structural blocks removed (6):

- `<header>` : @media screen and (max-width:768px) { .uds-blockquote { display: block; } } @media screen and (max-width: 576px) { .uds-card-and-image { min-height: auto; } } .
- `<nav>` : Home Academic Integrity
- `<nav>` : What is Academic Integrity? ASU Student Honor Code Why is it Important? Student Policy Meet Your Academic Integrity Officer Student Resources Faculty Resources
- `<footer>` contentinfo: Office of the University Provost Academics Academic Accreditation Academic Advisors Committees eAdvisor™ University Senate Faculty and Staff Academic Personnel 
- `<nav>` : Maps and Locations Jobs Directory Contact ASU My ASU
- `<nav>` : Copyright and Trademark Accessibility Privacy Terms of Use Emergency

Id/class-marked blocks removed (2):

- `<div>` pr-3 block block-layout-builder block-inline-block: Academic Integrity Select Section
- `<div>` sidebar-toggler: Select Section

Link-dense blocks removed (1):

- `<li>` share=1.00 words=1: Plagiarizing.

## US | University of Notre Dame | ai | 20260110034728

URL: honorcode_nd_edu_policy_update_ai_editing_tools_fall_2024  
raw words 332, clean words 214, content rule `//main`


Clean text (first 400 chars): Policy Update: AI Editing Tools (Fall 2024) AI-powered editing tools like Grammarly and WordTune work by using AI to suggest revisions to your writing, so the suggestions they make are AI-generated text. This means that if your instructor prohibits the use of gen AI on an assignment or in a class, this prohibition includes the use of editing tools, unless explicitly stated otherwise. If your instr


Structural blocks removed (7):

- `<nav>` : Skip To Content Skip To Navigation Skip To Search
- `<header>` : University of Notre Dame Undergraduate Academic Code of Honor Home Search Menu
- `<button>` : Search
- `<nav>` : The Honor CodeHonor Code Violation ReportEducational Outcome ReportReporting PolicyUniversity Committee on the Honor CodeCollege / School Honor Code CommitteesS
- `<footer>` : Undergraduate Academic Code of Honor 217N Main Building Notre Dame, IN 46556 USA Phone 574-631-0626 honor@nd.edu © 2026 University of Notre Dame Search Mobile A
- `<nav>` : Search Mobile App News Events Visit Accessibility
- `<nav>` : Facebook X/Twitter Instagram YouTube LinkedIn

Id/class-marked blocks removed (1):

- `<ol>` breadcrumbs: The Honor Code › Policy Update: AI Editing Tools (Fall 2024)

## US | University of Chicago | ai | 20260624145056

URL: teaching_uchicago_edu_resources_programming_and_resources_ai  
raw words 1646, clean words 1544, content rule `//article`


Clean text (first 400 chars): The CCTL is available to discuss and provide guidance on the teaching and learning implications of AI for anyone in an instructional role at the University -- faculty, instructional professors, graduate student instructors, and so on. The third annual Spring Pedagogy Symposium featured speaker Tricia Bertram Gallant who explored student motivation and academic integrity in the age of AI. Dr. Bertr


Structural blocks removed (2):

- `<header>` : Resources Programming and Resources on AI
- `<footer>` : The University of Chicago Chicago Center for Teaching and Learning Harper Memorial Library 1116 East 59th St. Chicago, IL 60637 773.834.4439 Contact Us Subscrib

Link-dense blocks removed (11):

- `<p>` share=1.00 words=4: View the recording here.
- `<p>` share=1.00 words=4: View the recording here.
- `<p>` share=1.00 words=4: View the recording here.
- `<p>` share=1.00 words=8: Learn More about Teaching in the AI Landscape
- `<p>` share=1.00 words=3: Access Event Materials
- `<p>` share=1.00 words=4: Explore CCTL Teaching Spotlights
- `<p>` share=0.82 words=11: Access the repository of unit-level AI guidance and policies (CNET required).
- `<p>` share=0.80 words=5: Explore Syllabus Statements on AI
- `<p>` share=0.89 words=9: Explore Syllabus Statements on Generative AI from UChicago Faculty
- `<p>` share=1.00 words=5: Book an AI Pedagogy Consultation
- `<p>` share=1.00 words=5: Schedule a Workshop by Request

## UK | University of St Andrews | integrity | 20230808105708

URL: https://www.st-andrews.ac.uk/students/academic/academic-advising/glossary/academic-misconduct/  
raw words 350, clean words 38, content rule `body`


Clean text (first 400 chars): Academic misconduct Academic misconduct is defined as a failure to adhere to the principles of good academic practice. Penalties include written warnings, reduction of module grades (in some cases to zero), and in extreme cases, termination of studies.


Structural blocks removed (7):

- `<nav>` : Home Current Staff Current Postgraduates Current Students Administration A-Z Academic Schools Maps Contacts
- `<div>` banner: University of St Andrews Current Students Ask a question MMS Moodle MySaint Office 365 SaintMail Library
- `<nav>` : Ask a question MMS Moodle MySaint Office 365 SaintMail Library
- `<div>` complementary: Academic matters Academic advising Advisers of studies Choices Events Rules Academic advising system New students FAQs Glossary Absence Academic alert Academic 
- `<nav>` : You are here: University » Current Students » Academic matters » Academic advising » Glossary » Academic misconduct
- `<aside>` : Social media Find us on: ‎ Facebook ‎ Twitter Contact Registry - Undergraduate University of St Andrews Postal Walter Bower House Eden Campus, Main StreetGuardb
- `<footer>` : Cookie preferencesAccessibility statementTerms and conditionsWebsite helpEdit © 2023 The University of St Andrews is a charity registered in Scotland, No SC0135

Link-dense blocks removed (1):

- `<div>` share=1.00 words=4: Skip navigation to content

## UK | Newcastle University | ai | 20260428085242

URL: https://www.ncl.ac.uk/academic-skills-kit/good-academic-practice/artificial-intelligence/  
raw words 1675, clean words 1204, content rule `//main`


Clean text (first 400 chars): At Newcastle University we are committed to supporting you to develop good academic practice and your critical awareness of generative AI. These pages aim to support you in: thinking critically about how to generative AI tools responsibly and ethically understanding when use of generative AI is inappropriate and when it could be considered academic misconduct maintaining good academic practice by 


Structural blocks removed (4):

- `<form>` : Search for something Search... Search...
- `<label>` : Search...
- `<header>` : Artificial Intelligence and Your LearningGuidance to help you responsibly engage with AI for your education by maintaining academic integrity.
- `<footer>` : Academic Skills Kit Email: academicskills@ncl.ac.ukTelephone: +44 (0) 191 208 7662 Newcastle UniversityNewcastle upon TyneNE1 7RU Book an appointment Donate now

Id/class-marked blocks removed (7):

- `<div>` js-navigation navigation: Academic Skills Kit CareersLibraryCurrent StudentsStaffNews & PressEventsContact Logo Academic Skills Kit AssessmentAssessmentExams & RevisionExam Technique for
- `<ul>` menu-secondary: CareersLibraryCurrent StudentsStaffNews & PressEventsContact
- `<div>` menu: AssessmentAssessmentExams & RevisionExam Technique for In-Person ExamsTake Home ExamsBefore the Take Home ExamExam Technique for Take Home ExamsDissertations & 
- `<div>` menu-wrapper: AssessmentAssessmentExams & RevisionExam Technique for In-Person ExamsTake Home ExamsBefore the Take Home ExamExam Technique for Take Home ExamsDissertations & 
- `<ul>` menu-toplevel: AssessmentAssessmentExams & RevisionExam Technique for In-Person ExamsTake Home ExamsBefore the Take Home ExamExam Technique for Take Home ExamsDissertations & 
- `<section>` breadcrumb: Newcastle University Academic Skills KitGood Academic PracticeArtificial Intelligence and Your Learning
- `<ul>` menu-breadcrumb: Newcastle University Academic Skills KitGood Academic PracticeArtificial Intelligence and Your Learning

## UK | University of Southampton | integrity | 20260113054445

URL: https://www.southampton.ac.uk/quality/assessment/academic_integrity.page  
raw words 217, clean words 94, content rule `body`


Clean text (first 400 chars): Skip to main navigation Skip to main content Academic Responsibility and Conduct Academic responsibility and conduct (previously known as academic integrity) is integral to studying at University and a guiding principle of academic life. At its most basic, it describes taking responsibility for and acting with honesty in one's own academic work. Guidance for Investigating Suspected Breaches of Aca


Structural blocks removed (7):

- `<header>` : The University of Southampton × Search the Site Search
- `<form>` : Search the Site Search
- `<label>` : Search the Site
- `<button>` : Search
- `<nav>` : Left Right // Download Menu JSON function SiteMenuPrimary_fetchJSON(url) { return new Promise((resolve, reject) => { fetch(url).then(response => { if (!response
- `<nav>` : Home
- `<footer>` : Information for Contact us +44(0)23 8059 5000 +44(0)23 8059 3131 Address University of Southampton University Road Southampton SO17 1BJ United Kingdom Get direc

Link-dense blocks removed (12):

- `<div>` share=1.00 words=2: Quality Handbook
- `<div>` share=1.00 words=2: Quality Handbook
- `<span>` share=1.00 words=2: Quality Handbook
- `<p>` share=1.00 words=6: Regulations Governing Academic Responsibility and Conduct
- `<p>` share=1.00 words=5: Regulations Governing Academic Integrity 2023-24
- `<p>` share=1.00 words=8: University of Southampton Academic Responsibility and Conduct Guidance
- `<p>` share=1.00 words=6: Academic Responsibility and Conduct Declaration Statement
- `<p>` share=1.00 words=6: Faculty Academic Conduct Officer Role Description
- `<p>` share=1.00 words=5: Academic Conduct Officer Role Description
- `<p>` share=1.00 words=7: Library Guidance on Academic Responsibility and Conduct
- `<p>` share=1.00 words=7: Getting Started with Academic Responsibility and Conduct
- `<p>` share=1.00 words=5: Academic Responsibility and Conduct Toolkit

## UK | University of Glasgow | integrity | 20260215142307

URL: https://www.gla.ac.uk/myglasgow/sld/plagiarism/  
raw words 665, clean words 374, content rule `//*[@id='main']`


Clean text (first 400 chars): Plagiarism You should read this advice in conjunction with any resources from subject area. The University definition of plagiarism is: 'The incorporation of material without formal and proper acknowledgement (even with no deliberate intent to cheat) can constitute plagiarism. Work may be considered to be plagiarised if it consists of: a direct quotation; a close paraphrase; an unacknowledged summ


Structural blocks removed (13):

- `<div>` navigation: Skip to main content
- `<div>` complementary: The University of Glasgow uses cookies for analytics. Find out more about our Privacy policy. privacy settings accept
- `<button>` : privacy settings
- `<button>` : accept
- `<div>` complementary: We use cookies Necessary cookies Necessary cookies enable core functionality. The website cannot function properly without these cookies, and can only be disabl
- `<label>` : Switch analytics
- `<label>` : Switch clarity
- `<button>` : close
- `<nav>` : Turnitin and Online ExamsHow to avoid plagiarismWhat happens if you plagiarise?Using TurnitinWho can help you?Frequently asked questions
- `<div>` navigation: Study Research Explore Connect
- `<div>` navigation: HomeMyGlasgowStudent Learning DevelopmentPlagiarism
- `<div>` navigation: Turnitin and Online ExamsHow to avoid plagiarismWhat happens if you plagiarise?Using TurnitinWho can help you?Frequently asked questions
- ... and 1 more

Link-dense blocks removed (2):

- `<section>` share=1.00 words=1: Plagiarism
- `<li>` share=1.00 words=6: inappropriate use of artificial intelligence (AI)

## AU | Australian National University | integrity | 20250725015113

URL: https://www.anu.edu.au/students/academic-skills/academic-integrity  
raw words 440, clean words 151, content rule `//main`


Clean text (first 400 chars): Academic integrity Academic integrity is a core part of our culture as a community of scholars. At its heart, academic integrity is about behaving ethically. This means that all members of the community commit to honest and responsible scholarly practice and to upholding these values with respect and fairness. Why it matters As scholars, we develop our ideas by critically engaging with the work of


Structural blocks removed (5):

- `<div>` navigation: Skip to main content
- `<header>` banner: NewsroomEventsSafetyMapsServicesLibraryJobsDirectories
- `<nav>` navigation: Main navigationAboutAcademic CollegesUniversity ExecutiveCampuses & facilitiesStrategic planningGlobal engagementAwards & achievementsGovernanceOur historyStrat
- `<header>` : Information for
- `<nav>` navigation: BreadcrumbHomeCurrent studentsAcademic skillsAcademic integrity

Link-dense blocks removed (6):

- `<div>` share=1.00 words=2: Book appointment
- `<div>` share=1.00 words=2: Book appointment
- `<div>` share=1.00 words=2: Book appointment
- `<div>` share=1.00 words=2: Book appointment
- `<li>` share=1.00 words=2: Send email
- `<li>` share=1.00 words=2: Academic skills

## AU | University of Wollongong | integrity | 20241103050422

URL: https://www.uow.edu.au/about/governance/academic-integrity/  
raw words 957, clean words 287, content rule `//main`


Clean text (first 400 chars): Academic & research integrity Academic integrity is fundamental to learning, teaching and research at UOW. It involves upholding ethical standards in all aspects of academic work, including learning, teaching and research. It involves acting with the principles of honesty, fairness, trust and responsibility and requires respect for knowledge and its development. Ugh! Third cold this year. My brain


Structural blocks removed (26):

- `<div>` contentinfo: We use cookies to improve your experience on our site and to show you personalised advertising. To find out more, read our privacy policy and cookie policy OK, 
- `<button>` : OK, THANKS
- `<header>` : Search Give Library Current Students Staff UOW GlobalOur global presenceUOW in DubaiUOW in Hong KongUOW in IndiaUOW in Malaysia Menu Study at UOW Study at UOW C
- `<nav>` : Search Give Library Current Students Staff UOW GlobalOur global presenceUOW in DubaiUOW in Hong KongUOW in IndiaUOW in Malaysia Menu
- `<nav>` : Study at UOW Study at UOW Courses Apply Pathways to University Scholarships & Grants High school students Non-school leavers Postgraduate students International
- `<button>` : Study at UOW
- `<button>` : Close
- `<button>` : Engage
- `<button>` : Close
- `<button>` : About UOW
- `<button>` : Close
- `<button>` : Research
- ... and 14 more

Id/class-marked blocks removed (9):

- `<a>` skip-link: Skip to Content
- `<section>` uw-masthead uw-masthead--page-nav uw-masthead--ima: You are here More Pages HomeAbout UOWGovernanceAcademic integrity Academic integrityAcademic Integrity OfficersGenAI in assessmentGlossaryReport academic miscon
- `<div>` grid-container blue-nav: You are here More Pages HomeAbout UOWGovernanceAcademic integrity Academic integrityAcademic Integrity OfficersGenAI in assessmentGlossaryReport academic miscon
- `<a>` page-navigator__button page-navigator__button--bre: You are here
- `<div>` page-navigator__list page-navigator__list--breadcr: HomeAbout UOWGovernanceAcademic integrity
- `<ul>` no-bullet breadcrumbs js-breadcrumbs: HomeAbout UOWGovernanceAcademic integrity
- `<div>` uw-masthead__main: Academic integrity
- `<div>` uw-masthead__content: Academic integrity
- `<h1>` cell js-scroll-reveal--left uw-masthead__title uw-: Academic integrity

Link-dense blocks removed (44):

- `<ul>` share=1.00 words=4: Students Teachers Researchers AIOs
- `<li>` share=1.00 words=1: Students
- `<li>` share=1.00 words=1: Teachers
- `<li>` share=1.00 words=1: Researchers
- `<li>` share=1.00 words=1: AIOs
- `<div>` share=1.00 words=45: What is academic integrity? Why is academic integrity so important? What are your responsibilities? What is academic misconduct? How to avoid plagiarism? What i
- `<div>` share=1.00 words=45: What is academic integrity? Why is academic integrity so important? What are your responsibilities? What is academic misconduct? How to avoid plagiarism? What i
- `<div>` share=1.00 words=45: What is academic integrity? Why is academic integrity so important? What are your responsibilities? What is academic misconduct? How to avoid plagiarism? What i
- `<ul>` share=1.00 words=45: What is academic integrity? Why is academic integrity so important? What are your responsibilities? What is academic misconduct? How to avoid plagiarism? What i
- `<li>` share=1.00 words=4: What is academic integrity?
- `<li>` share=1.00 words=6: Why is academic integrity so important?
- `<li>` share=1.00 words=4: What are your responsibilities?
- ... and 32 more

## AU | Swinburne University of Technology | integrity | 20260529025125

URL: https://www.swinburne.edu.au/student-login/academic-integrity/  
raw words 3704, clean words 2665, content rule `//article`


Clean text (first 400 chars): Academic integrity means using ideas, knowledge and information to develop your own insights, not presenting someone else's work as your own or trying to gain unfair advantage. It also means acknowledging the work of others when you include it in your work. Changes to Academic Integrity at Swinburne Swinburne is updating its processes to support students in acting with Academic Integrity while und


Structural blocks removed (42):

- `<header>` banner: Explore More from Swinburne University News Events Library Alumni Giving to Swinburne Current students Staff login var x, i; x = document.getElementsByClassName
- `<button>` : Explore
- `<button>` button: visitCourses toggle Courses menu
- `<button>` button: visitFind a course toggle Find a course menu
- `<button>` button: visitPlanning your future toggle Planning your future menu
- `<button>` button: visitStudy levels and options toggle Study levels and options menu
- `<button>` button: visitCourse delivery toggle Course delivery menu
- `<button>` button: visitFees toggle Fees menu
- `<button>` button: visitScholarships toggle Scholarships menu
- `<button>` button: visitApplying toggle Applying menu
- `<button>` button: visitEnrolling toggle Enrolling menu
- `<button>` button: visitLife at Swinburne toggle Life at Swinburne menu
- ... and 30 more

Id/class-marked blocks removed (11):

- `<a>` skip-to skip-to--search: Skip to search
- `<a>` skip-to skip-to--content: Skip to content
- `<div>` nav-tabs-wrapper: Behaving with academic integrity Penalties for academic misconduct Where to seek assistance
- `<div>` nav-tabs-container: Behaving with academic integrity Penalties for academic misconduct Where to seek assistance
- `<ul>` nav nav-tabs container: Behaving with academic integrity Penalties for academic misconduct Where to seek assistance
- `<li>` nav-item: Behaving with academic integrity
- `<a>` nav-link active: Behaving with academic integrity
- `<li>` nav-item: Penalties for academic misconduct
- `<a>` nav-link : Penalties for academic misconduct
- `<li>` nav-item: Where to seek assistance
- `<a>` nav-link : Where to seek assistance

Link-dense blocks removed (7):

- `<div>` share=1.00 words=2: Close video
- `<div>` share=1.00 words=2: Close video
- `<div>` share=1.00 words=2: Close video
- `<div>` share=1.00 words=3: View video transcript
- `<div>` share=1.00 words=5: Learn more (Reviews and appeals)
- `<div>` share=1.00 words=7: Learn more (Understanding your academic results )
- `<div>` share=1.00 words=3: Learn more (Graduation)

## AU | Monash University | integrity | 20260521033322

URL: https://publicpolicydms.monash.edu/Monash/documents/1935748  
raw words 5028, clean words 1425, content rule `pdf`


Clean text (first 400 chars): Assessment and Academic Integrity Policy | 1 SCOPE This policy applies to all Monash University: • staff; • students; • coursework courses and units; and • teaching locations. POLICY STATEMENT This policy describes the principles of assessment at Monash University to maintain academic standards of student achievement, support students in their academic development and uphold standards of academic 


## CA | Simon Fraser University | integrity | 20240117010856

URL: http://www.sfu.ca/students/academicintegrity.html  
raw words 347, clean words 161, content rule `//*[@id='page-content']`


Clean text (first 400 chars): Academic Integrity All members of the university are expected to uphold the values of academic integrity: honesty, trust, fairness, respect, responsibility, and courage. SFU considers any act of falsification, misrepresentation or deception to be destructive because it is unfair to students who pursue their studies honestly, it compromises the worth of other’s work, and ultimately prevents student


Structural blocks removed (8):

- `<header>` : Search Simon Fraser UniversityEngaging the World Student Services Academic Integrity This site SFU.ca A-Z directory Sign in Mail goSFU Canvas A-Z Directory a b 
- `<button>` : Search
- `<form>` : This site SFU.ca
- `<label>` : This site
- `<label>` : SFU.ca
- `<nav>` : Nav Academic Integrity Academic dishonesty: what is it? Don't risk it Student support and resources Using Generative AI As A Student Academic disciplinary proce
- `<button>` : Nav
- `<footer>` : Admission Programs Learning Research Community About Maps + directions Library Academic Calendar Road Report Give to SFU Emergency Information Connect with us F

Id/class-marked blocks removed (1):

- `<div>` below-nav inherited-parsys: CONTACT Arlette Stewart, MA Coordinator, Academic Integrity Phone: 778-782-7075 Email: aic_sfu@sfu.ca Contact me for: • Case consultations for faculty • Guidanc

Link-dense blocks removed (2):

- `<p>` share=1.00 words=3: View the PDF
- `<p>` share=0.80 words=5: What is Academic Integrity (video)

## CA | University of Regina | integrity | 20260316211441

URL: https://academic-integrity.uregina.ca/  
raw words 378, clean words 282, content rule `//main`


Clean text (first 400 chars): Welcome to the University of Regina Academic Integrity site. The purpose of this site is to provide information to both instructors and students about key issues related to upholding the University’s standards of Academic Integrity as outlined in the Student Code of Conduct and Right to Appeal. The site has two parts: an instructor and student site. The instructor site provides information for ins


Structural blocks removed (5):

- `<header>` banner: Academic Integrity Hub Academic Integrity at the University of Regina
- `<nav>` navigation: Menu Academic Integrity Instructor Page Frequently Asked Questions for Instructors Strategies to Promote Academic Integrity Preventing Plagiarism Contract cheat
- `<button>` : Menu
- `<header>` : Academic Integrity
- `<footer>` contentinfo: Academic Integrity Instructor Page Student Page University of Regina CC-BY-NC-SA Proudly powered by WordPress | Education Hub by WEN Themes

Id/class-marked blocks removed (1):

- `<a>` skip-link screen-reader-text: Skip to content

## CA | Carleton University | integrity | 20260210181831

URL: https://students.carleton.ca/services/academic-integrity/  
raw words 383, clean words 222, content rule `body`


Clean text (first 400 chars): Special weather statement for Ottawa: reduced visibility in heavy snow today. View weather updates → Services Academic Integrity Service offered by University Registrar’s Office Summary Carleton University demands academic integrity from all its members. The Academic Integrity Policy governs the academic behaviour of students. Academic dishonesty, in whatever form, is destructive to the values of 


Structural blocks removed (6):

- `<label>` : Search Input
- `<nav>` : NewsEvents and Important DatesStudent Services
- `<button>` : Dismiss
- `<button>` : Ok. Got it.
- `<footer>` : Follow @MyCarletonU on social! Instagram Twitter Carleton University acknowledges the location of its campus on the traditional, unceded territories of the Algo
- `<aside>` : Follow @MyCarletonU on social! Instagram Twitter

Id/class-marked blocks removed (6):

- `<div>` header w-full bg-white shadow-none border-t-[5px] : Current Students Login to 360 News Events and Important Dates Student Services
- `<ul>` tablet-nav md:ml-[6px]: News Events and Important Dates Student Services
- `<li>` 53161-tablet main-nav-item inline-block px-4 w-ful: News
- `<li>` 52997-tablet main-nav-item inline-block px-4 w-ful: Events and Important Dates
- `<li>` 53162-tablet main-nav-item inline-block px-4 w-ful: Student Services
- `<div>` cookie-notice cookie-notice--container rounded-md: Cookies Notice This site uses cookies to offer you a better browsing experience. Find out more on how we use cookies and how you can change your settings.

Link-dense blocks removed (1):

- `<li>` share=1.00 words=2: Visit Website

## CA | Lakehead University | integrity | 20260309055943

URL: https://www.lakeheadu.ca/students/student-life/student-conduct/academic-integrity  
raw words 630, clean words 266, content rule `//*[@role='main']`


Clean text (first 400 chars): Instructors can find the relevant forms and resources for the academic integrity investigation process under the Resources tab on menu on the lefthand side of this page or by contacting studentconduct@lakeheadu.ca Academic Integrity The Academic Integrity Code provides members of the University Community with general guidelines for appropriate academic behaviours and identifies prohibited Academic


Structural blocks removed (8):

- `<header>` : LakeheadU.ca Thunder Bay • Orillia • Barrie User Login Search form Search Students Faculty & Staff Alumni Donate Visit Apply Now Romeo Research Library mySucces
- `<ul>` navigation: Thunder Bay • Orillia • Barrie
- `<button>` : User Login
- `<form>` search: Search form Search
- `<label>` : Search
- `<nav>` : HomeStudentsStudent Life. . .Student ConductAcademic IntegritySet Campus
- `<header>` : Student Code of Conduct - Academic Integrity
- `<footer>` contentinfo: Academic Calendar myCourselink Library myEmail myInfo Directory A-Z Index Contact Us Careers Accessibility Privacy Lakehead University respectfully acknowledges

Id/class-marked blocks removed (13):

- `<div>` sidebar sidebar: Menu Contact Us Student Conduct Academic Integrity ChatGPT & Other AI Tools FAQ Academic Integrity Non-Academic Appeal Policy AIM Course Resources Code of the W
- `<div>` sidebar-toggle clearfix: Menu Contact Us
- `<div>` sidebar-toggle-first active: Menu
- `<div>` sidebar-toggle-second: Contact Us
- `<div>` sidebar-first column active: Student Conduct Academic Integrity ChatGPT & Other AI Tools FAQ Academic Integrity Non-Academic Appeal Policy AIM Course Resources Code of the Wolfpack News & E
- `<div>` region region-sidebar-first: Student Conduct Academic Integrity ChatGPT & Other AI Tools FAQ Academic Integrity Non-Academic Appeal Policy AIM Course Resources Code of the Wolfpack News & E
- `<div>` block-lu-blocks-lu-mm-sidebar block block-lu-block: Student Conduct Academic Integrity ChatGPT & Other AI Tools FAQ Academic Integrity Non-Academic Appeal Policy AIM Course Resources Code of the Wolfpack News & E
- `<ul>` menu: Student Conduct Academic Integrity ChatGPT & Other AI Tools FAQ Academic Integrity Non-Academic Appeal Policy AIM Course Resources Code of the Wolfpack News & E
- `<ul>` menu: Academic Integrity ChatGPT & Other AI Tools FAQ Academic Integrity Non-Academic Appeal Policy AIM Course Resources Code of the Wolfpack News & Events
- `<ul>` menu: ChatGPT & Other AI Tools FAQ Academic Integrity
- `<div>` sidebar-second column: Contact Us Thunder Bay Hours: Monday - Friday8:30 am - 4:30 pm Address: University Centre 1002, Lakehead University, 955 Oliver Road, Thunder Bay, ON, P7B 5E1 P
- `<div>` region region-sidebar-second: Contact Us Thunder Bay Hours: Monday - Friday8:30 am - 4:30 pm Address: University Centre 1002, Lakehead University, 955 Oliver Road, Thunder Bay, ON, P7B 5E1 P
- ... and 1 more

Link-dense blocks removed (1):

- `<p>` share=1.00 words=8: Academic Integrity Policy DownloadLearn about the Appeal process