"""
services/docgen_services.py
Lightweight document generator built around string templates.
"""

from __future__ import annotations

from datetime import date
from textwrap import dedent
from typing import Dict


def _today() -> str:
    return date.today().strftime("%d %B %Y")


TEMPLATES = {
    "nda": dedent(
        """
        NON-DISCLOSURE AGREEMENT

        This Agreement is made on {effective_date} between {disclosing_party} ("Disclosing Party")
        and {receiving_party} ("Receiving Party").

        1. Purpose: {purpose}
        2. Confidential Information: Includes any information disclosed in oral, written, or electronic form.
        3. Obligations: The Receiving Party shall maintain strict confidentiality and restrict access on a need-to-know basis.
        4. Term: {term}
        5. Governing Law: {governing_law}

        Signed:
        Disclosing Party: ______________________
        Receiving Party: ______________________
        """
    ).strip(),
    "employment_offer": dedent(
        """
        EMPLOYMENT OFFER LETTER

        Date: {effective_date}
        Candidate: {candidate_name}

        Dear {candidate_name},

        We are pleased to offer you the position of {role_title} at {company_name} located at {office_location}.
        Start Date: {start_date}
        Compensation: {compensation}
        Reporting To: {reporting_manager}

        Please confirm your acceptance by {acceptance_deadline}.

        Regards,
        {company_representative}
        """
    ).strip(),
    "legal_notice": dedent(
        """
        LEGAL NOTICE

        Date: {effective_date}
        To: {recipient_name}
        Address: {recipient_address}

        Subject: {subject}

        {body}

        Kindly treat this as a formal notice. We expect your response within {response_timeline}.

        Sincerely,
        {issued_by}
        """
    ).strip(),
}


def generate_document(template: str, fields: Dict[str, str]) -> Dict[str, str]:
    key = template.lower()
    if key not in TEMPLATES:
        raise ValueError(f"Unknown template '{template}'. Available: {', '.join(TEMPLATES)}")

    data = {"effective_date": _today(), **fields}
    content = TEMPLATES[key].format(**data)
    return {"template": key, "content": content}

