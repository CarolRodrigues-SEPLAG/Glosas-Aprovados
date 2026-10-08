"""Parser for SIHD2 QuickReport (.QRP) files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal


_TEXT_MARKER = b"\x00" * 12 + b"\xff" * 8
_COMPETENCE_RE = re.compile(r"Competência:\s*(\d{2}/\d{4})", re.IGNORECASE)
_CNES_RE = re.compile(r"^(?P<cnes>\d{7})\s*-\s*(?P<name>.+?)\s*$")
_MONEY_RE = re.compile(
    r"^(?P<whole>(?:\d{1,3}(?:\.\d{3})+|\d+)),(?P<fraction>\d{2,3}),?$"
)
_COUNT_RE = re.compile(r"^(?P<count>\d+)(?:[^\d.,]+)?$")


class QrpFormatError(ValueError):
    """Raised when a QRP file does not contain a readable SIHD2 report."""


@dataclass(frozen=True)
class ReportRow:
    cnes: str
    unit_name: str
    competence: str
    presented: int
    approved: int
    hospital_service: Decimal
    professional_service: Decimal


def _extract_text_records(data: bytes) -> list[str]:
    records: list[str] = []
    cursor = 0

    while True:
        marker_offset = data.find(_TEXT_MARKER, cursor)
        if marker_offset < 0:
            break

        text_start = marker_offset + len(_TEXT_MARKER) + 4
        if text_start >= len(data):
            break

        text_end = text_start
        while text_end + 1 < len(data):
            if data[text_end] == 0 and data[text_end + 1] == 0:
                break
            text_end += 2

        if text_end + 1 >= len(data):
            break

        text = data[text_start:text_end].decode("utf-16le", errors="replace")
        text = re.sub(r"[\x00-\x1f\x7f]+", " ", text).strip()
        if text:
            records.append(text)

        cursor = text_end + 2

    return records


def _numeric_value(text: str) -> Decimal | int | None:
    money_match = _MONEY_RE.fullmatch(text)
    if money_match is not None:
        whole = money_match.group("whole").replace(".", "")
        return Decimal(f"{whole}.{money_match.group('fraction')}")

    count_match = _COUNT_RE.fullmatch(text)
    if count_match is not None:
        return int(count_match.group("count"))
    return None


def parse_qrp(data: bytes) -> list[ReportRow]:
    """Parse unit totals and competence from an SIHD2 .QRP report."""
    if not data:
        raise QrpFormatError("O arquivo enviado está vazio.")

    records = _extract_text_records(data)
    if not records:
        raise QrpFormatError(
            "Não foi possível ler os registros de texto do arquivo. "
            "Confirme se o arquivo enviado é um relatório .QRP do SIHD2."
        )

    competence = next(
        (
            match.group(1)
            for record in records
            if (match := _COMPETENCE_RE.search(record)) is not None
        ),
        None,
    )
    if competence is None:
        raise QrpFormatError(
            "A competência não foi encontrada. O arquivo pode não ser um "
            "relatório de valores aprovados por CNES do SIHD2."
        )

    rows: list[ReportRow] = []
    seen_cnes: set[str] = set()
    found_units = False

    for index, record in enumerate(records):
        match = _CNES_RE.fullmatch(record)
        if match is None:
            continue

        found_units = True
        cnes = match.group("cnes")
        name = re.sub(
            r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ .,'&()/+-]",
            "",
            match.group("name"),
        )
        name = re.sub(r"\s+", " ", name).strip()
        prior_numeric_values = [
            value
            for prior_record in records[max(0, index - 50) : index]
            if (value := _numeric_value(prior_record)) is not None
        ]
        fields = prior_numeric_values[-5:]

        if (
            len(fields) != 5
            or not all(isinstance(value, Decimal) for value in fields[:3])
            or not all(isinstance(value, int) for value in fields[3:])
        ):
            continue

        if cnes in seen_cnes:
            raise QrpFormatError(
                f"O CNES {cnes} aparece mais de uma vez no relatório. "
                "Verifique o arquivo antes de exportar."
            )

        hospital_service, professional_service, _total, approved, presented = fields
        rows.append(
            ReportRow(
                cnes=cnes,
                unit_name=name,
                competence=competence,
                presented=presented,
                approved=approved,
                hospital_service=hospital_service,
                professional_service=professional_service,
            )
        )
        seen_cnes.add(cnes)

    if not rows:
        if found_units:
            raise QrpFormatError(
                "Foram encontrados nomes de unidades, mas os campos de "
                "apresentado, aprovado e valores dos serviços não puderam "
                "ser associados. Confirme se o relatório está completo."
            )
        raise QrpFormatError("Nenhuma unidade de saúde com CNES foi encontrada.")

    return rows
