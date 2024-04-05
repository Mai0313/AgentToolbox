from typing import Optional
from datetime import date

from pydantic import Field, BaseModel, constr
from pydantic_extra_types.payment import PaymentCardNumber


class PaymentModel(BaseModel):
    card_holder: Optional[str] = Field(default=None)
    card_number: Optional[PaymentCardNumber] = Field(default=None)
    card_expire_date: Optional[date] = Field(default=None, gt=date.today())
