import unittest

from qrp_parser import QrpFormatError, parse_qrp


_TEXT_MARKER = b"\x00" * 12 + b"\xff" * 8


def _text_record(text: str) -> bytes:
    return _TEXT_MARKER + (84).to_bytes(4, "little") + text.encode("utf-16le") + b"\x00\x00"


class ParseQrpTests(unittest.TestCase):
    def _report(self) -> bytes:
        texts = [
            "Competência: 07/2026",
            "0,29",
            "311.575,52",
            "104.387,03",
            "415.962,55",
            "679",
            "681",
            "2428385 - HOSPITAL REGIONAL EMILIA CAMARA",
            "1,20",
            "941.649,62",
            "195.317,03",
            "1.136.966,65",
            "329",
            "333",
            "2639262 - HOSPITAL E MATERNIDADE SANTA MARIA",
        ]
        return b"".join(_text_record(text) for text in texts)

    def test_parses_competence_counts_and_service_totals(self) -> None:
        rows = parse_qrp(self._report())

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].cnes, "2428385")
        self.assertEqual(rows[0].unit_name, "HOSPITAL REGIONAL EMILIA CAMARA")
        self.assertEqual(rows[0].competence, "07/2026")
        self.assertEqual(rows[0].presented, 681)
        self.assertEqual(rows[0].approved, 679)
        self.assertEqual(str(rows[0].hospital_service), "311575.52")
        self.assertEqual(str(rows[0].professional_service), "104387.03")
        self.assertEqual(rows[1].presented, 333)
        self.assertEqual(rows[1].approved, 329)

    def test_rejects_file_without_report_text(self) -> None:
        with self.assertRaises(QrpFormatError):
            parse_qrp(b"not a QRP file")

    def test_parses_three_decimal_amounts_and_rendering_artifacts(self) -> None:
        texts = [
            "Competência: 07/2026",
            "3,77",
            "58.193,467",
            "38.740,54,",
            "96.934,007",
            "434\uffff",
            "4510",
            "7297394 - UPAE DR EMANUEL ALIRIO BRANDAO PETROLINA",
        ]
        rows = parse_qrp(b"".join(_text_record(text) for text in texts))

        self.assertEqual(rows[0].approved, 434)
        self.assertEqual(rows[0].presented, 4510)
        self.assertEqual(str(rows[0].hospital_service), "58193.467")
        self.assertEqual(str(rows[0].professional_service), "38740.54")


if __name__ == "__main__":
    unittest.main()
