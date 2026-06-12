# Vendor coding: all 30 questions (overview)

5 vendors x 6 dimensions. For each cell, read the evidence and pick ONE option.
This file is just to read through; fill the answers in the terminal with
`python3 fill_coding.py coder_a` (first coder) or `python3 fill_coding.py coder_b` (second coder).

---

### 1. Proctorio | noface_flag

**Q:** Does the documentation say a 'no face' / 'missing from frame' reading produces a recorded event?

**Evidence (from the vendor's docs):** "Face detection is used to detect the presence of one or more human faces or if the test-taker has left the exam for any reason." [proctorio_faq]

**Pick one:**
- `automatic_flag` -- the system records a flag/incident on its own
- `proctor_alert` -- it routes to a live human proctor in real time
- `not_documented` -- the pages do not say

### 2. Proctorio | id_gate

**Q:** When automated identity verification FAILS, what does the documentation say happens?

**Evidence (from the vendor's docs):** "If they have enabled Live Verify ID then a Proctorio live proctor will compare your image to the image on your ID card at the beginning of the exam in real time. Once your identity is validated you will be allowed to enter the exam." [proctorio_faq]

**Pick one:**
- `blocks_entry` -- the exam cannot start until verification passes
- `flag_proceed` -- the exam proceeds; the failure is recorded for later review
- `human_fallback` -- a human completes the verification
- `not_documented` -- the pages do not say

### 3. Proctorio | consequence_path

**Q:** Where does a face flag ultimately go?

**Evidence (from the vendor's docs):** "Proctorio's software does not perform any type of algorithmic decision making, such as determining if a breach of exam integrity has occurred. All decisions regarding exam integrity are left up to the exam administrator or institution." [proctorio_faq]

**Pick one:**
- `suspicion_score` -- flags add up into a score/priority shown to the instructor
- `vendor_review` -- vendor staff review the flag before reporting out
- `instructor_review` -- raw flags go to the instructor to interpret
- `not_documented` -- the pages do not say

### 4. Proctorio | human_review

**Q:** Does a human review the flag before it can affect the student?

**Evidence (from the vendor's docs):** "All decisions regarding exam integrity are left up to the exam administrator or institution." [proctorio_faq]

**Pick one:**
- `yes_documented` -- yes, the pages state a human reviews
- `not_documented` -- the pages do not say

### 5. Proctorio | lighting_burden

**Q:** Does student-facing text put the burden of good lighting on the STUDENT (well-lit room, no backlight)?

**Evidence (from the vendor's docs):** nan

**Pick one:**
- `yes` -- yes
- `no` -- no

### 6. Proctorio | bias_acknowledgment

**Q:** Does the public documentation acknowledge face detection can perform differently by skin tone or race?

**Evidence (from the vendor's docs):** "Unlike some competitors, Proctorio only uses face detection and gaze detection which cannot uniquely identify an individual's face." / "No. Proctorio does not use biometric analysis like facial recognition, keystroke fingerprinting, voice recognition, etc." [proctorio_faq]

**Pick one:**
- `acknowledged` -- it names a skin-tone or demographic performance gap
- `deflected` -- it re-describes the tech ('detection, not recognition') without addressing a gap
- `silent` -- no mention at all

### 7. Respondus | noface_flag

**Q:** Does the documentation say a 'no face' / 'missing from frame' reading produces a recorded event?

**Evidence (from the vendor's docs):** "During an online exam, Respondus Monitor will warn students when their face cannot be detected by the webcam." / "This reduces the likelihood of students being flagged" [respondus_enhancedflagging]

**Pick one:**
- `automatic_flag` -- the system records a flag/incident on its own
- `proctor_alert` -- it routes to a live human proctor in real time
- `not_documented` -- the pages do not say

### 8. Respondus | id_gate

**Q:** When automated identity verification FAILS, what does the documentation say happens?

**Evidence (from the vendor's docs):** nan

**Pick one:**
- `blocks_entry` -- the exam cannot start until verification passes
- `flag_proceed` -- the exam proceeds; the failure is recorded for later review
- `human_fallback` -- a human completes the verification
- `not_documented` -- the pages do not say

### 9. Respondus | consequence_path

**Q:** Where does a face flag ultimately go?

**Evidence (from the vendor's docs):** "Respondus Monitor is a fully automated proctoring solution. Students use a webcam to record themselves during an online exam. Afterward, flagged events and proctoring results are available to the instructor for further review." [respondus_monitor]

**Pick one:**
- `suspicion_score` -- flags add up into a score/priority shown to the instructor
- `vendor_review` -- vendor staff review the flag before reporting out
- `instructor_review` -- raw flags go to the instructor to interpret
- `not_documented` -- the pages do not say

### 10. Respondus | human_review

**Q:** Does a human review the flag before it can affect the student?

**Evidence (from the vendor's docs):** "flagged events and proctoring results are available to the instructor for further review" [respondus_monitor]

**Pick one:**
- `yes_documented` -- yes, the pages state a human reviews
- `not_documented` -- the pages do not say

### 11. Respondus | lighting_burden

**Q:** Does student-facing text put the burden of good lighting on the STUDENT (well-lit room, no backlight)?

**Evidence (from the vendor's docs):** "Respondus Monitor will now detect a very darkly lit environment (or a glaringly bright one) and prompt the student to make a correction. This reduces the chance of a student being flagged" [respondus_enhancedflagging]

**Pick one:**
- `yes` -- yes
- `no` -- no

### 12. Respondus | bias_acknowledgment

**Q:** Does the public documentation acknowledge face detection can perform differently by skin tone or race?

**Evidence (from the vendor's docs):** nan

**Pick one:**
- `acknowledged` -- it names a skin-tone or demographic performance gap
- `deflected` -- it re-describes the tech ('detection, not recognition') without addressing a gap
- `silent` -- no mention at all

### 13. Honorlock | noface_flag

**Q:** Does the documentation say a 'no face' / 'missing from frame' reading produces a recorded event?

**Evidence (from the vendor's docs):** "If no face is detected, or if multiple faces are detected, AI will flag the incident, and a human proctor may intervene." [honorlock_faq]

**Pick one:**
- `automatic_flag` -- the system records a flag/incident on its own
- `proctor_alert` -- it routes to a live human proctor in real time
- `not_documented` -- the pages do not say

### 14. Honorlock | id_gate

**Q:** When automated identity verification FAILS, what does the documentation say happens?

**Evidence (from the vendor's docs):** "In the case that your identity will be manually verified by a proctor, we will request a photo of you before an exam." [honorlock_idverification]

**Pick one:**
- `blocks_entry` -- the exam cannot start until verification passes
- `flag_proceed` -- the exam proceeds; the failure is recorded for later review
- `human_fallback` -- a human completes the verification
- `not_documented` -- the pages do not say

### 15. Honorlock | consequence_path

**Q:** Where does a face flag ultimately go?

**Evidence (from the vendor's docs):** "After our human proctors review the sessions, they will provide you with detailed reports that are easy to understand. These reports will highlight any incidents ... you can review the incidents yourself and decide if any further action is necessary." [honorlock_faq]

**Pick one:**
- `suspicion_score` -- flags add up into a score/priority shown to the instructor
- `vendor_review` -- vendor staff review the flag before reporting out
- `instructor_review` -- raw flags go to the instructor to interpret
- `not_documented` -- the pages do not say

### 16. Honorlock | human_review

**Q:** Does a human review the flag before it can affect the student?

**Evidence (from the vendor's docs):** "After our human proctors review the sessions, they will provide you with detailed reports" [honorlock_faq]

**Pick one:**
- `yes_documented` -- yes, the pages state a human reviews
- `not_documented` -- the pages do not say

### 17. Honorlock | lighting_burden

**Q:** Does student-facing text put the burden of good lighting on the STUDENT (well-lit room, no backlight)?

**Evidence (from the vendor's docs):** nan

**Pick one:**
- `yes` -- yes
- `no` -- no

### 18. Honorlock | bias_acknowledgment

**Q:** Does the public documentation acknowledge face detection can perform differently by skin tone or race?

**Evidence (from the vendor's docs):** "No. Honorlock uses facial detection, which only detects that there is a clear human face in the webcam. We do not identify the face, store any of the facial elements, or match the face to a database." [honorlock_faq]

**Pick one:**
- `acknowledged` -- it names a skin-tone or demographic performance gap
- `deflected` -- it re-describes the tech ('detection, not recognition') without addressing a gap
- `silent` -- no mention at all

### 19. ProctorU (Meazure Learning) | noface_flag

**Q:** Does the documentation say a 'no face' / 'missing from frame' reading produces a recorded event?

**Evidence (from the vendor's docs):** (archived pages document generic flagging only: "the platform detects and flags patterns of suspicious activity" [proctoru_recordplus]; no face-specific automatic event named)

**Pick one:**
- `automatic_flag` -- the system records a flag/incident on its own
- `proctor_alert` -- it routes to a live human proctor in real time
- `not_documented` -- the pages do not say

### 20. ProctorU (Meazure Learning) | id_gate

**Q:** When automated identity verification FAILS, what does the documentation say happens?

**Evidence (from the vendor's docs):** "Photos & Authentication: You'll take a photo of yourself as well as your I.D. for identity verification purposes." / "Your proctor will greet you and confirm that you passed your identity verification steps." [meazure_proctoringfaq]

**Pick one:**
- `blocks_entry` -- the exam cannot start until verification passes
- `flag_proceed` -- the exam proceeds; the failure is recorded for later review
- `human_fallback` -- a human completes the verification
- `not_documented` -- the pages do not say

### 21. ProctorU (Meazure Learning) | consequence_path

**Q:** Where does a face flag ultimately go?

**Evidence (from the vendor's docs):** "During a Record+ session, the platform detects and flags patterns of suspicious activity, but an incident report is not created unless a certified proctor reviews the situation and confirms that the activity is not allowed in your exam rules." [proctoru_recordplus]

**Pick one:**
- `suspicion_score` -- flags add up into a score/priority shown to the instructor
- `vendor_review` -- vendor staff review the flag before reporting out
- `instructor_review` -- raw flags go to the instructor to interpret
- `not_documented` -- the pages do not say

### 22. ProctorU (Meazure Learning) | human_review

**Q:** Does a human review the flag before it can affect the student?

**Evidence (from the vendor's docs):** "an incident report is not created unless a certified proctor reviews the situation and confirms" [proctoru_recordplus]

**Pick one:**
- `yes_documented` -- yes, the pages state a human reviews
- `not_documented` -- the pages do not say

### 23. ProctorU (Meazure Learning) | lighting_burden

**Q:** Does student-facing text put the burden of good lighting on the STUDENT (well-lit room, no backlight)?

**Evidence (from the vendor's docs):** nan

**Pick one:**
- `yes` -- yes
- `no` -- no

### 24. ProctorU (Meazure Learning) | bias_acknowledgment

**Q:** Does the public documentation acknowledge face detection can perform differently by skin tone or race?

**Evidence (from the vendor's docs):** nan

**Pick one:**
- `acknowledged` -- it names a skin-tone or demographic performance gap
- `deflected` -- it re-describes the tech ('detection, not recognition') without addressing a gap
- `silent` -- no mention at all

### 25. ExamSoft | noface_flag

**Q:** Does the documentation say a 'no face' / 'missing from frame' reading produces a recorded event?

**Evidence (from the vendor's docs):** "Applicant Missing: The exam-taker was not detected within the webcam frame. The exam-taker might be missing, or the exam-taker's face might be partly covered." [examsoft_reviewresults]

**Pick one:**
- `automatic_flag` -- the system records a flag/incident on its own
- `proctor_alert` -- it routes to a live human proctor in real time
- `not_documented` -- the pages do not say

### 26. ExamSoft | id_gate

**Q:** When automated identity verification FAILS, what does the documentation say happens?

**Evidence (from the vendor's docs):** "Pending Verification: Select this filter to show only exam-takers whose photo has not yet been validated. Exam-takers are allowed to start an exam after capturing their photo." [examsoft_reviewresults]

**Pick one:**
- `blocks_entry` -- the exam cannot start until verification passes
- `flag_proceed` -- the exam proceeds; the failure is recorded for later review
- `human_fallback` -- a human completes the verification
- `not_documented` -- the pages do not say

### 27. ExamSoft | consequence_path

**Q:** Where does a face flag ultimately go?

**Evidence (from the vendor's docs):** "After you post an assessment with ExamID or ExamMonitor enabled, you can monitor the overall results, review incidents, and submit dispositions." [examsoft_reviewresults]

**Pick one:**
- `suspicion_score` -- flags add up into a score/priority shown to the instructor
- `vendor_review` -- vendor staff review the flag before reporting out
- `instructor_review` -- raw flags go to the instructor to interpret
- `not_documented` -- the pages do not say

### 28. ExamSoft | human_review

**Q:** Does a human review the flag before it can affect the student?

**Evidence (from the vendor's docs):** "you can monitor the overall results, review incidents, and submit dispositions" [examsoft_reviewresults]

**Pick one:**
- `yes_documented` -- yes, the pages state a human reviews
- `not_documented` -- the pages do not say

### 29. ExamSoft | lighting_burden

**Q:** Does student-facing text put the burden of good lighting on the STUDENT (well-lit room, no backlight)?

**Evidence (from the vendor's docs):** "Ensure that you're in a well-lit area and that the light on your face is brighter than the light behind you. Tips: Turn on lights to illuminate your face." [examsoft_baselinephoto]

**Pick one:**
- `yes` -- yes
- `no` -- no

### 30. ExamSoft | bias_acknowledgment

**Q:** Does the public documentation acknowledge face detection can perform differently by skin tone or race?

**Evidence (from the vendor's docs):** nan

**Pick one:**
- `acknowledged` -- it names a skin-tone or demographic performance gap
- `deflected` -- it re-describes the tech ('detection, not recognition') without addressing a gap
- `silent` -- no mention at all
