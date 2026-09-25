import unittest
from datetime import date

from fq_observatorio.panorama_pdf import build_panorama_pdf
from fq_observatorio.publication_calendar import calendar_to_ics


class DownloadAccessibilityTests(unittest.TestCase):
    def test_ics_uses_crlf_and_folds_every_physical_line_to_75_octets(self):
        events = [
            {
                "slug": "inflation",
                "name": "Inflación interanual con descripción extensa",
                "date": date(2026, 10, 7),
                "source": "INEC/BCCR",
                "confirmation": "Programada oficialmente",
                "note": (
                    "Fecha tomada de un calendario oficial; puede modificarse "
                    "si la institución lo comunica, incluso después de publicada."
                ),
            }
        ]

        content = calendar_to_ics(events, date(2026, 9, 24))

        self.assertNotIn("\n", content.replace("\r\n", ""))
        physical_lines = content.rstrip("\r\n").split("\r\n")
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in physical_lines))
        self.assertTrue(any(line.startswith(" ") for line in physical_lines))

        unfolded = ""
        for line in physical_lines:
            if line.startswith(" "):
                unfolded += line[1:]
            else:
                unfolded += "\n" + line
        self.assertIn("SUMMARY:Revisar Inflación interanual", unfolded)
        self.assertIn("oficial\\; puede modificarse", unfolded)
        self.assertIn("comunica\\, incluso", unfolded)

    def test_pdf_embeds_unicode_font_maps_for_accented_text(self):
        pdf = build_panorama_pdf(
            [
                {
                    "group": "Coyuntura económica",
                    "name": "Inflación interanual",
                    "value": "-0.28",
                    "unit": "% interanual",
                    "period": "31/07/2026",
                    "source": "INEC/BCCR",
                    "status": "Al día",
                }
            ],
            date(2026, 9, 24),
            ["Inflación interanual"],
        )

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertIn(b"/ToUnicode", pdf)
        self.assertIn(b"BitstreamVeraSans", pdf)


if __name__ == "__main__":
    unittest.main()
