from typing import Optional
from datetime import date

from pydantic import Field, BaseModel, constr
from pydantic_extra_types.payment import PaymentCardNumber


class PaymentModel(BaseModel):
    card_holder: Optional[str] = constr(strip_whitespace=True, min_length=1)
    card_number: Optional[PaymentCardNumber]
    card_expire_date: Optional[date] = Field(..., gt=date.today())
