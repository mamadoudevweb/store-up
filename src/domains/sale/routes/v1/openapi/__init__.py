from .sale_openapi import register as register_sale
from .refund_openapi import register as register_refund

def register() -> None:
    register_sale()
    register_refund()
