from dataclasses import dataclass


@dataclass
class Member:
    user_id: int
    first_name: str
    last_name: str
    affiliation_id: int


class Members:
    JEFFREY = Member(
        user_id=10779625,
        first_name="Jeffrey",
        last_name="Collett (C)",
        affiliation_id=3948,
    )
    SONIA = Member(
        user_id=13704325,
        first_name="Sonia",
        last_name="Collett (C)",
        affiliation_id=3948,
    )
    JAMIE = Member(
        user_id=8561653,
        first_name="Jamie",
        last_name="Calhoun",
        affiliation_id=3948,
    )
    GENA = Member(
        user_id=9805876,
        first_name="Gena",
        last_name="Calhoun",
        affiliation_id=3948,
    )
    JOHN = Member(
        user_id=5835347,
        first_name="John",
        last_name="Manning",
        affiliation_id=87049,
    )
    LORI = Member(
        user_id=8261119,
        first_name="Lori",
        last_name="Kelly (C)",
        affiliation_id=3948,
    )
    SHAUNA = Member(
        user_id=8524202,
        first_name="Shauna",
        last_name="Scott",
        affiliation_id=87049,
    )
