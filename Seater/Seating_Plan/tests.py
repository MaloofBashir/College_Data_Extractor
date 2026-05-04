from django.test import SimpleTestCase

from .result_parser import parse_overall_result, parse_subject_grades, split_student_blocks


class ResultParserTests(SimpleTestCase):
    def test_split_student_blocks_handles_pdf_layout(self):
        page_text = """
        Roll No.Reg No. Name Subjects ResultGovt. Degree College
        25530344 559-zp-2022 FAAZIL MANZOOR HST522J1(58;20) HST522J2(36;42)
        HST522J3(55;42) URL522N(54;25) <br>HST522J1(B+) HST522J2(C+)
        HST522J3(B) URL522N(B+) <br>PASS/ SGPA--> 7.1
        25535774 453-ZP-2022 SAIQA MAJEED PLS522N(35;16) EDU522J1(27;18)
        EDU522J2(52;28) EDU522J3(23;27) <br>PLS522N(C+) EDU522J1(C)
        EDU522J2(C+) EDU522J3(F) <br>R EDU522J3
        """

        blocks = split_student_blocks(page_text)

        self.assertEqual(len(blocks), 2)

    def test_parse_subject_grades_reads_grade_section(self):
        block = (
            "25535774 453-ZP-2022 SAIQA MAJEED PLS522N(35;16) EDU522J1(27;18) "
            "EDU522J2(52;28) EDU522J3(23;27) <br>PLS522N(C+) EDU522J1(C) "
            "EDU522J2(C+) EDU522J3(F) <br>R EDU522J3"
        )

        parsed = parse_subject_grades(block)

        self.assertEqual(parsed["PLS522N"], "PASS")
        self.assertEqual(parsed["EDU522J3"], "FAIL")

    def test_parse_overall_result_uses_pass_sgpa_marker(self):
        block = "ABC <br>SUB1(B+) SUB2(C) <br>PASS/ SGPA--> 7.1"

        parsed = parse_overall_result(block)

        self.assertEqual(parsed, "PASS")

# Create your tests here.
