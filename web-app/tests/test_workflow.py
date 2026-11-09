import io
import re
import tempfile
import unittest
from unittest.mock import patch

from pptx import Presentation
from pptx.util import Inches
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from app import create_app, quiz_questions
from study_tools import build_messages

BASE = "http://127.0.0.1"


def sample_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(width=320, height=240)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                             NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 80 Td (Synthetic PDF notes) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    data = io.BytesIO()
    writer.write(data)
    data.seek(0)
    return data


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with patch.dict("os.environ", {"STUDYCAP_MODEL": "", "STUDYCAP_MODEL_PORT": ""}):
            self.app = create_app(directory.name)
        self.client = self.app.test_client()
        self.token = self.token_for(self.client)

    def token_for(self, client):
        html = client.get("/import", base_url=BASE).get_data(as_text=True)
        return re.search(r'name="csrf" value="(\w+)"', html).group(1)

    def post(self, route, **fields):
        return self.client.post(route, base_url=BASE, data={"csrf": self.token, **fields})

    def test_capture_edit_study_and_access(self):
        result = self.post("/import", title="Practice", captions="Proportional gain changes control action.")
        self.assertEqual(result.status_code, 303)
        route = result.location
        self.assertIn("Proportional gain", self.client.get(route, base_url=BASE).get_data(as_text=True))
        other = self.app.test_client()
        other_token = self.token_for(other)
        self.assertEqual(other.get(route, base_url=BASE).status_code, 404)
        self.assertEqual(other.post(route + "/remove", base_url=BASE, data={"csrf": other_token}).status_code, 404)
        self.assertEqual(self.client.post(route + "/remove", base_url=BASE).status_code, 403)
        self.assertIn("Reveal answer", self.post(route + "/study", action="quiz").get_data(as_text=True))
        self.assertIn("Response", self.post(route + "/study", action="chat", question="gain").get_data(as_text=True))
        self.assertEqual(self.post(route + "/edit", title="Revised", summary="Edited notes", notes="<markup>").status_code, 303)
        html = self.client.get(route, base_url=BASE).get_data(as_text=True)
        self.assertIn("&lt;markup&gt;", html)
        self.assertEqual(self.post(route + "/remove").status_code, 303)
        self.assertEqual(self.client.get(route, base_url=BASE).status_code, 404)

    def test_synthetic_documents(self):
        slides = Presentation()
        slide = slides.slides.add_slide(slides.slide_layouts[6])
        slide.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = "Synthetic slide notes"
        stream = io.BytesIO()
        slides.save(stream)
        stream.seek(0)
        for suffix, data, expected in (("pdf", sample_pdf(), "Synthetic PDF notes"), ("pptx", stream, "Synthetic slide notes")):
            with self.subTest(suffix=suffix):
                saved = self.post("/import", title="Slides", slides=(data, "practice." + suffix))
                self.assertEqual(saved.status_code, 303)
                self.assertIn(expected, self.client.get(saved.location, base_url=BASE).get_data(as_text=True))

    def test_input_boundaries(self):
        self.assertEqual(self.post("/import", title="Empty").status_code, 400)
        self.assertEqual(self.post("/import", title="Long", captions="x" * 60001).status_code, 400)
        self.assertEqual(self.post("/import", title="Legacy", slides=(io.BytesIO(b""), "example.ppt")).status_code, 400)
        self.assertEqual(self.client.get("/", base_url="http://example.invalid").status_code, 400)

    def test_prompt_modes_and_quiz_contract(self):
        for data in ({"captions": "synthetic text"}, {"pdfText": "synthetic text"},
                     {"captions": "synthetic text", "pdfText": "slide text"}):
            self.assertIn("synthetic text", build_messages("summary", data)[-1]["content"])
        for kind in ("chat", "quiz"):
            self.assertTrue(build_messages(kind, {"summaryText": "practice", "userQuestion": "why?"}))
        with self.assertRaises(ValueError):
            quiz_questions('{"questions": []}')


if __name__ == "__main__":
    unittest.main()
